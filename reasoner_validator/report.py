"""Error and Warning Reporting Module"""
import copy
from typing import Optional, Set, Dict, List
from json import dumps


def _output(json, flat=False):
    return dumps(json, sort_keys=False, indent=None if flat else 4)


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
        self.trapi_version = trapi_version if trapi_version else self.DEFAULT_TRAPI_VERSION
        self.biolink_version = biolink_version
        self.messages: Dict[str, Set[str]] = {
            "information": set(),
            "warnings": set(),
            "errors": set()
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

    def validate(self, validation_method, *args, **kwargs) -> bool:
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
