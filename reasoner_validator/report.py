"""Error and Warning Reporting Module"""
from typing import Set, Dict


class ValidationReporter:

    def __init__(self, prefix: str):
        self.prefix: str = prefix
        self.information: Set[str] = set()
        self.warnings: Set[str] = set()
        self.errors: Set[str] = set()

    def info(self, err_msg: str):
        """
        Capture an informative message to report from the Validator.

        :param err_msg: error message to report.
        :type err_msg: str
        """
        self.information.add(f"{self.prefix}: INFO -{err_msg}")

    def warning(self, err_msg: str):
        """
        Capture a warning message to report from the Validator.

        :param err_msg: error message to report.
        :type err_msg: str
        """
        self.warnings.add(f"{self.prefix}: WARNING - {err_msg}")

    def error(self, err_msg: str):
        """
        Capture an error message to report from the Validator.

        :param err_msg: error message to report.
        :type err_msg: str
        """
        self.errors.add(f"{self.prefix}: ERROR - {err_msg}")

    # TODO: should the return value be an immutable NamedTuple instead?
    def get_messages(self) -> Dict[str, Set[str]]:
        return {
            "information": self.information,
            "warnings": self.warnings,
            "errors": self.errors
        }
