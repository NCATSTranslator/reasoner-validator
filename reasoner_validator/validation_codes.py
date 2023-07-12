import copy
from os.path import join, abspath, dirname
from typing import Optional, Any, Dict, List, Tuple, Union, NamedTuple

from yaml import load, BaseLoader
import logging

from reasoner_validator.message import SCOPED_MESSAGES, IDENTIFIED_MESSAGES

logger = logging.getLogger(__name__)

DEFAULT_CODES_DOCUMENTATION_FILE = abspath(join(dirname(__file__), "..", "docs", "validation_codes_dictionary.md"))


class CodeDictionary:

    CODE_DICTIONARY_FILE: str = abspath(join(dirname(__file__), "codes.yaml"))

    MESSAGE = "$message"
    CONTEXT = "$context"
    DESCRIPTION = "$description"

    code_dictionary: Optional[Dict] = None

    @classmethod
    def _get_code_dictionary(cls) -> Dict:
        if not cls.code_dictionary:
            # Open the file and load the file
            with open(cls.CODE_DICTIONARY_FILE, mode='r') as f:
                cls.code_dictionary = load(f, Loader=BaseLoader)
        return cls.code_dictionary

    @classmethod
    def filter_copy_by_facet(cls, tree: Dict, facet: str) -> Dict:
        """
        Copy subtree, filtering out leaf data by specified facet. Leaves are simply identified by
        the presence of the mandatory '$message' tree parameter dictionary key.

        :param tree: Dict, message code dictionary tree to be copied, possibly filtered by facet
        :param facet: str, constraint on code entry facet to be returned; if specified, should be either
                        "message", "context" or "description" (default: return all facets of the code entry)

        :return: Dict, tree filtered by facet
        """
        if facet:
            if cls.MESSAGE in tree:
                # Terminate recursion; Copy this leaf in the subtree, filtering on the specified 'facet'
                return {key: value for key, value in tree.items() if key == f"${facet.lower()}"}
            else:
                # Recurse filter/copy the tree's children?
                tree_copy: Dict = dict()
                for key, subtree in tree.items():
                    if isinstance(subtree, Dict):
                        tree_copy[key] = cls.filter_copy_by_facet(subtree, facet)
                    else:
                        # Note: this error may occur if the codes.yaml leaf entry is missing its MESSAGE?
                        logger.warning(f"filter_copy_by_facet(): subtree '{str(subtree)}' is not a dictionary?")

                return tree_copy
        else:
            # Shortcut: simply deepcopy the subtree, if facet is not being filtered
            return copy.deepcopy(tree)

    @classmethod
    def _get_nested_code_entry(
            cls,
            data: Dict[str, Dict],
            path: List[str],
            pos: int,
            facet: Optional[str],
            is_leaf: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Navigate dot delimited tag 'path' into a multi-level dictionary, to return its associated value.

        :param data: Dict, multi-level data dictionary being traversed
        :param path: str, dotted JSON tag path
        :param pos: int, zero-based current position in tag path
        :param facet: Optional[str], constraint on code entry facet to be returned; if specified, should be either
                                     "message" or "description" (default: return all facets of the code entry)
        :param is_leaf: bool, only return entry if it is a 'leaf' of the code tree
        :return: Dict, value of the multi-level tag, if available; 'None' otherwise if no tag value found in the path
        """
        tag = path[pos]
        if tag not in data:
            return None

        subtree: Dict = data[tag]

        pos += 1
        if pos == len(path):

            if not subtree:
                # sanity check...
                return None

            # If the is_leaf flag is True, then the expected code value *must* be a
            # code subtree leaf which, at a minimum, must contain a MESSAGE template.
            # Conversely, a MESSAGE template should not be there if a code subtree is expected?
            if cls.MESSAGE in subtree and not is_leaf or cls.MESSAGE not in subtree and is_leaf:
                return None

            return cls.filter_copy_by_facet(subtree, facet)

        else:
            return cls._get_nested_code_entry(subtree, path, pos, facet, is_leaf)

    @staticmethod
    def get_message_type(code: str) -> str:
        assert code, "Empty code!"
        code_path = code.split(".")
        return code_path[0]

    @classmethod
    def get_code_subtree(
            cls,
            code: str,
            facet: Optional[str] = None,
            is_leaf: Optional[bool] = False
    ) -> Optional[Tuple[str, Dict]]:
        """
        Get subtree of specified dot-delimited tag name, returning message type (i.e. info, warning, error, critical).
        If optional 'is_leaf' flag is set to True, then only return the code if it is a terminal leaf in the code tree.

        :param code: Optional[str], dot delimited validation message code identifier (None is ok, but returns None)
        :param facet: Optional[str], constraint on code entry facet to be returned; if specified, should be either
                                     "message" or "description" (default: return all facets of the code entry)
        :param is_leaf: Optional[bool], only return entry if it is a 'leaf' of the code tree (default: False)

        :return: Optional[Tuple[str, Dict[str,str]]], 2-tuple of the code type (i.e. info, warning, error, critical)
                 and the validation message entry (dictionary); None if empty code or code unknown in the
                 code dictionary, or (if the is_leaf option is 'True') if the code doesn't resolve to a single leaf.
        """
        if not code:
            return None

        codes: Dict = cls._get_code_dictionary()
        code_path = code.split(".")
        value: Optional[Dict[str, str]] = cls._get_nested_code_entry(codes, code_path, 0, facet, is_leaf)
        if value is not None:
            return cls.get_message_type(code), value
        else:
            return None

    @classmethod
    def get_code_entry(cls, code: Optional[str], facet: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Get the single code entry corresponding to the given code, if available.

        :param code: Optional[str], dot delimited validation message code identifier (None is ok, but returns None)
        :param facet: Optional[str], constraint on code entry facet to be returned; if specified, should be either
                                     "message" or "description" (default: return all facets of the code entry)

        :return: Dict, single terminal leaf code entry (complete with indicated or all facets); None, if not available
        """
        value: Optional[Tuple[str, Dict[str, str]]] = cls.get_code_subtree(code, facet=facet, is_leaf=True)
        if not value:
            return None
        entry: Optional[Dict[str, str]]
        message_type, entry = value
        return entry

    @classmethod
    def get_message_template(cls, code: Optional[str]) -> Optional[str]:
        entry: Optional[Dict[str, str]] = cls.get_code_entry(code)
        return entry[cls.MESSAGE] if entry else None

    @classmethod
    def get_message_context(cls, code: Optional[str]) -> Optional[List[str]]:
        entry: Optional[Dict[str, str]] = cls.get_code_entry(code)
        return entry[cls.CONTEXT] if entry else None

    @classmethod
    def get_description(cls, code: Optional[str]) -> Optional[str]:
        entry: Optional[Dict[str, str]] = cls.get_code_entry(code)
        return entry[cls.DESCRIPTION] if entry else None

    @staticmethod
    def validation_code_tag(code: str) -> str:
        assert code, "Empty code!"
        path: List[str] = [part for part in code.replace("_", ".").split(".")]
        code_parts: List[str] = [part.capitalize() for part in path[1:-1]]
        tag: str = ' '.join(code_parts) if code_parts else path[-1].capitalize()
        return tag

    @classmethod
    def display(
            cls,
            code: str,  # code for specific validation message template
            messages: Optional[SCOPED_MESSAGES] = None,
            add_prefix: bool = False
    ) -> Dict[str, List[str]]:
        """
        Generate one or more full messages from provided Validation Reporter code
        and associated parameters (if applicable).

        :param code: str, valid (dot delimited YAML key path) identified code,
                          which should be registered in the project codes.yaml file.
        :param messages: Optional[SCOPED_MESSAGES], collection of scoped validation messages (Default: None)
                         If this parameter specified as None, then it is actually taken to be {"global": None}
        :param add_prefix: bool, flag to prepend a prefix for the message type
                           (i.e. critical, error, warning, info) to displayed messages (default: False)

        :return: Dict[str, List[str]], scope-indexed dictionary of lists of decoded messages for a given code
        """
        # All validation messages have a context, even if just "global" with no other distinguishing parameters.
        if messages is None:
            messages = {"global": None}

        value: Optional[Tuple[str, Dict[str, str]]] = cls.get_code_subtree(code, is_leaf=True)
        assert value, f"CodeDictionary.display(): unknown message code {code}"

        message_type = cls.get_message_type(code)
        message_type_prefix: str = f"{message_type.upper()} - " if add_prefix else ""
        context: str = cls.validation_code_tag(code) + ": " if add_prefix else ""

        template: str = cls.get_message_template(code)
        message_set: Dict = dict()

        # 'messages' is an instance of 'SCOPED_MESSAGES' that is a Dict[<scope>, Optional[IDENTIFIED_MESSAGES]]
        # where <scope> is either "global" or a "sources trail" string designating the audit trail from the
        # 'primary_knowledge_source' up to topmost 'aggregator_knowledge_source' which reported the validation message,
        # and the (Optional) 'IDENTIFIED_MESSAGES' are validation contexts possibly discriminated by a specific
        # target entity (identifier) of the validation, plus any (Optional) additional parameters.
        scope: str
        parameters: Optional[IDENTIFIED_MESSAGES]
        for scope, parameters in messages.items():
            message_set[scope] = list()
            if parameters:
                # A non-null IDENTIFIED_MESSAGES entry is a dictionary of additional validation message parameters
                # indexed by an identifier discriminating the (Biolink or TRAPI) target of the validation.
                # A given validation code may or may not have additional parameters (as documented in the codes.yaml).
                # If such parameters are expected, then they will be documented in a List[MESSAGE_PARAMETERS].
                for identifier in parameters.keys():
                    other_parameters: Optional[IDENTIFIED_MESSAGES] = parameters[identifier]
                    identifier_dict: Dict = {'identifier': identifier}
                    if other_parameters:
                        # is a list of one or more dictionaries of additional parameters
                        for another_parameter_dict in other_parameters:
                            # make copies, to be safe...
                            content: Dict = identifier_dict.copy()
                            content.update(another_parameter_dict)
                            message_set[scope].append(
                                f"{message_type_prefix}{context}{template.format(**content)}"
                            )
                    else:
                        message_set[scope].append(
                            f"{message_type_prefix}{context}{template.format(**identifier_dict)}"
                        )

            else:
                # simple scalar message without identification and parameterization?
                message_set[scope].append(f"{message_type_prefix}{context}{template}")

        return message_set

    @classmethod
    def _dump_code_markdown_entries(cls, root: str, code_subtree: Dict, markdown_file):
        for tag, value in code_subtree.items():
            if cls.MESSAGE not in value:
                # Recurse down to leaf of tree
                cls._dump_code_markdown_entries(f"{root}.{tag}", value, markdown_file)
            else:
                print(f"### {root}.{tag}\n", file=markdown_file)
                message: str = value[cls.MESSAGE]
                context: str = value[cls.CONTEXT] if cls.CONTEXT in value else None
                description: str = value[cls.DESCRIPTION] if cls.DESCRIPTION in value else None
                print(f"**Message:** {message}\n", file=markdown_file)
                if context:
                    print(f"**Context:** {', '.join(context)}\n", file=markdown_file)
                if description:
                    print(f"**Description:** {description}\n", file=markdown_file)

    @classmethod
    def markdown(cls, filename: str = DEFAULT_CODES_DOCUMENTATION_FILE) -> bool:
        """Dump the Code Dictionary into a validation_codes_dictionary.md Markdown file, for documentation purposes.

        :param filename: str, defaults to DEFAULT_CODES_DOCUMENTATION_FILE
        :return: bool, True if successful; False otherwise
        """
        code_dictionary: Dict = cls._get_code_dictionary()

        try:
            with open(filename, mode='w') as markdown_file:
                print("# Validation Codes Dictionary\n", file=markdown_file)
                top_level_tag: str

                for top_level_tag in code_dictionary.keys():

                    if top_level_tag == "info":
                        top_level_name = "Information"
                    elif top_level_tag == "critical":
                        top_level_name = "Critical Error"
                    else:
                        top_level_name = top_level_tag.capitalize()

                    print(f"## {top_level_name}\n", file=markdown_file)
                    cls._dump_code_markdown_entries(
                        top_level_tag,
                        code_dictionary[top_level_tag],
                        markdown_file=markdown_file
                    )

        except IOError:
            return False

        return True


if __name__ == '__main__':
    CodeDictionary.markdown()
