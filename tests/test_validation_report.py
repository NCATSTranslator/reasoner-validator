"""Testing Validation Report methods"""
from mailbox import Message
from typing import Optional, Dict, Tuple, List
from sys import stderr

import pytest

from reasoner_validator.message import (
    MessageType,
    SCOPED_MESSAGES,
    MESSAGE_PARTITION,
    MESSAGE_CATALOG,
    MESSAGES_BY_TEST,
    MESSAGES_BY_TARGET
)
from reasoner_validator.report import ValidationReporter, TRAPIGraphType
from reasoner_validator.validation_codes import CodeDictionary
from reasoner_validator.versioning import get_latest_version

TEST_TRAPI_VERSION = get_latest_version(ValidationReporter.DEFAULT_TRAPI_VERSION)
TEST_BIOLINK_VERSION = "2.4.8"


def check_messages(
        validator: ValidationReporter,
        code: str,
        no_errors: bool = False,
        source_trail: Optional[str] = None
):
    messages: MESSAGE_CATALOG = validator.get_all_messages()
    if code:
        # print("code is:", code)
        # print("message_type", message_type)
        # TODO: 'code' should be found in code.yaml
        # value: Optional[Tuple[str, str]] = CodeDictionary.get_code_subtree(code)
        # assert value is not None
        message_type = validator.get_message_type(code)
        if message_type == "critical":
            assert any([critical_code == code for critical_code in messages['critical']])
        elif message_type == "error":
            assert any([error_code == code for error_code in messages['errors']])
        elif message_type == "warning":
            assert any([warning_code == code for warning_code in messages['warnings']])
        elif message_type == "skipped":
            assert any([skipped_code == code for skipped_code in messages['skipped tests']])
        elif message_type == "info":
            assert any([info_code == code for info_code in messages['information']])
        if source_trail:
            mtt: str = validator.get_message_type_label(message_type)
            source_trail_tags = messages[mtt][code].keys()
            assert source_trail in source_trail_tags
            if source_trail != "global":
                assert "global" not in source_trail_tags
    else:
        if no_errors:
            # just don't want any 'critical' (errors) nor 'errors'; 'information' and 'warnings' are ok?
            assert not validator.has_critical(), f"Unexpected critical error messages seen {messages}"
            assert not validator.has_errors(), f"Unexpected error messages seen {messages}"
        else:
            # no expected at all? Assert the absence of such messages?
            assert not validator.has_messages(), f"Unexpected messages seen {messages}"


def test_graph_type_label():
    assert TRAPIGraphType.Input_Edge.label() == "input_edge"
    assert TRAPIGraphType.Query_Graph.label() == "query_graph"
    assert TRAPIGraphType.Knowledge_Graph.label() == "knowledge_graph"


def test_check_basic_get_code_subtree():
    assert CodeDictionary.get_code_subtree("") is None
    assert CodeDictionary.get_code_subtree("info") is not None
    assert CodeDictionary.get_code_subtree("skipped") is not None
    assert CodeDictionary.get_code_subtree("warning") is not None
    assert CodeDictionary.get_code_subtree("error") is not None
    assert CodeDictionary.get_code_subtree("critical") is not None
    assert CodeDictionary.get_code_subtree("foo.bar") is None


def test_get_code_subtree_is_leaf():

    result = CodeDictionary.get_code_subtree("info.compliant", is_leaf=True)
    assert result is not None
    message_type, leaf = result
    assert leaf is not None
    assert isinstance(leaf, Dict)
    assert all([key in [CodeDictionary.MESSAGE, CodeDictionary.DESCRIPTION] for key in leaf])
    assert leaf[CodeDictionary.MESSAGE] == "Biolink Model-compliant TRAPI Message"
    assert leaf[CodeDictionary.DESCRIPTION].startswith("Specified TRAPI message completely satisfies")

    assert CodeDictionary.get_code_subtree("info.compliant", is_leaf=False) is None


