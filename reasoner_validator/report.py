"""Error and Warning Reporting Module"""
from enum import Enum
from typing import Optional, Dict, List
from sys import stdout
from importlib import metadata
from io import StringIO
import copy

from json import dumps, JSONEncoder

from reasoner_validator.message import (
    MessageType,
    MESSAGE_CATALOG,
    MESSAGE_PARTITION,
    IDENTIFIED_MESSAGES,
    MESSAGE_PARAMETERS,
    MESSAGES_BY_TARGET,
    MESSAGES_BY_TEST
)
from reasoner_validator.validation_codes import CodeDictionary

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


class TRAPIGraphType(Enum):
    """ Enum type of Biolink Model compliant graph data being validated."""
    Input_Edge = "Input Edge"
    Query_Graph = "Query Graph"
    Knowledge_Graph = "Knowledge Graph"

    def label(self) -> str:
        return self.value.lower().replace(" ", "_")


class ValidationReporter:
    """
    General wrapper for managing validation status messages: information, warnings, errors and 'critical' (errors).
    The TRAPI version and Biolink Model versions are also tracked for convenience at this abstract level
    although their application is within specific pertinent subclasses.
    """

    # Default major version resolves to latest TRAPI OpenAPI release,
    # specifically 1.3.0, as of September 1st, 2022
    DEFAULT_TRAPI_VERSION = "1"

    def __init__(
            self,
            default_test: Optional[str] = None,
            default_target: Optional[str] = None,
            strict_validation: Optional[bool] = None
    ):
        """
        :param default_test: Optional[str] =  None, initial default test context of the Validator messages
                             Default "global" if not provided.
        :param default_target: Optional[str] =  None, initial default target context of the Validator,
                               also used as a prefix in validation messages. Default "global" if not provided.
        :param strict_validation: Optional[bool] = None, if True, some tests validate as 'error';  False, simply issues
                                  'info' message; A value of 'None' uses the default value for specific graph contexts.
        """
        self.default_test: str = default_test if default_test else "Test"
        self.default_target: str = default_target if default_target else "Target"
        self.strict_validation: Optional[bool] = strict_validation
        self.messages: MESSAGES_BY_TARGET = dict()

    def reset_default_test(self, name: str):
        """
        Resets the default test identifier of the ValidationReporter to a new string.
        :param name: str, new default test identifier
        :return: None
        """
        self.default_test = name

    def get_default_test(self) -> str:
        """
        Returns the current default test identifier of the ValidationReporter.
        :return: str, current default test identifier
        """
        return self.default_test

    def reset_default_target(self, name: str):
        """
        Resets the default target identifier of the ValidationReporter to a new string.
        :param name: str, new default target identifier (generally a URL, URI or CURIE)
        :return: None
        """
        self.default_target = name

    def get_default_target(self) -> str:
        """
        Returns the current target of the ValidationReporter.
        :return: str, current target
        """
        return self.default_target

    def is_strict_validation(self, graph_type: TRAPIGraphType, ignore_graph_type: bool = False) -> bool:
        """
        Predicate to test if strict validation is to be applied. If the internal
        'strict_validation' flag is not set (i.e. None), then graph_type is
        to resolve strictness based on TRAPI graph type context.

        :param graph_type: TRAPIGraphType, type of TRAPI graph component being validated
        :param ignore_graph_type: bool, if strict validation is None (not set globally), then
               only apply graph-type-differential strict validation if 'ignore_graph_type' is False
        :return: bool, value of validation strictness set in the ValidationReporter.
        """
        if self.strict_validation is None:
            if not ignore_graph_type and graph_type == TRAPIGraphType.Knowledge_Graph:
                return True
            else:
                return False
        else:
            return self.strict_validation

    def get_messages_by_target(self, target: Optional[str] = None) -> MESSAGES_BY_TEST:
        """
        Returns a block of MESSAGES_BY_TEST corresponding to a given or default target.
        :param target: str, specified target (gets current 'default' target if not given)
        :return: MESSAGES_BY_TEST corresponding to a resolved target
        """
        current_target = target if target else self.get_default_target()
        if current_target not in self.messages:
            self.messages[current_target] = dict()
        return self.messages[current_target]

    def get_messages_by_test(self, test: Optional[str] = None, target: Optional[str] = None) -> MESSAGE_CATALOG:
        """
        Returns MESSAGE_CATALOG corresponding to a given or default target.
        Note that the dictionary returned is not a copy of the original
         thus caution should be taken not to mutate it!
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: MESSAGES_BY_TEST corresponding to a resolved target
        """
        messages_by_test: MESSAGES_BY_TEST = self.get_messages_by_target(target=target)
        current_test = test if test else self.get_default_test()
        if current_test not in messages_by_test:
            messages_by_test[current_test] = {name: dict() for name in MessageType.__members__}
        return messages_by_test[current_test]

    def has_messages(self, test: Optional[str] = None, target: Optional[str] = None) -> bool:
        """Predicate to detect any recorded validation messages.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: bool, True if ValidationReporter has any non-empty messages.
        """
        return (
                self.has_information(test, target) or
                self.has_skipped(test, target) or
                self.has_warnings(test, target) or
                self.has_errors(test, target) or
                self.has_critical(test, target)
        )

    def has_message_type(
            self,
            message_type: MessageType,
            test: Optional[str] = None,
            target: Optional[str] = None
    ) -> bool:
        """Predicate to detect if ValidationReporter has any non-empty messages of type 'message_type'.
        :param message_type: MessageType, type of message whose presence is to be detected.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: bool, true only if ValidationReporter has any non-empty messages of type 'message_type'.
        """
        message_catalog: MESSAGE_CATALOG = self.get_messages_by_test(test=test, target=target)
        return bool(message_catalog[message_type.name])

    def has_information(self, test: Optional[str] = None, target: Optional[str] = None) -> bool:
        """Predicate to detect any recorded information messages.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: bool, True if ValidationReporter has any 'information' messages.
        """
        return self.has_message_type(MessageType.info, test=test, target=target)

    def has_skipped(self, test: Optional[str] = None, target: Optional[str] = None) -> bool:
        """Predicate to detect any recorded 'skipped test' messages.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: bool, True if ValidationReporter has any 'skipped tests' messages.
        """
        return self.has_message_type(MessageType.skipped,  test=test, target=target)

    def has_warnings(self, test: Optional[str] = None, target: Optional[str] = None) -> bool:
        """Predicate to detect any recorded warning messages.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: bool, True if ValidationReporter has any 'warning' messages.
        """
        return self.has_message_type(MessageType.warning,  test=test, target=target)

    def has_errors(self, test: Optional[str] = None, target: Optional[str] = None) -> bool:
        """Predicate to detect any recorded error messages.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: bool, True if ValidationReporter has any 'error' messages.
        """
        return self.has_message_type(MessageType.error,  test=test, target=target)

    def has_critical(self, test: Optional[str] = None, target: Optional[str] = None) -> bool:
        """Predicate to detect any recorded critical error messages.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: bool, True if ValidationReporter has any 'critical error' messages.
        """
        return self.has_message_type(MessageType.critical,  test=test, target=target)

    def dump_messages_type(
            self,
            message_type: MessageType,
            test: Optional[str] = None,
            target: Optional[str] = None,
            flat=False
    ) -> str:
        """Dump ValidationReporter messages of type 'message_type' as JSON.
        :param message_type: MessageType, type of message whose presence is to be detected.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :param flat: render output as 'flat' JSON (default: False)
        :return: bool, true only if ValidationReporter has any non-empty messages of type 'message_type'.
        """
        message_catalog: MESSAGE_CATALOG = self.get_messages_by_test(test=test, target=target)
        return _output(message_catalog[message_type.name], flat)

    def dump_info(self, test: Optional[str] = None, target: Optional[str] = None, flat=False) -> str:
        """Dump 'information' messages as JSON.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :param flat: render output as 'flat' JSON (default: False)
        :return: str, JSON formatted string of information messages.
        """
        return self.dump_messages_type(MessageType.info, test=test, target=target, flat=flat)

    def dump_skipped(self, test: Optional[str] = None, target: Optional[str] = None, flat=False) -> str:
        """Dump 'skipped test' messages as JSON.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :param flat: render output as 'flat' JSON (default: False)
        :return: str, JSON formatted string of 'skipped test' messages.
        """
        return self.dump_messages_type(MessageType.skipped, test=test, target=target, flat=flat)

    def dump_warnings(self, test: Optional[str] = None, target: Optional[str] = None, flat=False) -> str:
        """Dump 'warning' messages as JSON.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :param flat: render output as 'flat' JSON (default: False)
        :return: str, JSON formatted string of warning messages.
        """
        return self.dump_messages_type(MessageType.warning, test=test, target=target, flat=flat)

    def dump_errors(self, test: Optional[str] = None, target: Optional[str] = None, flat=False) -> str:
        """Dump 'error' messages as JSON.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :param flat: render output as 'flat' JSON (default: False)
        :return: str, JSON formatted string of error messages.
        """
        return self.dump_messages_type(MessageType.error, test=test, target=target, flat=flat)

    def dump_critical(self, test: Optional[str] = None, target: Optional[str] = None, flat=False) -> str:
        """Dump critical error messages as JSON.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :param flat: render output as 'flat' JSON (default: False)
        :return: str, JSON formatted string of critical error messages.
        """
        return self.dump_messages_type(MessageType.critical, test=test, target=target, flat=flat)

    def dump_all_messages(self, test: Optional[str] = None, target: Optional[str] = None, flat=False) -> str:
        """Dump **all** messages for a given test from a given target, as JSON.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :param flat: render output as 'flat' JSON (default: False)
        :return: str, JSON formatted string of all messages of test for target.
        """
        message_catalog: MESSAGE_CATALOG = self.get_messages_by_test(test=test, target=target)
        return _output(message_catalog, flat)

    @staticmethod
    def get_message_type(code: str) -> MessageType:
        """Get messages by message code.
        :param code: message code
        :return: MessageType
        """
        code_id_parts: List[str] = code.split('.')
        message_type: str = code_id_parts[0]
        if message_type in MessageType.__members__:
            return MessageType[message_type]
        else:
            raise NotImplementedError(
                f"ValidationReport.get_message_type(): {code} is unknown code type: {message_type}"
            )

    def report(
            self,
            code: str,
            test: Optional[str] = None,
            target: Optional[str] = None,
            **message
    ):
        """
        Capture a single validation message, as per specified
        'code' (with any code-specific contextual parameters).

        :param code: Dot delimited validation path code string
        :param test: Specified test name string (gets current 'default' test if not given)
        :param target: Specified target name string (gets current 'default' test if not given)
        :param message: Named parameter dictionary representing extra context for the given code message

        :return: None (internally record the validation message)
        """
        # Sanity check: that the given code has been registered in the codes.yaml file
        assert CodeDictionary.get_code_entry(code) is not None, f"ValidationReporter.report: unknown code '{code}'"

        # Rarely, get_message_type_label() can raise a
        # "KeyError" if the message_type_id is unknown?
        message_type: MessageType = self.get_message_type(code)

        message_catalog: MESSAGE_CATALOG = self.get_messages_by_test(test=test, target=target)
        messages: message_catalog[message_type.name]

        if code not in message_catalog[message_type.name]:
            message_catalog[message_type.name][code] = dict()

        partition = message_catalog[message_type.name][code]

        if message:
            # If a message has any parameters, then one of them is
            # expected to be a message indexing identifier
            if "identifier" in message:
                message_identifier = message.pop("identifier")
                if not message:
                    # the message_identifier was the only parameter to keep track of...
                    partition[message_identifier] = None
                else:
                    # keep track of additional parameters in a list of dictionaries
                    # (may have additional, currently unavoidable, content duplication?)
                    if message_identifier not in partition or partition[message_identifier] is None:
                        partition[message_identifier] = list()

                    partition[message_identifier].append(message)

        # else: additional parameters are None

    def add_messages(self, new_messages: MESSAGES_BY_TARGET):
        """
        Batch addition of MESSAGES_BY_TARGET messages to a ValidationReporter instance.
        :param new_messages: MESSAGES_BY_TARGET, messages indexed by target, test and categories:
                             one of "information", "skipped tests", "warnings", "errors" or "critical",
                             with code-keyed dictionaries of (structured) message parameters.
        """
        target: str
        target_messages: MESSAGES_BY_TEST
        for target, target_messages in new_messages.items():
            test: str
            new_message_catalog: MESSAGE_CATALOG
            for test, new_message_catalog in target_messages.items():
                this_message_catalog: MESSAGE_CATALOG = self.get_messages_by_test(test=test, target=target)
                for message_type in [name for name in MessageType.__members__]:
                    if message_type in new_message_catalog.keys():
                        new_message_type_entry: Dict = new_message_catalog[message_type]
                        this_message_type_entry: Dict = this_message_catalog[message_type]
                        code: str
                        content: Optional[IDENTIFIED_MESSAGES]
                        for code, content in new_message_type_entry.items():
                            if code not in this_message_type_entry:
                                this_message_type_entry[code] = dict() if content else None
                            partition = this_message_type_entry[code]
                            if content:
                                # content is of type IDENTIFIED_MESSAGES
                                # where dictionary keys are a set of
                                # message discriminating 'identifier'
                                identifier: str
                                parameters: Optional[IDENTIFIED_MESSAGES]
                                for identifier, parameters in content.items():
                                    if parameters:
                                        # additional parameters seen, then capture
                                        if partition is None:
                                            partition = this_message_type_entry[code][code] = dict()
                                        if identifier not in partition or partition[identifier] is None:
                                            partition[identifier] = list()
                                        partition[identifier].extend(parameters)
                                    else:
                                        # the message 'identifier' is the only parameter
                                        partition[identifier] = None

    def get_all_messages(self) -> MESSAGES_BY_TARGET:
        """
        Get copy of all MESSAGES_BY_TARGET as a Python data structure.
        :return: Dict (copy) of all validation messages in the ValidationReporter.
        """
        # TODO: is it necessary to copy these messages -
        #       may be a large data structure,
        #       costly to replicate (just for 'safety')
        return copy.deepcopy(self.messages)

    def get_messages_of_type(
            self,
            message_type: MessageType,
            test: Optional[str] = None,
            target: Optional[str] = None
    ) -> MESSAGE_PARTITION:
        """
        Get Python data dictionary of ValidationReporter messages of
        'message_type', for a specified (or default?) target and test.
        :param message_type: MessageType, type of message whose presence is to be detected.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: get copy of messages of type 'message_type'.
        """
        message_catalog: MESSAGE_CATALOG = self.get_messages_by_test(test=test, target=target)
        # TODO: the deepcopy may be desirable for message data
        #       integrity, but it may be computationally expensive?
        return copy.deepcopy(message_catalog[message_type.name])

    @staticmethod
    def merge_identified_messages(
        aggregated: IDENTIFIED_MESSAGES,
        additions: IDENTIFIED_MESSAGES
    ):
        identifier: str
        message_parameters_list: Optional[List[MESSAGE_PARAMETERS]]
        for identifier, message_parameters_list in additions.items():
            if identifier not in aggregated:
                aggregated[identifier] = None
            if message_parameters_list is not None:
                if aggregated[identifier] is None:
                    aggregated[identifier] = list()
                aggregated[identifier].extend(copy.deepcopy(message_parameters_list))

    def merge_coded_messages(
            self,
            aggregated: MESSAGE_PARTITION,
            additions: MESSAGE_PARTITION
    ):
        source: str
        identified_messages: Optional[IDENTIFIED_MESSAGES]
        for source, identified_messages in additions.items():
            if source not in aggregated:
                aggregated[source] = None
            if identified_messages is not None:
                if aggregated[source] is None:
                    aggregated[source] = dict()
                self.merge_identified_messages(aggregated[source], identified_messages)

    def get_all_messages_of_type(self, message_type: MessageType) -> MESSAGE_PARTITION:
        """
        Get the MESSAGE_PARTITION dictionary a given 'message_type',
        harvested from all target and test contexts.
        :param message_type: The MessageType whose presence is to be detected.
        :return: MESSAGE_PARTITION of the specified MessageType.
        """
        all_messages_of_type: MESSAGE_PARTITION = dict()
        target: str
        messages_by_target: MESSAGES_BY_TARGET = self.get_all_messages()
        test: str
        messages_by_test: MESSAGES_BY_TEST
        message_catalog: MESSAGE_CATALOG
        for target, messages_by_test in messages_by_target.items():
            for test in messages_by_test.keys():
                additional_messages: MESSAGE_PARTITION = \
                    self.get_messages_of_type(message_type=message_type, test=test, target=target)
                self.merge_coded_messages(all_messages_of_type, additional_messages)
        return all_messages_of_type

    def get_info(self, test: Optional[str] = None, target: Optional[str] = None) -> MESSAGE_PARTITION:
        """
        Get a copy of all recorded 'information' messages for a given test from a given target.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: Dict of all 'information' messages.
        """
        return self.get_messages_of_type(message_type=MessageType.info, test=test, target=target)

    def get_skipped(self, test: Optional[str] = None, target: Optional[str] = None) -> MESSAGE_PARTITION:
        """
        Get copy of all recorded 'skipped test' messages for a given test from a given target.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: Dict of all 'skipped test' messages.
        """
        return self.get_messages_of_type(message_type=MessageType.skipped, test=test, target=target)

    def get_warnings(self, test: Optional[str] = None, target: Optional[str] = None) -> MESSAGE_PARTITION:
        """
        Get copy of all recorded 'warning' messages for a given test from a given target.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: Dict of all 'warning' messages.
        """
        return self.get_messages_of_type(message_type=MessageType.warning, test=test, target=target)

    def get_errors(self, test: Optional[str] = None, target: Optional[str] = None) -> MESSAGE_PARTITION:
        """
        Get copy of all recorded 'error' messages, for a given test from a given target.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: Dict of all 'error' messages.
        """
        return self.get_messages_of_type(message_type=MessageType.error, test=test, target=target)

    def get_critical(self, test: Optional[str] = None, target: Optional[str] = None) -> MESSAGE_PARTITION:
        """
        Get copy of all recorded 'critical' error messages, for a given test from a given target.
        :param test: str, specified test (gets current 'default' test if not given)
        :param target: str, specified target (gets current 'default' test if not given)
        :return: Dict of all 'critical error' messages.
        """
        return self.get_messages_of_type(message_type=MessageType.critical, test=test, target=target)

    ############################
    # General Instance methods #
    ############################
    def merge(self, reporter):
        """
        Merge all messages and metadata from a second reporter
        into the calling ValidationReporter instance.

        :param reporter: second ValidationReporter
        """
        assert isinstance(reporter, ValidationReporter)

        # new coded messages also need to be merged!
        self.add_messages(reporter.get_all_messages())

    def to_dict(self) -> Dict:
        """
        Export ValidationReporter message contents as a Python dictionary.
        :return: Dict
        """
        return {"messages": self.get_all_messages()}

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
        """
        Check if the testcase has validation errors.

        :param tag: str, top level string key in the 'case' whose value is the validation messages 'dictionary'
        :param case: Dict, containing error messages in a structurally similar
                     format to what is returned by the to_dict() method in this class.
        :return: True if the case contains validation messages
        """
        # TODO: not sure if this method is adversely affected by the new release 4.* messages data structure
        # TODO: not sure if we should detect both 'errors' and 'critical' here or just 'critical'
        #
        # The 'case' dictionary object could have a format something like this:
        #
        #     tag: {
        #         ...
        #         "messages": {
        #             "information": [],
        #             "skipped tests": [],
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

    def report_header(self, title: Optional[str] = "", compact_format: bool = True) -> str:
        """
        Return a suitably generated report header.
        :param title: Optional[str], if the title is None, then only the 'reasoner-validator' version is printed out
                      in the header. If the title is an empty string (the default), then 'Validation Report' used.
        :param compact_format: bool, whether to print the header in compact format (default: True).
                               Extra line feeds are otherwise provided to provide space around header
                               and control characters are output to underline the header.
        :return: str, generated header.
        """
        header: str = ""
        if title is not None:

            if not compact_format:
                header += "\n"

            if not title:
                title = f"Validation Report"

            if not compact_format:
                header += f"\n\033[4m{title}\033[0m\n"
            else:
                # compact also ignores underlining
                header += f"{title}\n"

        if not compact_format:
            header += "\n"

        header += f"Reasoner Validator version '{metadata.version('reasoner-validator')}'"
        return header

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

        print(f"{self.report_header(title, compact_format)}.", file=file)
        if not compact_format:
            # extra blank line spacer
            print(file=file)

        if self.has_messages():

            # self.messages is now a MESSAGES_BY_TARGET
            # where MESSAGE_CATALOG is Dict[<message type>, MESSAGE_PARTITION]
            # <message type> is the top level partition of messages into
            # 'critical', 'error', 'warning', 'skipped' or 'info'
            target: str
            test: str
            message_type: str
            target_messages: MESSAGES_BY_TEST
            test_messages: MESSAGE_CATALOG
            coded_messages: MESSAGE_PARTITION
            for target, target_messages in self.messages.items():

                # TODO: clean up 'target' subheader here?
                if not compact_format:
                    print(f"\033[4mTarget: {target}\033[0m", file=file)
                    print(file=file)
                else:
                    # compact also ignores underlining
                    print(f"\nTarget: {target}", file=file)

                for test, test_messages in target_messages.items():

                    # TODO: clean up 'test' subheader here?
                    if not compact_format:
                        print(f"\t\033[4mTest: {test}\033[0m", file=file)
                        print(file=file)
                    else:
                        # compact also ignores underlining
                        print(f"\tTest: {test}", file=file)

                    for message_type, coded_messages in test_messages.items():

                        # if there are coded validation messages for given message type:
                        # ('critical', 'error', 'warning', 'skipped' or 'info')
                        if coded_messages:

                            # ... then iterate through them and print them out

                            if not compact_format:
                                print(f"\t\t\033[4m{message_type.capitalize()}\033[0m", file=file)
                                print(file=file)
                            else:
                                # compact also ignores underlining
                                print(f"\n\t\t{message_type.capitalize()}:", file=file)

                            # 'coded_messages' is a MESSAGE_PARTITION where
                            # MESSAGE_PARTITION is Dict[<validation code>, Optional[IDENTIFIED_MESSAGES]]

                            # 'validation code' is the dot-delimited string
                            # representation of the YAML path of the message codes.yaml
                            code: str
                            messages_by_code:  Optional[IDENTIFIED_MESSAGES]

                            # Grouping message outputs by validation codes
                            for code, messages_by_code in coded_messages.items():

                                code_label: str = CodeDictionary.validation_code_tag(code)
                                print(
                                    f"\t\t* {code_label}:\n"
                                    f"\t\t=> {CodeDictionary.get_message_template(code)}",
                                    file=file
                                )
                                if not compact_format:
                                    print(file=file)

                                # 'coded_messages' are Optional[IDENTIFIED_MESSAGES]
                                # An entry of 'coded_messages' may be None if the given message code
                                # has no additional parameters that distinguish instances of context
                                # (eg., edge id?) where the validation message occurs for the given identifier.
                                if messages_by_code is None:
                                    continue

                                # Otherwise, codes with associated parameters in scope
                                # 'IDENTIFIED_MESSAGES' are Dict[<identifier>, Optional[List[MESSAGE_PARAMETERS]]]
                                # where a unique 'identifier' serves as the discriminator
                                # of the (TRAPI or Biolink) context of the validation message

                                ids_per_row: int = 0
                                num_ids: int = len(messages_by_code.keys())
                                more_ids: int = num_ids - id_rows if num_ids > id_rows else 0
                                identifier: str
                                messages: Optional[List[MESSAGE_PARAMETERS]]
                                for identifier, messages in messages_by_code.items():
                                    if messages is None:
                                        # For codes whose context of validation is solely discerned
                                        # with their identifier, just print out the identifier
                                        print(f"\t\t\t\t# {identifier}", file=file)
                                        if not compact_format:
                                            print(file=file)
                                    else:
                                        # Since we have already checked if messages is None above,
                                        # then we assume here that 'messages' is a List[MESSAGE_PARAMETERS]
                                        # which records distinct additional context
                                        # for a list of messages associated with a given code.

                                        print(f"\t\t\t\t# {identifier}", file=file)
                                        first_message: bool = True
                                        messages_per_row: int = 0
                                        num_messages: int = len(messages)
                                        more_msgs: int = num_messages - msg_rows if num_messages > msg_rows else 0
                                        # 'messages' is an instance List[MESSAGE_PARAMETERS] where every entry of
                                        # 'MESSAGE_PARAMETERS' is a dictionary of additional parameters documenting
                                        # a specific instance of the validation message related to the given identifier,
                                        # where the keys are a validation code specific id (documented in codes.yaml)
                                        parameters: MESSAGE_PARAMETERS
                                        for parameters in messages:
                                            if first_message:
                                                tags = tuple(parameters.keys())
                                                print(f"\t\t\t\t- {' | '.join(tags)}: ", file=file)
                                                first_message = False
                                            # Sanitize the parameter values for the report
                                            # (in case non-string values sneak through)
                                            parameters = {tag: str(value) for tag, value in parameters.items()}
                                            print(f"\t\t\t\t\t{' | '.join(parameters.values())}", file=file)
                                            messages_per_row += 1
                                            if msg_rows and messages_per_row >= msg_rows:
                                                if more_msgs:
                                                    print(
                                                        f"\t\t\t\t{str(more_msgs)} more messages " +
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
                                                f"\t\t\t{str(more_ids)} more identifiers for code '{code_label}'...",
                                                file=file
                                            )
                                        break
                                if not compact_format:
                                    print(file=file)
                        # else: print nothing if a given message_type has no messages
                    # end for each coded message
                # end for each test
            # end for each target
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
        reporter, as a formatted human-readable text blob.

        :param id_rows: int >= 0, if set, maximum number of code-related identifiers to
                             print per code (value of 0 means print all; default: 0)
        :param msg_rows: int >= 0, if set, maximum number of parameterized code-related messages to
                                  print, per identifier row (value of 0 means print all; default: 0)
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
