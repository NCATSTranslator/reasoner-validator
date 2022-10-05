"""Error and Warning Reporting Module"""
from os.path import join, abspath, dirname
import copy
from typing import Optional, Dict, List, Tuple
from json import dumps, JSONEncoder
from yaml import load, BaseLoader

from reasoner_validator.versioning import latest


class CodeDictionary:

    CODE_DICTIONARY: str = join(abspath(dirname(__file__)), "codes.yaml")

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
        Get value of specified dot delimited tag name
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
        if message:
            # Message template parameterized with additional named parameter
            # message context, assumed to be referenced by the template
            return f"{message_type.upper()} - {template.format(**message)}"
        else:
            # simple scalar message without parameterization?
            return f"{message_type.upper()} - {template}"


class ReportJsonEncoder(JSONEncoder):
    def default(self, o):
        try:
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)
        # Let the base class default method raise the TypeError
        return JSONEncoder.default(self, o)


def _output(json, flat=False):
    return dumps(json, cls=ReportJsonEncoder, sort_keys=False, indent=None if flat else 4)


class ValidationReporter:
    """
    General wrapper for managing validation status messages: information, warnings and errors.
    The TRAPI version and Biolink Model versions are also tracked for convenience at
    this abstract level although their application is within specific pertinent subclasses.
    """

    # Default major version resolves to latest TRAPI OpenAPI release,
    # specifically 1.3.0, as of September 1st, 2022
    DEFAULT_TRAPI_VERSION = "1"

    _message_type_name: Dict[str, str] = {
        "info": "information",
        "warning": "warnings",
        "error": "errors"
    }

    def __init__(
            self,
            prefix: Optional[str] = None,
            trapi_version: Optional[str] = None,
            biolink_version: Optional[str] = None,
            sources: Optional[Dict] = None,
            strict_validation: bool = False
    ):
        """
        :param prefix: named context of the Validator, used as a prefix in validation messages.
        :type prefix: str
        :param trapi_version: version of component against which to validate the message (mandatory, no default assumed).
        :type trapi_version: str
        :param biolink_version: Biolink Model (SemVer) release against which the knowledge graph is to be
                                validated (Default: if None, use the Biolink Model Toolkit default version.
        :type biolink_version: Optional[str] = None
        :param sources: Dictionary of validation context identifying the ARA and KP for provenance attribute validation
        :type sources: Dict
        :param strict_validation: if True, abstract and mixin elements validate as 'error'; None or False, issue a 'warning'
        :type strict_validation: Optional[bool] = None
        """
        self.prefix: str = prefix + ": " if prefix else ""
        self.trapi_version = trapi_version if trapi_version else latest.get(self.DEFAULT_TRAPI_VERSION)
        self.biolink_version = biolink_version
        self.sources: Optional[Dict] = sources
        self.strict_validation: Optional[bool] = strict_validation
        self.messages: Dict[str, List] = {
            "information": list(),
            "warnings": list(),
            "errors": list()
        }

    def get_trapi_version(self) -> str:
        """
        :return: str, TRAPI (SemVer) version
        """
        return self.trapi_version

    def get_biolink_version(self) -> str:
        """
        :return: Biolink Model version currently targeted by the validator.
        :rtype biolink_version: str
        """
        return self.biolink_version

    def is_strict_validation(self) -> bool:
        return self.strict_validation

    def has_messages(self) -> bool:
        return self.has_information() or self.has_warnings() or self.has_errors()

    def has_information(self) -> bool:
        return bool(self.messages["information"])

    def has_warnings(self) -> bool:
        return bool(self.messages["warnings"])

    def has_errors(self) -> bool:
        return bool(self.messages["errors"])

    @staticmethod
    def get_message_type(code: str) -> str:
        code_id_parts: List[str] = code.split('.')
        message_type: str = code_id_parts[0]
        if message_type in ['info', 'warning', 'error']:
            return message_type
        else:
            raise NotImplementedError(
                f"ValidationReport.get_message_type(): {code} is unknown code type: {message_type}"
            )

    def report(self, code: str, **message):
        message_type = self.get_message_type(code)
        message_set = self._message_type_name[message_type]
        message['code'] = code  # add the code into the message
        self.messages[message_set].append(message)

    def add_messages(self, new_messages: Dict[str, List]):
        """
        Batch addition of a dictionary of messages to a ValidatorReporter instance.

        :param new_messages: Dict[str, List], with key one of
                             "information", "warnings" or "errors",
                              with Lists of (structured) messages.
        """
        for key in self.messages:
            if key in new_messages:
                self.messages[key].extend(new_messages[key])

    def get_messages(self) -> Dict[str, List[Dict]]:
        return copy.deepcopy(self.messages)

    ############################
    # General Instance methods #
    ############################
    def merge(self, reporter):
        """
        Merge all messages and metadata from a second ValidatorReporter,
        into the calling ValidatorReporter instance.

        :param reporter: second ValidatorReporter
        """
        assert isinstance(reporter, ValidationReporter)

        # new coded messages also need to be merged!
        self.add_messages(reporter.get_messages())

        # First come, first serve... We only overwrite
        # empty versions in the parent reporter
        if not self.trapi_version:
            self.trapi_version = reporter.trapi_version
        if not self.biolink_version:
            self.biolink_version = reporter.biolink_version

    def to_dict(self) -> Dict:
        return {
            "trapi_version": self.trapi_version,
            "biolink_version": self.biolink_version,
            "messages": self.get_messages()
        }

    def apply_validation(self, validation_method, *args, **kwargs) -> bool:
        """
        Wrapper to allow validation_methods direct access to the ValidatorReporter.

        :param validation_method: function which accepts this instance of the
               ValidatorReporter as its first argument, for use in reporting validation errors.
        :param args: any positional arguments to the validation_method, after the initial ValidatorReporter argument
        :param kwargs: any (optional, additional) keyword arguments to the validation_method, after positional arguments
        :return: bool, returns 'False' if validation method documented errors; True otherwise
        """
        validation_method(self, *args, **kwargs)
        if self.has_errors():
            return False
        else:
            return True

    @staticmethod
    def has_validation_errors(tag: str, case: Dict) -> bool:
        """

        :param tag: str, top level string key of the case 'dictionary' input
        :param case: Dict, containing error messages in a structurally similar
                     format to what is returned by the to_dict() method in this class.
        :return: True if the case contains validation messages
        """
        #
        # The 'case' dictionary object could have a format something like this:
        #
        #     tag: {
        #         "trapi_version": "1",
        #         "biolink_version": "2.4.7",
        #         "messages": {
        #             "information": [],
        #             "warnings": [
        #                 {
        #                     'code': "warning.deprecated",
        #                     'context': "Input",
        #                     "name": "biolink:ChemicalSubstance"
        #                 },
        #                 {
        #                     'code': "warning.predicate.non_canonical",
        #                     'predicate': "biolink:participates_in"
        #                 }
        #             ],
        #             "errors": []
        #         }
        #     }
        #
        # and we have non-empty "errors"
        if case is not None and tag in case and \
                'messages' in case[tag] and \
                'errors' in case[tag]['messages'] and \
                case[tag]['messages']['errors']:
            return True
        else:
            return False

    def display(self, **message) -> str:
        """
        Augmented message display wrapper prepends
        the ValidationReporter prefix to a
        resolved coded validation message.

        :return: str, full validation message
        """
        return self.prefix + CodeDictionary.display(**message)