def test_get_code_subtree_facet_message():

    result = CodeDictionary.get_code_subtree("info.compliant", facet="message", is_leaf=True)
    assert result is not None
    message_type, leaf = result
    assert leaf is not None
    assert isinstance(leaf, Dict)
    assert CodeDictionary.MESSAGE in leaf
    assert leaf[CodeDictionary.MESSAGE] == "Biolink Model-compliant TRAPI Message"
    assert CodeDictionary.DESCRIPTION not in leaf

    result = CodeDictionary.get_code_subtree("info.input_edge.predicate", facet="message")
    assert result is not None
    message_type, subtree = result
    assert subtree is not None
    assert isinstance(subtree, Dict)
    assert all([key in ["abstract", "mixin"] for key in subtree])
    assert CodeDictionary.MESSAGE in subtree["abstract"]
    assert subtree["abstract"][CodeDictionary.MESSAGE] == "Edge has an 'abstract' predicate"
    assert CodeDictionary.DESCRIPTION not in subtree["abstract"]


def test_get_code_subtree_facet_description():

    result = CodeDictionary.get_code_subtree("info.compliant", facet="description", is_leaf=True)
    assert result is not None
    message_type, leaf = result
    assert leaf is not None
    assert isinstance(leaf, Dict)
    assert CodeDictionary.DESCRIPTION in leaf
    assert leaf[CodeDictionary.DESCRIPTION].startswith("Specified TRAPI message completely satisfies")
    assert CodeDictionary.MESSAGE not in leaf

    result = CodeDictionary.get_code_subtree("info.input_edge.predicate", facet="description")
    assert result is not None
    message_type, subtree = result
    assert subtree is not None
    assert isinstance(subtree, Dict)
    assert all([key in ["abstract", "mixin"] for key in subtree])
    assert CodeDictionary.DESCRIPTION in subtree["mixin"]
    assert subtree["mixin"][CodeDictionary.DESCRIPTION] == \
           "Input edge data can have 'mixin' predicates, when the mode of validation is 'non-strict'."
    assert CodeDictionary.MESSAGE not in subtree["mixin"]


def test_get_code_subtree_internal_subtree():
    assert CodeDictionary.get_code_subtree("warning") is not None

    result = CodeDictionary.get_code_subtree("warning.knowledge_graph")
    assert result is not None
    message_type, subtree = result
    assert isinstance(subtree, Dict)
    assert message_type == "warning"
    assert subtree is not None
    assert all([key in ["nodes", "node", "predicate", "edge"] for key in subtree])


def test_get_entry():
    assert CodeDictionary.get_code_entry("") is None

    code_entry: Optional[Dict] = CodeDictionary.get_code_entry("info.compliant")
    assert code_entry is not None
    assert CodeDictionary.MESSAGE in code_entry
    assert code_entry[CodeDictionary.MESSAGE] == "Biolink Model-compliant TRAPI Message"

    # Higher level subtrees, not terminal leaf entries?
    assert CodeDictionary.get_code_entry("info") is None
    assert CodeDictionary.get_code_entry("skipped") is None
    assert CodeDictionary.get_code_entry("info.query_graph") is None
    assert CodeDictionary.get_code_entry("info.query_graph.node") is None
    assert CodeDictionary.get_code_entry("warning") is None
    assert CodeDictionary.get_code_entry("error") is None
    assert CodeDictionary.get_code_entry("critical") is None

    # Unknown code?
    assert CodeDictionary.get_code_entry("foo.bar") is None


def test_get_message_template():
    assert CodeDictionary.get_message_template("") is None
    assert CodeDictionary.get_message_template("info.compliant") == "Biolink Model-compliant TRAPI Message"
    assert CodeDictionary.get_message_template("critical.trapi.request.invalid") == \
           "Test could not generate a valid TRAPI query request object using identified element"
    assert CodeDictionary.get_message_template("foo.bar") is None


def test_get_description():
    assert CodeDictionary.get_description("") is None
    info_compliant = CodeDictionary.get_description("info.compliant")
    assert info_compliant is not None
    assert info_compliant.startswith("Specified TRAPI message completely satisfies")
    info_attribute = CodeDictionary.get_description("warning.knowledge_graph.edge.attribute.type_id.non_biolink_prefix")
    assert info_attribute is not None
    assert info_attribute.startswith("Non-Biolink CURIEs are tolerated")
    assert CodeDictionary.get_description("foo.bar") is None


