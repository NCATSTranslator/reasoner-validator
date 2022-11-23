from os.path import join, abspath, dirname
from typing import Optional, Dict, List, Tuple

from yaml import load, BaseLoader

DEFAULT_CODES_DOCUMENTATION_FILE = abspath(join(dirname(__file__), "..", "docs", "validation_codes_dictionary.md"))


class CodeDictionary:

    CODE_DICTIONARY: str = abspath(join(dirname(__file__), "codes.yaml"))

    code_dictionary: Optional[Dict] = None

    @classmethod
    def _get_code_dictionary(cls) -> Dict:
        if not cls.code_dictionary:
            # Open the file and load the file
            with open(cls.CODE_DICTIONARY, mode='r') as f:
                cls.code_dictionary = load(f, Loader=BaseLoader)
        return cls.code_dictionary

    @classmethod
    def _get_nested_code_value(cls, data: Dict, path: List[str], pos: int) -> Optional[str]:
        """
        Navigate dot delimited tag 'path' into a multi-level dictionary, to return its associated value.

        :param data: Dict, multi-level data dictionary
        :param path: str, dotted JSON tag path
        :param pos: int, zero-based current position in tag path
        :return: string value of the multi-level tag, if available; 'None' otherwise if no tag value found in the path
        """
        tag = path[pos]
        if tag not in data:
            return None

        pos += 1
        if pos == len(path):
            return data[tag]
        else:
            return cls._get_nested_code_value(data[tag], path, pos)

    @classmethod
    def _code_value(cls, code) -> Optional[Tuple[str, str]]:
        """
        Get value of specified dot delimited tag name.

        :param code:
        :return: Optional[Tuple[str, str]], 2-tuple of the code type (i.e. info, warning, error) and the
                 validation message template; None if empty code or code unknown in the code dictionary
        """
        if not code:
            return None

        codes: Dict = cls._get_code_dictionary()
        code_path = code.split(".")
        value = cls._get_nested_code_value(codes, code_path, 0)
        if value is not None:
            return code_path[0], value
        else:
            return None

    @staticmethod
    def display(**message):
        assert message and 'code' in message  # should be non-empty, containing a code
        code: str = message.pop('code')
        value: Optional[Tuple[str, str]] = CodeDictionary._code_value(code)
        assert value, f"CodeDictionary.display(): unknown message code {code}"
        message_type, template = value
        code_parts: List[str] = [part.capitalize() for part in code.replace("_", ".").split(".")[1:-1]]
        context: str = ' '.join(code_parts) + ': ' if code_parts else ''
        if message:
            # Message template parameterized with additional named parameter
            # message context, assumed to be referenced by the template
            return f"{message_type.upper()} - {context}{template.format(**message)}"
        else:
            # simple scalar message without parameterization?
            return f"{message_type.upper()} - {context}{template}"

    @classmethod
    def _dump_code_markdown_entries(cls, root: str, code_subtree: Dict, markdown_file):
        for tag, value in code_subtree.items():
            if isinstance(value, Dict):
                # Recurse down to leaf of tree
                cls._dump_code_markdown_entries(f"{root}.{tag}", value, markdown_file)
            elif isinstance(value, str):
                print(f"### {root}.{tag}\n\n{value}\n", file=markdown_file)
            #
            # Future design of the codes dictionary *might* provide
            # for additional descriptive contents in a list of strings
            #
            # elif isinstance(value, List):
            #     print(f"### {root}.{tag}\n\n{value}\n", file=markdown_file)
            #     for item in value:
            #         print(f"- {item}", file=markdown_file)
            else:
                raise RuntimeError("Unknown code data type?")

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
                    top_level_name = "Information" if top_level_tag == "info" else top_level_tag.capitalize()
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
