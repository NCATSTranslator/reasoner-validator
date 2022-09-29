"""Error and Warning Reporting Module"""
from os.path import join, abspath, dirname
import copy
from typing import Optional, Set, Dict, List
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
    def _code_value(cls, tag_path) -> Optional[str]:
        """
        Get value of specified dot delimited tag name
        :param tag_path:
        :return:
        """
        if not tag_path:
            return None

        codes: Dict = cls._get_code_dictionary()
        parts = tag_path.split(".")
        return cls._get_nested_code_value(codes, parts, 0)

    @staticmethod
    def display(**context):
        assert context and 'code' in context  # should be non-empty, containing a code
        code: str = context.pop('code')
        template: str = CodeDictionary._code_value(code)
        if context:
            # Message template parameterized with additional named parameter
            # message context, assumed to be referenced by the template
            return template.format(**context)
        else:
            # simple scalar message without parameterization?
            return template


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

    def __init__(
            self,
            prefix: Optional[str] = None,
            trapi_version: Optional[str] = None,
            biolink_version: Optional[str] = None
    ):
        self.prefix: str = prefix + ": " if prefix else ""
        self.trapi_version = trapi_version if trapi_version else latest.get(self.DEFAULT_TRAPI_VERSION)
        self.biolink_version = biolink_version
        self.messages: Dict[str, Set[str]] = {
            "information": set(),
            "warnings": set(),
            "errors": set()
        }
        # new code reporting format?
        self.coded_messages: List[Dict[str, str]] = list()

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

    ############################
    # Legacy messaging methods #
    ############################
    def info(self, err_msg: str):
        """
        Capture an informative message to report from the Validator.

        :param err_msg: error message to report.
        :type err_msg: str
        """
        self.messages["information"].add(f"{self.prefix}INFO - {err_msg}")

    def warning(self, err_msg: str):
        """
        Capture a warning message to report from the Validator.

        :param err_msg: error message to report.
        :type err_msg: str
        """
        self.messages["warnings"].add(f"{self.prefix}WARNING - {err_msg}")

    def error(self, err_msg: str):
        """
        Capture an error message to report from the Validator.

        :param err_msg: error message to report.
        :type err_msg: str
        """
        self.messages["errors"].add(f"{self.prefix}ERROR - {err_msg}")

    def add_messages(self, new_messages: Dict[str, Set[str]]):
        """
        Batch addition of a dictionary of messages to a ValidatorReporter instance..

        :param new_messages: Dict[str, Set[str]], with key one of
                             "information", "warnings" or "errors",
                              with Sets of associated message strings.
        """
        for key in self.messages:
            if key in new_messages:
                self.messages[key].update(new_messages[key])

    def has_messages(self) -> bool:
        return bool(self.messages["information"] or self.messages["warnings"] or self.messages["errors"])

    def has_information(self) -> bool:
        return bool(self.messages["information"])

    def has_warnings(self) -> bool:
        return bool(self.messages["warnings"])

    def has_errors(self) -> bool:
        return bool(self.messages["errors"])

    def get_info(self) -> List:
        return list(self.messages["information"])

    def get_warnings(self) -> List:
        return list(self.messages["warnings"])

    def get_errors(self) -> List:
        return list(self.messages["errors"])

    def dump_info(self, flat=False) -> str:
        return _output(self.messages["information"], flat)

    def dump_warnings(self, flat=False) -> str:
        return _output(self.messages["warnings"], flat)

    def dump_errors(self, flat=False) -> str:
        return _output(self.messages["errors"], flat)

    ############################
    # Legacy messaging methods #
    ############################
    def report(self, **message):
        self.coded_messages.append(message)

    def get_report(self) -> List[Dict[str, str]]:
        return copy.deepcopy(self.coded_messages)

    ############################
    # General Instance methods #
    ############################
    # TODO: should the return value be an immutable NamedTuple instead?
    def get_messages(self) -> Dict[str, Set[str]]:
        """
        :return: Dict[str, Set[str]], of "information", "warnings" or "errors" indexed sets of string messages
        """
        return copy.deepcopy(self.messages)

    def merge(self, reporter):
        """
        Merge all messages and metadata from a second ValidatorReporter,
        into the calling ValidatorReporter instance.

        :param reporter: second ValidatorReporter
        """
        assert isinstance(reporter, ValidationReporter)
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

    def report_to_dict(self) -> Dict:
        return {
            "trapi_version": self.trapi_version,
            "biolink_version": self.biolink_version,
            "report": self.get_report()
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
        #                 "Validation: WARNING - Input Biolink class 'biolink:ChemicalSubstance' is deprecated?",
        #                 "Validation: WARNING - Input predicate 'biolink:participates_in' is non-canonical!"
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