def test_message_display():
    scoped_messages = CodeDictionary.display(code="info.compliant", add_prefix=True)
    assert "INFO - Compliant: Biolink Model-compliant TRAPI Message" in scoped_messages["global"]

    scoped_messages = CodeDictionary.display("error.knowledge_graph.nodes.empty", add_prefix=True)
    assert "ERROR - Knowledge Graph Nodes: No nodes found" in scoped_messages["global"]

    scoped_messages = CodeDictionary.display(
        code="info.excluded",

        # this code has "global" scope plus
        # an "identifier" context, but no other parameters
        messages={
            "global": {"a->biolink:related_to->b": None}
        },
        add_prefix=True
    )
    assert "INFO - Excluded: All test case S-P-O triples from " + \
           "resource test location, or specific user excluded S-P-O triples" in scoped_messages["global"]

    scoped_messages = CodeDictionary.display(
        code="info.input_edge.predicate.abstract",

        # this code has "global" scope, an "identifier" context
        # plus one other parameter named 'edge_id'
        messages={
            "infores:chebi->infores:molepro->infores:arax": {
                "biolink:contributor": [
                    {
                        "edge_id": "a->biolink:related_to->b"
                    }
                ]
            }
        },
        add_prefix=True
    )
    assert "INFO - Input Edge Predicate: Edge has an 'abstract' predicate" \
           in scoped_messages["infores:chebi->infores:molepro->infores:arax"]


def test_unknown_message_code():
    with pytest.raises(AssertionError):
        CodeDictionary.display(code="foo.bar")


def test_prefix_accessors():
    reporter = ValidationReporter()
    assert reporter.report_header().startswith("Validation Report for 'Target'\n")
    assert reporter.get_default_target() == "Target"
    reporter.reset_default_target("test_prefix_accessors")
    assert reporter.get_default_target() == "test_prefix_accessors"
    assert reporter.report_header().startswith("Validation Report for 'test_prefix_accessors'\n")


def test_get_message_type():
    reporter = ValidationReporter()
    assert reporter.get_message_type("info.compliant") == "info"
    assert reporter.get_message_type("skipped.test") == "skipped"
    assert reporter.get_message_type("warning.graph.empty") == "warning"
    assert reporter.get_message_type("error.trapi.response.empty") == "error"
    assert reporter.get_message_type("critical.trapi.validation") == "critical"
    with pytest.raises(NotImplementedError):
        # unknown message type
        reporter.get_message_type(code="foo.bar")


def test_global_sourced_validation_message_report():
    reporter1 = ValidationReporter(
        default_test="test_global_sourced_validation_message_report",
        default_target="First Validation Report"
    )
    reporter1.report(code="info.compliant")
    reporter1.report(
        code="info.input_edge.predicate.abstract",
        identifier="biolink:contributor",
        edge_id="a->biolink:contributor->b"
    )
    messages_by_code: MESSAGE_PARTITION = reporter1.get_messages_type(MessageType.info)
    assert len(messages_by_code) > 0

    displayed: List[str] = list()
    for code, messages in messages_by_code.items():
        scoped_messages = CodeDictionary.display(code, messages, add_prefix=True)
        displayed.extend(scoped_messages["global"])
    assert "INFO - Compliant: Biolink Model-compliant TRAPI Message" in displayed
    assert "INFO - Input Edge Predicate: Edge has an 'abstract' predicate" in displayed


def test_source_trail_scoped_validation_message_report():
    reporter2 = ValidationReporter(
        default_test="test_source_trail_scoped_validation_message_report",
        default_target="Second Validation Report"
    )
    reporter2.report(
        code="error.knowledge_graph.edge.predicate.abstract",
        identifier="biolink:contributor",
        edge_id="Richard->biolink:contributor->Translator",
        source_trail="infores:sri"
    )
    reporter2.report(
        code="error.knowledge_graph.edge.predicate.abstract",
        identifier="biolink:contributor",
        edge_id="Tim->biolink:contributor->Translator",
        source_trail="infores:sri"
    )
    messages_by_code: MESSAGE_PARTITION = reporter2.get_messages_type(MessageType.error)
    assert len(messages_by_code) > 0
    assert "error.knowledge_graph.edge.predicate.abstract" in messages_by_code
    assert "infores:sri" in messages_by_code['error.knowledge_graph.edge.predicate.abstract']
    assert "global" not in messages_by_code['error.knowledge_graph.edge.predicate.abstract']


def _validate_full_messages(
        reporter: ValidationReporter,
        message_type: MessageType,
        full_message: str
) -> None:
    # DRY helper function for validating fully annotated messages
    messages_by_code: MESSAGE_PARTITION = reporter.get_messages_type(message_type)
    assert len(messages_by_code) > 0
    full_messages_list: List[str] = list()
    for code, messages in messages_by_code.items():
        scoped_messages: Dict = CodeDictionary.display(code, messages, add_prefix=True)
        scope, value = scoped_messages.popitem()
        full_messages_list.append(value[0])
    assert full_message in full_messages_list


