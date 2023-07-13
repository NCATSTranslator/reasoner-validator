"""Error and Warning Reporting Module"""
from typing import Optional, Dict, List
from sys import stdout
from importlib import metadata
from io import StringIO
import copy

from json import dumps, JSONEncoder

from reasoner_validator.message import (
    MESSAGE_CATALOG,
    MESSAGE_PARTITION,
    SCOPED_MESSAGES,
    IDENTIFIED_MESSAGES,
    MESSAGE_PARAMETERS
)
from reasoner_validator.validation_codes import CodeDictionary
from reasoner_validator.versioning import SemVer, SemVerError, get_latest_version

import logging
logger = logging.getLogger(__name__)


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
    General wrapper for managing validation status messages: information, warnings, errors and 'critical' (errors).
    The TRAPI version and Biolink Model versions are also tracked for convenience at this abstract level
    although their application is within specific pertinent subclasses.
    """

    # Default major version resolves to latest TRAPI OpenAPI release,
    # specifically 1.3.0, as of September 1st, 2022
    DEFAULT_TRAPI_VERSION = "1"

    _message_type_name: Dict[str, str] = {
        "info": "information",
        "warning": "warnings",
        "error": "errors",
        "critical": "critical"
    }

    def __init__(
            self,
            prefix: Optional[str] = None,
            trapi_version: Optional[str] = None,
            biolink_version: Optional[str] = None,
            strict_validation: bool = False
    ):
        """
        :param prefix: named context of the Validator, used as a prefix in validation messages.
        :type prefix: str
        :param trapi_version: version of component against which to validate the message.
                              Could be a TRAPI release SemVer or a Git branch identifier.
        :type trapi_version: Optional[str], target version of TRAPI upon which the validation is attempted
        :param biolink_version: Biolink Model (SemVer) release against which the knowledge graph is to be
                                validated (Default: if None, use the Biolink Model Toolkit default version).
        :type biolink_version: Optional[str] = None
        :param strict_validation: if True, abstract and mixin elements validate as 'error';
                                  if None or False, just issue a 'warning'
        :type strict_validation: Optional[bool] = None
        """
        self.prefix: str = prefix if prefix else ""
        self.trapi_version = get_latest_version(trapi_version) \
            if trapi_version else get_latest_version(self.DEFAULT_TRAPI_VERSION)
        self.biolink_version = biolink_version
        self.strict_validation: Optional[bool] = strict_validation
        self.messages: MESSAGE_CATALOG = {
            "critical": dict(),
            "errors": dict(),
            "warnings": dict(),
            "information": dict()
        }

    def get_trapi_version(self) -> str:
        """
        :return: str, TRAPI (SemVer) version currently targeted by the ValidationReporter.
        """
        return self.trapi_version

    def minimum_required_trapi_version(self, version: str) -> bool:
        """
        :param version: simple 'major.minor.patch' TRAPI schema release SemVer
        :return: True if current version is equal to, or newer than, a targeted 'minimum_version'
        """
        try:
            current: SemVer = SemVer.from_string(self.trapi_version)
            target: SemVer = SemVer.from_string(version)
            return current >= target
        except SemVerError as sve:
            logger.error(f"minimum_required_trapi_version() error: {str(sve)}")
            return False

    def get_biolink_version(self) -> str:
        """
        :return: Biolink Model version currently targeted by the ValidationReporter.
        :rtype biolink_version: str
        """
        return self.biolink_version

    def validate_biolink(self) -> bool:
        """
        Predicate to check if the Biolink (version) is
        tagged to 'suppress' compliance validation.

        :return: bool, returns 'True' if Biolink Validation is expected.
        """
        return self.biolink_version is None or self.biolink_version.lower() != "suppress"

    def is_strict_validation(self) -> bool:
        """
        :return: bool, value of validation strictness set in the ValidationReporter.
        """
        return self.strict_validation

    def has_messages(self) -> bool:
        """Predicate to detect any recorded validation messages.
        :return: bool, True if ValidationReporter has any non-empty messages.
        """
        return self.has_information() or self.has_warnings() or self.has_errors() or self.has_critical()

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

    def has_critical(self) -> bool:
        """Predicate to detect any recorded critical error messages.
        :return: bool, True if ValidationReporter has any critical error messages.
        """
        return bool(self.messages["critical"])

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

    def dump_critical(self, flat=False) -> str:
        """Dump critical error messages as JSON.
        :param flat: render output as 'flat' JSON (default: False)
        :return: str, JSON formatted string of critical error messages.
        """
        return _output(self.messages["critical"], flat)

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
        :return: message type, one of 'info', 'warning', 'error' or 'critical'
        """
        code_id_parts: List[str] = code.split('.')
        message_type: str = code_id_parts[0]
        if message_type in ['info', 'warning', 'error', 'critical']:
            return message_type
        else:
            raise NotImplementedError(
                f"ValidationReport.get_message_type(): {code} is unknown code type: {message_type}"
            )

    def report(self, code: str, source_trail: Optional[str] = None, **message):
        """
        Capture a single validation message, as per specified 'code' (with any code-specific contextural parameters).

        :param code: str, dot delimited validation path code
        :param source_trail, Optional[str], audit trail of knowledge source provenance for a given Edge, as a string.
                             Defaults to "global" if not specified.
        :param message: **Dict, named parameters representing extra (str-formatted) context for the given code message
        :return: None (internally record the validation message)
        """
        # Sanity check: that the given code has been registered in the codes.yaml file
        assert CodeDictionary.get_code_entry(code) is not None, f"ValidationReporter.report: unknown code '{code}'"

        message_type_id = self.get_message_type(code)
        message_type = self._message_type_name[message_type_id]
        if code not in self.messages[message_type]:
            self.messages[message_type][code] = dict()

        # Set current scope of validation message
        if source_trail is not None and source_trail not in self.messages[message_type][code]:
            scope = self.messages[message_type][code][source_trail] = dict()
        else:
            scope = self.messages[message_type][code]["global"] = dict()

        if message:
            # If a message has any parameters, then one of them is
            # expected to be a message indexing identifier
            if "identifier" in message:
                message_identifier = message.pop("identifier")
                if not message:
                    # the message_identifier was the only parameter to keep track of...
                    scope[message_identifier] = None
                else:
                    # keep track of additional parameters in a list of dictionaries
                    # (may have additional, currently unavoidable, content duplication?)
                    if message_identifier not in scope or scope[message_identifier] is None:
                        scope[message_identifier] = list()

                    scope[message_identifier].append(message)

        # else: additional parameters are None

    def add_messages(self, new_messages: MESSAGE_CATALOG):
        """
        Batch addition of a dictionary of messages to a ValidationReporter instance.
        :param new_messages: Dict[str, Dict], with key one of "information", "warnings", "errors" or "critical",
                              with 'code' keyed dictionaries of (structured) message parameters.
        """
        for message_type in self.messages:   # 'info', 'warning', 'error', 'critical'
            if message_type in new_messages:
                message_type_contents = new_messages[message_type]
                for code, details in message_type_contents.items():   # codes.yaml message codes
                    if code not in self.messages[message_type]:
                        self.messages[message_type][code] = dict()

                    # 'source' scope is 'global' or a source trail path string, from primary to topmost aggregator
                    for source, content in details.items():
                        scope = self.messages[message_type][code][source] = dict()
                        if content:
                            # content is of type Dict[str, Optional[List[Dict[str, str]]]]
                            # where dictionary keys are a set of message discriminating 'identifier'
                            identifier: str
                            parameters: Optional[List[Dict[str, str]]]
                            for identifier, parameters in content.items():
                                if self.messages[message_type][code] is None:
                                    self.messages[message_type][code] = dict()
                                if parameters:
                                    # additional parameters seen?
                                    if identifier not in self.messages[message_type][code] or \
                                            scope[identifier] is None:
                                        scope[identifier] = list()

                                    scope[identifier].extend(parameters)
                                else:
                                    # the message 'identifier' is the only parameter
                                    scope[identifier] = None

    def get_messages(self) -> MESSAGE_CATALOG:
        """
        Get copy of all messages as a Python data structure.
        :return: Dict (copy) of all validation messages in the ValidationReporter.
        """
        return copy.deepcopy(self.messages)

    def get_info(self) -> MESSAGE_PARTITION:
        """
        Get copy of all recorded 'information' messages.
        :return: List, copy of all information messages.
        """
        return copy.deepcopy(self.messages["information"])

    def get_warnings(self) -> MESSAGE_PARTITION:
        """
        Get copy of all recorded 'warning' messages.
        :return: List, copy of all warning messages.
        """
        return copy.deepcopy(self.messages["warnings"])

    def get_errors(self) -> MESSAGE_PARTITION:
        """
        Get copy of all recorded 'error' messages.
        :return: List, copy of all error messages.
        """
        return copy.deepcopy(self.messages["errors"])

    def get_critical(self) -> MESSAGE_PARTITION:
        """
        Get copy of all recorded 'critical' error messages.
        :return: List, copy of all critical error messages.
        """
        return copy.deepcopy(self.messages["critical"])

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
        :return: bool, returns 'False' if validation method documented (critical) errors; True otherwise
        """
        validation_method(self, *args, **kwargs)
        # TODO: not sure if we should detect both 'errors' and 'critical' here or just 'critical'
        if self.has_critical() or self.has_errors():
            return False
        else:
            return True

    @staticmethod
    def test_case_has_validation_errors(tag: str, case: Dict) -> bool:
        """Check if test case has validation errors.

        :param tag: str, top level string key in the 'case' whose value is the validation messages 'dictionary'
        :param case: Dict, containing error messages in a structurally similar
                     format to what is returned by the to_dict() method in this class.
        :return: True if the case contains validation messages
        """
        # TODO: not sure if we should detect both 'errors' and 'critical' here or just 'critical'
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
        #                     "warning.predicate.non_canonical": {
        #                         "infores:molepro -> infores:arax": {  # local source scope of error
        #                             "biolink:participates_in": {
        #                                   "edge_id": "a--['biolink:participates_in']->b"
        #                             }
        #                         }
        #                     }
        #                 }
        #             ],
        #             "errors": [
        #                 {
        #                     "error.knowledge_graph.empty_nodes": {
        #                         "global": None  # scope of error
        #                     }
        #                 }
        #             ],
        #             "critical": [
        #                 {
        #                     "critical.trapi.validation": {
        #                         "global": None   # scope of critical error
        #                     }
        #                 }
        #             ]
        #         }
        #     }
        #
        # where 'tag' == 'messages' and we have a non-empty "errors" set of messages
        #
        if case is not None and tag in case and \
                'messages' in case[tag] and \
                (
                    'errors' in case[tag]['messages'] and case[tag]['messages']['errors'] or
                    'critical' in case[tag]['messages'] and case[tag]['messages']['critical']
                ):
            return True
        else:
            return False

    def dump(
            self,
            title: Optional[str] = "",
            id_rows: int = 0,
            msg_rows: int = 0,
            compact_format: bool = False,
            file=stdout
    ):
        """
        Dump all available messages captured by the ValidationReporter,
        printed as formatted human-readable text, on a specified file device.

        :param title: Optional[str], user supplied report title (default: autogenerated if not set or empty string;
                                     suppressed if an explicit argument of None is given); default: "" -> default title
        :param id_rows: int >= 0, if set, maximum number of code-related identifiers to
                             print per code (value of 0 means print all; default: 0)
        :param msg_rows: int >= 0, if set, maximum number of parameterized code-related messages to
                                  print per identifier row (value of 0 means print all; default: 0)
        :param compact_format: bool, if True, omit blank lines inserted by default for human readability;
                               also, suppress character escapes (i.e. underlining of titles) (default: False)
        :param file: target file device for output
        :return: n/a
        """
        assert id_rows >= 0, "dump(): 'id_rows' argument must be positive or equal to zero"
        assert msg_rows >= 0, "dump(): 'pm_rows' argument must be positive or equal to zero"

        if title is not None:

            if not compact_format:
                print(file=file)

            if not title:
                title = f"Validation Report"
                title += f" for '{self.prefix}'" if self.prefix else ""

            if not compact_format:
                print(f"\n\033[4m{title}\033[0m", file=file)
                print(file=file)
            else:
                # compact also ignores underlining
                print(title, file=file)

        print(
            f"Reasoner Validator version '{metadata.version('reasoner-validator')}' validating against "
            f"TRAPI schema version '{str(self.trapi_version if self.trapi_version is not None else 'Default')}' " +
            "and Biolink Model version " +
            f"'{str(self.biolink_version if self.biolink_version is not None else 'Default')}'.\n",
            file=file
        )

        if self.has_messages():

            # self.messages is a MESSAGE_CATALOG where MESSAGE_CATALOG is Dict[<message type>, MESSAGE_PARTITION]
            # <message type> is the top level partition of messages into 'critical', 'error', 'warning' or 'info'
            message_type: str
            coded_messages: MESSAGE_PARTITION
            for message_type, coded_messages in self.messages.items():

                # if there are coded validation messages for a
                # given message type: 'critical', 'error', 'warning' or 'info' ...
                if coded_messages:

                    # ... then iterate through them and print them out

                    if not compact_format:
                        print(f"\033[4m{message_type.capitalize()}\033[0m", file=file)
                        print(file=file)
                    else:
                        # compact also ignores underlining
                        print(f"\n{message_type.capitalize()}:", file=file)

                    # 'coded_messages' is a MESSAGE_PARTITION where
                    # MESSAGE_PARTITION is Dict[<validation code>, SCOPED_MESSAGES]

                    # 'validation code' is the dot-delimited string
                    # representation of the YAML path of the message codes.yaml
                    code: str
                    messages_by_code:  SCOPED_MESSAGES

                    # Grouping message outputs by validation codes
                    for code, messages_by_code in coded_messages.items():

                        code_label: str = CodeDictionary.validation_code_tag(code)
                        print(
                            f"* {code_label}:\n"
                            f"=> {CodeDictionary.get_message_template(code)}",
                            file=file
                        )
                        if not compact_format:
                            print(file=file)

                        # 'messages_by_code' is a SCOPED_MESSAGES where
                        # SCOPED_MESSAGES is Dict[<scope>, Optional[IDENTIFIED_MESSAGES]]

                        # <scope> is "global" or source trail path string
                        scope: str
                        messages_by_scope: Optional[IDENTIFIED_MESSAGES]
                        for scope, messages_by_scope in messages_by_code.items():

                            print(f"\t$ {scope}", file=file)

                            # Codes with associated parameters should have
                            # an embedded dictionary with 'identifier' keys

                            ids_per_row: int = 0
                            num_ids: int = len(messages_by_scope.keys())
                            more_ids: int = num_ids - id_rows if num_ids > id_rows else 0

                            # 'messages_by_scope' is Optional[IDENTIFIED_MESSAGES] where
                            # 'IDENTIFIED_MESSAGES' is Dict[<identifier>, Optional[List[MESSAGE_PARAMETERS]]]

                            # An entry of 'messages_by_scope' may be None if the given message code
                            # has no additional parameters that distinguish instances of context (e.g. edge id?)
                            # where the validation message occurs for the given identifier.

                            # unique 'identifier' discriminator of the
                            # (TRAPI or Biolink) token target of the validation
                            identifier: str
                            messages: Optional[List[MESSAGE_PARAMETERS]]
                            for identifier, messages in messages_by_scope.items():

                                if messages is None:

                                    # For codes whose context of validation is solely discerned
                                    # with their identifier, just print out the identifier

                                    print(f"\t\t# {identifier}", file=file)

                                    if not compact_format:
                                        print(file=file)

                                else:
                                    # Since we have already checked if messages is None above, then we assume here that
                                    # 'messages' is a List[MESSAGE_PARAMETERS] which records distinct additional context
                                    # for a list of messages associated with a given code.
                                    print(f"\t\t# {identifier}:", file=file)

                                    first_message: bool = True
                                    messages_per_row: int = 0
                                    num_messages: int = len(messages)
                                    more_msgs: int = num_messages - msg_rows if num_messages > msg_rows else 0

                                    # 'messages' is an instance List[MESSAGE_PARAMETERS] where every entry of
                                    # 'MESSAGE_PARAMETERS' is a dictionary of additional parameters documenting
                                    # one specific instance of validation message related to the given identifier,
                                    # where the keys are validation code specific (documented in codes.yaml)
                                    parameters: MESSAGE_PARAMETERS
                                    for parameters in messages:

                                        if first_message:
                                            tags = tuple(parameters.keys())
                                            print(f"\t\t- {' | '.join(tags)}: ", file=file)
                                            first_message = False

                                        print(f"\t\t\t{' | '.join(parameters.values())}", file=file)

                                        messages_per_row += 1
                                        if msg_rows and messages_per_row >= msg_rows:
                                            if more_msgs:
                                                print(
                                                    f"\t\t{str(more_msgs)} more messages " +
                                                    f"for identifier '{identifier}'...",
                                                    file=file
                                                )
                                            break

                                    if not compact_format:
                                        print(file=file)

                                ids_per_row += 1
                                if id_rows and ids_per_row >= id_rows:
                                    if more_ids:
                                        print(
                                            f"{str(more_ids)} more identifiers for code '{code_label}'...",
                                            file=file
                                        )
                                    break

                            if not compact_format:
                                print(file=file)

                        # else:
                        #     For codes with associated non-parametric templates,
                        #     just printing the template (done above) suffices

                # else: print nothing if a given message_type has no messages
        else:
            print(f"Hurray! No validation messages reported!", file=file)

    def dumps(
            self,
            id_rows: int = 0,
            msg_rows: int = 0,
            compact_format: bool = True
    ) -> str:
        """
        Text string version of dump(): returns all available messages captured by the
        ValidationReporter, as a formatted human-readable text blob.

        :param id_rows: int >= 0, if set, maximum number of code-related identifiers to
                             print per code (value of 0 means print all; default: 0)
        :param msg_rows: int >= 0, if set, maximum number of parameterized code-related messages to
                                  print per identifier row (value of 0 means print all; default: 0)
        :param compact_format: bool, if True, omit blank lines inserted by default for human readability (default: True)
        :return: n/a
        """
        output_buffer: StringIO = StringIO()
        self.dump(
            title=None,  # title suppressed in dumps() string output
            id_rows=id_rows,
            msg_rows=msg_rows,
            compact_format=compact_format,
            file=output_buffer
        )
        text_output: str = output_buffer.getvalue()
        output_buffer.close()
        return text_output.strip()
