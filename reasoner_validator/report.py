"""Error and Warning Reporting Module"""
import copy
from typing import Optional, Dict, List
from json import dumps, JSONEncoder

from reasoner_validator.validation_codes import CodeDictionary
from reasoner_validator.versioning import latest


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
        :return: str, TRAPI (SemVer) version currently targeted by the ValidationReporter.
        """
        return self.trapi_version

    def get_biolink_version(self) -> str:
        """
        :return: Biolink Model version currently targeted by the ValidationReporter.
        :rtype biolink_version: str
        """
        return self.biolink_version

    def is_strict_validation(self) -> bool:
        """
        :return: bool, value of validation strictness set in the ValidationReporter.
        """
        return self.strict_validation

    def has_messages(self) -> bool:
        """Predicate to detect any recorded validation messages.
        :return: bool, True if ValidationReporter has any non-empty messages.
        """
        return self.has_information() or self.has_warnings() or self.has_errors()

    def has_information(self) -> bool:
        """Predicate to detect any recorded information messages.
        :return: bool, True if ValidationReporter has any information messages.
        """
        return bool(self.messages["information"])

    def has_warnings(self) -> bool:
        """Predicate to detect any recorded warning messages.
        :return: bool, True if ValidationReporter has any warning messages.
        """
        return bool(self.messages["warnings"])

    def has_errors(self) -> bool:
        """Predicate to detect any recorded error messages.
        :return: bool, True if ValidationReporter has any error messages.
        """
        return bool(self.messages["errors"])

    def dump_info(self, flat=False) -> str:
        """Dump information messages as JSON.
        :param flat: render output as 'flat' JSON (default: False)
        :return: str, JSON formatted string of information messages.
        """
        return _output(self.messages["information"], flat)

    def dump_warnings(self, flat=False) -> str:
        """Dump warning messages as JSON.
        :param flat: render output as 'flat' JSON (default: False)
        :return: str, JSON formatted string of warning messages.
        """
        return _output(self.messages["warnings"], flat)

    def dump_errors(self, flat=False) -> str:
        """Dump error messages as JSON.
        :param flat: render output as 'flat' JSON (default: False)
        :return: str, JSON formatted string of error messages.
        """
        return _output(self.messages["errors"], flat)

    def dump_messages(self, flat=False) -> str:
        """Dump all messages as JSON.
        :param flat: render output as 'flat' JSON (default: False)
        :return: str, JSON formatted string of all messages.
        """
        return _output(self.messages, flat)

    @staticmethod
    def get_message_type(code: str) -> str:
        """Get type of message code.
        :param code: message code
        :return: message type, one of 'info', 'warning' or 'error'
        """
        code_id_parts: List[str] = code.split('.')
        message_type: str = code_id_parts[0]
        if message_type in ['info', 'warning', 'error']:
            return message_type
        else:
            raise NotImplementedError(
                f"ValidationReport.get_message_type(): {code} is unknown code type: {message_type}"
            )

    def report(self, code: str, **message):
        """
        Capture a single validation message, as per specified 'code' (with any code-specific contextural parameters)
        :param code: 
        :param message: named parameters representing extra (str-formatted) context for the given code message
        :return: None (internally record the validation message)
        """
        message_type = self.get_message_type(code)
        message_set = self._message_type_name[message_type]
        message['code'] = code  # add the code into the message
        self.messages[message_set].append(message)

    def add_messages(self, new_messages: Dict[str, List]):
        """
        Batch addition of a dictionary of messages to a ValidationReporter instance.

        :param new_messages: Dict[str, List], with key one of
                             "information", "warnings" or "errors",
                              with Lists of (structured) messages.
        """
        for key in self.messages:
            if key in new_messages:
                self.messages[key].extend(new_messages[key])

    def get_messages(self) -> Dict[str, List[Dict]]:
        """
        Get copy of all messages as a Python data structure.
        :return: Dict (copy) of all validation messages in the ValidationReporter.
        """
        return copy.deepcopy(self.messages)

    def get_info(self) -> List:
        """
        Get copy of all recorded information messages.
        :return: List, copy of all information messages.
        """
        return copy.deepcopy(self.messages["information"])

    def get_warnings(self) -> List:
        """
        Get copy of all recorded warning messages.
        :return: List, copy of all warning messages.
        """
        return copy.deepcopy(self.messages["warnings"])

    def get_errors(self) -> List:
        """
        Get copy of all recorded error messages.
        :return: List, copy of all error messages.
        """
        return copy.deepcopy(self.messages["errors"])

    ############################
    # General Instance methods #
    ############################
    def merge(self, reporter):
        """
        Merge all messages and metadata from a second ValidationReporter,
        into the calling ValidationReporter instance.

        :param reporter: second ValidationReporter
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
        """
        Export ValidationReporter contents as a Python dictionary
        (including TRAPI version, Biolink Model version and messages)
        :return: Dict
        """
        return {
            "trapi_version": self.trapi_version,
            "biolink_version": self.biolink_version,
            "messages": self.get_messages()
        }

    def apply_validation(self, validation_method, *args, **kwargs) -> bool:
        """
        Wrapper to allow validation_methods direct access to the ValidationReporter.

        :param validation_method: function which accepts this instance of the
               ValidationReporter as its first argument, for use in reporting validation errors.
        :param args: any positional arguments to the validation_method, after the initial ValidationReporter argument
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
        """Check if test case has validation errors.

        :param tag: str, top level string key in the 'case' whose value is the validation messages 'dictionary'
        :param case: Dict, containing error messages in a structurally similar
                     format to what is returned by the to_dict() method in this class.
        :return: True if the case contains validation messages
        """

        #
        # The 'case' dictionary object could have a format something like this:
        #
        #     tag: {
        #         "trapi_version": "1.3",
        #         "biolink_version": "3.0.2",
        #         "messages": {
        #             "information": [],
        #             "warnings": [
        #                 {
        #                     'code': "warning.predicate.non_canonical",
        #                     'predicate': "biolink:participates_in"
        #                 }
        #             ],
        #             "errors": [
        #                 {
        #                     'code': "error.knowledge_graph.empty_nodes"
        #                 }
        #             ]
        #         }
        #     }
        #
        # where 'tag' == 'messages' and we have a non-empty "errors" set of messages
        #
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
        :return: str, fully rendered validation message
        """
        return self.prefix + CodeDictionary.display(**message)