def test_messages():
    # Loading and checking a first reporter
    tm_default_test = "test_messages"
    tm_default_target = "1st Test Message Set"
    reporter1 = ValidationReporter(
        default_test=tm_default_test,
        default_target=tm_default_target
    )
    assert not reporter1.has_messages()
    reporter1.report("info.compliant")
    assert reporter1.has_messages()
    assert reporter1.has_information()
    assert not reporter1.has_warnings()
    assert not reporter1.has_skipped()
    assert not reporter1.has_errors()
    assert not reporter1.has_critical()

    reporter1.report("warning.graph.empty", identifier="Reporter1 Unit Test")
    assert reporter1.has_warnings()
    reporter1.report("error.knowledge_graph.nodes.empty")
    assert reporter1.has_errors()

    # Testing merging of messages from a second reporter
    reporter2 = ValidationReporter(
        default_test="test_messages",
        default_target="2nd Test Message Set"
    )
    reporter2.report(
        code="info.query_graph.edge.predicate.mixin",
        identifier="biolink:this_is_a_mixin",
        edge_id="a-biolink:this_is_a_mixin->b"
    )
    reporter2.report("warning.trapi.response.results.empty")
    reporter2.report("error.knowledge_graph.edges.empty")
    reporter1.merge(reporter2)

    # No prefix...
    reporter3 = ValidationReporter()
    reporter3.report("error.trapi.response.query_graph.missing")
    reporter1.merge(reporter3)

    # testing addition a few raw batch messages
    new_messages_catalog: MESSAGE_CATALOG = {
        "info": {
            "info.excluded": {
                "global": {
                    "Horace van der Gelder": None
                }
            }
        },
        "skipped": {
            "skipped.test": {
                "global": {
                    "Catastrophe": None
                }
            }

        },
        "warning": {
            "warning.knowledge_graph.node.id.unmapped_prefix": {
                "infores:earth -> infores:spaceship": {
                    "Will Robinson": [
                        {
                            "categories": "Lost in Space"
                        }
                    ]
                }
            }
        },
        "error": {
            "error.biolink.model.noncompliance": {
                "global": {
                    "6.6.6": [
                        {
                            'reason': "Dave, this can only be due to human error..."
                        }
                    ]
                }
            }
        },
        "critical": {
            "critical.trapi.validation": {
                "global": {
                    "9.1.1": [
                        {
                            'component': 'Query',
                            'reason': "Fire, Ambulance or Police?"
                        }
                    ]
                }
            }
        }
    }
    new_test_messages: MESSAGES_BY_TEST = {
        "new_test": new_messages_catalog
    }
    new_targeted_test_messages: MESSAGES_BY_TARGET = {
        "new_target": new_test_messages
    }
    reporter1.add_messages(new_targeted_test_messages)

    # Verify what we have
    test_message_type: MessageType
    full_message: str
    for test_message_type, full_message in (
        (
            MessageType.info,
            "INFO - Excluded: All test case S-P-O triples from resource test location, " +
            "or specific user excluded S-P-O triples"
        ),
        (
            MessageType.skipped,
            "SKIPPED - Test: For reason indicated in the identifier."
        ),
        (
            MessageType.warning,
            "WARNING - Knowledge Graph Node Id Unmapped: Node identifier found unmapped to target categories for node"
        ),
        (
            MessageType.error,
            "ERROR - Biolink Model: S-P-O statement is not compliant to Biolink Model release"
        ),
        (
            MessageType.critical,
            "CRITICAL - Trapi: Schema validation error"
        ),
    ):
        _validate_full_messages(reporter1, test_message_type, full_message)

    obj = reporter1.to_dict()
    assert "messages" in obj
    assert tm_default_target in obj["messages"]
    assert tm_default_test in obj["messages"][tm_default_target]
    assert "critical" in obj["messages"][tm_default_target][tm_default_test]
    assert "critical.trapi.validation" in obj["messages"][tm_default_target][tm_default_test]["critical"]

    messages_by_target: SCOPED_MESSAGES = \
        obj["messages"][tm_default_target][tm_default_test]["critical"]["critical.trapi.validation"]
    assert messages_by_target, "Empty 'critical.trapi.validation' messages set?"
    assert "9.1.1" in messages_by_target["global"]
    message_subset: List = messages_by_target["global"]["9.1.1"]
    assert "Fire, Ambulance or Police?"\
           in [message['reason'] for message in message_subset if 'reason' in message]

    for n in range(0, 10):
        reporter1.report(code="error.input_edge.node.category.missing", identifier=f"biolink:not_a_category_{n}")

    for c in range(0, 5):
        for n in range(0, 10):
            reporter1.report(
                code="error.input_edge.node.category.unknown",
                identifier=f"biolink:not_a_category_{c}",
                node_id=f"n{n}"
            )

    # Informal test of a text 'dump' of all the messages as a
    # text blob, using the 'display_all' method to format them
    print(
        "\n\nThis is an indirect 'test' of the ValidationReporter.dump() method\n"
        "which simply executes the function and look at the results here on the console:",
        file=stderr
    )
    reporter1.dump(file=stderr)

    print(
        f"\n{'-'*80}\n" +
        "ValidatorReporter.dump() with title suppressed using 'title=None'\n" +
        "and compressed using 'id_rows=2', 'msg_rows=3', 'compress=True':\n",
        file=stderr
    )
    reporter1.dump(title=None, id_rows=2, msg_rows=3, compact_format=True, file=stderr)

    print(
        f"\n{'-'*80}\n" +
        "ValidatorReporter.dump() resetting the title to a user string\n" +
        "and compressed using 'id_rows=1', 'msg_rows=1', 'compress=True':\n",
        file=stderr
    )
    reporter1.dump(title="My KP Validation Report", id_rows=1, msg_rows=1, compact_format=True, file=stderr)

    validation_report: str = reporter1.dumps(id_rows=2, msg_rows=3)
    assert validation_report.startswith("Reasoner Validator")


