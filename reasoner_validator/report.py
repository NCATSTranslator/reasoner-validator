"""Error and Warning Reporting Module"""
import copy
from typing import Optional, Set, Dict


class ValidationReporter:

    def __init__(self, prefix: Optional[str] = None):
        self.prefix: str = prefix + ": " if prefix else ""
        self.messages: Dict[str, Set[str]] = {
            "information": set(),
            "warnings": set(),
            "errors": set()
        }

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

    # TODO: should the return value be an immutable NamedTuple instead?
    def get_messages(self) -> Dict[str, Set[str]]:
        """
        :return: Dict[str, Set[str]], of "information", "warnings" or "errors" indexed sets of string messages
        """
        return copy.deepcopy(self.messages)

    def merge(self, reporter):
        """
        Merge all the messages from a second ValidatorReporter, in the calling ValidatorReporter instance.
        :param reporter: second ValidatorReporter
        """
        assert isinstance(reporter, ValidationReporter)
        for key in self.messages:
            self.messages[key].update(reporter.messages[key])