def test_validator_method():

    reporter = ValidationReporter(
        default_test="test_validator_method",
        default_target="Test Validator Method"
    )

    test_data: Dict = {
        "some key": "some value"
    }
    test_parameters: Dict = {
        "some parameter": "some parameter value",
        "another parameter": "some other parameter value"
    }

    def validator_method(validator: ValidationReporter, arg, **case):
        assert isinstance(arg, Dict)
        assert arg['some key'] == "some value"
        validator.report(
            "error.knowledge_graph.edge.provenance.infores.missing",
            identifier="fake-edge-id",
            infores="foo:bar"
        )
        assert len(case) == 2
        assert case['some parameter'] == "some parameter value"
        assert case['another parameter'] == "some other parameter value"
        validator.report("warning.graph.empty", identifier="Fake")

    reporter.apply_validation(validator_method, test_data, **test_parameters)

    test_message_type: MessageType
    full_message: str
    for test_message_type, full_message in (
        (
            MessageType.warning,
            "WARNING - Graph: Empty graph"
        ),
        (
            MessageType.error,
            "ERROR - Knowledge Graph Edge Provenance Infores: " +
            "Edge has provenance value which is not a well-formed InfoRes CURIE"
        )
    ):
        _validate_full_messages(reporter, test_message_type, full_message)


@pytest.mark.parametrize(
    "tag,case,result",
    [
        (
            'validation',
            {
                "validation": {
                    "messages": {
                        "information": {},
                        "skipped tests": {},
                        "warnings": {},
                        "errors": {},
                        "critical": {""}
                    }
                }
            },
            True
        ),
        (
            'validation',
            {
                "validation": {
                    "messages": {
                        "information": {},
                        "skipped tests": {},
                        "warnings": {},
                        "errors": {""},
                        "critical": {}
                    }
                }
            },
            True
        ),
        (
            "validation",
            {
                "validation": {
                    "messages": {
                        "information": {},
                        "skipped tests": {},
                        "warnings": {
                            "warning.input_edge.node.category.deprecated": [
                                {
                                    "identifier": "biolink:ChemicalSubstance"
                                }
                            ],
                            "warning.knowledge_graph.edge.predicate.non_canonical": [
                                {
                                    "identifier": "ABC1--biolink:participates_in->Glycolysis",
                                    "predicate": "biolink:participates_in"
                                }
                            ]
                        },
                        "errors": {},
                        "critical": {}
                    }
                }
            },
            False
        ),
    ]
)
def test_has_validation_errors(tag: str, case: Dict, result: bool):
    reporter = ValidationReporter()
    assert reporter.test_case_has_validation_errors(tag=tag, case=case) == result
