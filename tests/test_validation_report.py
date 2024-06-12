"""Testing Validation Report methods"""
import copy
import sys
from typing import Optional, Dict, List
from sys import stderr

import pytest

from reasoner_validator.message import (
    MessageType,
    IDENTIFIED_MESSAGES,
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


def check_messages(
        validator: ValidationReporter,
        code: str,
        no_errors: bool = False,
        source_trail: Optional[str] = None
):
    # TODO: only assume 'default' test and target for now (fix later if problematic)
    messages: MESSAGES_BY_TARGET = validator.get_all_messages()
    if code:
        assert CodeDictionary.get_code_entry(code) is not None, f"check_messages() unknown code: '{code}'"
        message_type: MessageType = validator.get_message_type(code)
        coded_messages: MESSAGE_PARTITION = validator.get_messages_of_type(message_type)
        assert any([message_code == code for message_code in coded_messages.keys()])
        if source_trail:
            source_trail_tags = coded_messages[code].keys()
            assert source_trail in source_trail_tags
            if source_trail != "global":
                assert "global" not in source_trail_tags
    else:
        if no_errors:
            # just don't want any error (including 'critical'); 'info', 'skipped' and 'warning' are ok?
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
           "Input edge data can have 'mixin' predicates, when the mode of validation is 'non-strict'"
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


im_test_aggregated: IDENTIFIED_MESSAGES = {
    "Fe": None,
    "Fo": None,
    "Fum": [
        {
            "I": "smell",
            "the": "blood"
        }
    ]
}

im_test_additions: IDENTIFIED_MESSAGES = {
    "Fi": None,
    "Fum": [
        {
            "of": "an",
            "English": "man"
        }
    ]
}


# IDENTIFIED_MESSAGES = Dict[
#     str,  # key is the message-unique template 'identifier' value of parameterized messages
#
#     # Note: some message codes may not have any associated
#     # parameters beyond their discriminating identifier
#     Optional[List[MESSAGE_PARAMETERS]]
# ]
def test_merge_identified_messages():
    reporter = ValidationReporter()
    aggregated: IDENTIFIED_MESSAGES = copy.deepcopy(im_test_aggregated)
    additions: IDENTIFIED_MESSAGES = copy.deepcopy(im_test_additions)
    reporter.merge_identified_messages(
        aggregated=aggregated,
        additions=additions
    )
    assert "Fi" in aggregated.keys()
    assert any(
        [
            "man" in parameters.values()
            for parameters in aggregated["Fum"]
            if "Fum" in aggregated.keys() and aggregated["Fum"]
        ],
    )


im_another_test_addition: IDENTIFIED_MESSAGES = {
    "Humpty": None,
    "Dumpty": [
        {
            "On": "a",
            "big": "wall"
        }
    ]
}


im_yetanother_test_addition: IDENTIFIED_MESSAGES = {
    "Dumpty": [
        {
            "Had": "a",
            "big": "fall"
        }
    ]
}

scope_test_tag = "infores:tweedle_dee -> infores:tweedle_dum"
sm_test_aggregated: SCOPED_MESSAGES = {
    "global": im_test_aggregated,
    "infores:foo -> infores:bar": None,
    scope_test_tag: im_another_test_addition
}


sm_test_additions: SCOPED_MESSAGES = {
    "global": im_test_additions,
    scope_test_tag: im_yetanother_test_addition
}


def _check_coded_messages(
        coded_messages: SCOPED_MESSAGES,
        target_scope: str,
        target_identifier: str,
        target_parameter_values: List[str]
):
    assert coded_messages is not None and target_scope in coded_messages.keys()
    scoped_messages: Optional[IDENTIFIED_MESSAGES] = coded_messages[target_scope]
    assert all(
        [
            any([p in parameters.values() for p in target_parameter_values])
            for parameters in scoped_messages[target_identifier]
            if target_identifier in scoped_messages.keys() and scoped_messages[target_identifier]
        ]
    )


def _check_unfriendly_giant(coded_messages: SCOPED_MESSAGES):
    _check_coded_messages(
        coded_messages,
        target_scope="global",
        target_identifier="Fum",
        target_parameter_values=["blood", "man"]
    )


def _check_humpty_dumpty(coded_messages: SCOPED_MESSAGES):
    _check_coded_messages(
        coded_messages,
        target_scope=scope_test_tag,
        target_identifier="Dumpty",
        target_parameter_values=["wall", "fall"]
    )


# SCOPED_MESSAGES = Dict[
#     str,  # 'source trail' origin of affected edge or 'global' validation error
#
#     # (A given message code may have
#     # no IDENTIFIED_MESSAGES with discriminating identifier
#     #  and parameters hence, it may have a scoped value of 'None')
#     Optional[IDENTIFIED_MESSAGES]
# ]
def test_merge_scoped_messages():
    reporter = ValidationReporter()
    aggregated: SCOPED_MESSAGES = copy.deepcopy(sm_test_aggregated)
    additions: SCOPED_MESSAGES = copy.deepcopy(sm_test_additions)
    reporter.merge_scoped_messages(
        aggregated=aggregated,
        additions=additions
    )
    global_scoped_message: Optional[IDENTIFIED_MESSAGES] = aggregated["global"]
    assert global_scoped_message is not None and "Fi" in global_scoped_message.keys()

    # Now check for Humpty Dumpty message
    # in the 'aggregated' SCOPED_MESSAGES
    _check_humpty_dumpty(aggregated)


code_for_testing = "info.input_edge.predicate.abstract"
pm_test_aggregated: MESSAGE_PARTITION = {
    "info.excluded": {
        "global": {
            "Horace van der Gelder": None
        }
    },
    code_for_testing: {
        "global": im_test_aggregated,
        scope_test_tag: im_another_test_addition
    }
}

pm_test_additions: MESSAGE_PARTITION = {
    "info.excluded": {
        "global": {
            "Dolly Gallagher Levi": None
        }
    },
    "info.compliant": {
        "global": None
    },
    code_for_testing: {
        "global": im_test_additions,
        scope_test_tag: im_yetanother_test_addition
    }
}


# MESSAGE_PARTITION = Dict[
#     str,  # message 'code' as indexing key
#     SCOPED_MESSAGES
# ]
def test_merge_coded_messages():
    reporter = ValidationReporter()
    aggregated: MESSAGE_PARTITION = copy.deepcopy(pm_test_aggregated)
    additions: MESSAGE_PARTITION = copy.deepcopy(pm_test_additions)
    reporter.merge_coded_messages(
        aggregated=aggregated,
        additions=additions
    )
    assert "info.compliant" in aggregated.keys()


##########################
# Full message test data #
##########################
full_test_messages_catalog_1: MESSAGE_CATALOG = {
    "info": {
        "info.excluded": {
            "global": {
                "Dolly Gallagher Levi": None
            }
        },
        "info.compliant": {
            "global": None
        },
        code_for_testing: {
            "global": copy.deepcopy(im_test_aggregated)
        }
    },
    "skipped": {
        "skipped.test": {
            "global": {
                "Catastrophe": [
                    {
                        "context": "Family Robinson",
                        "reason": "Lost in Space"
                    }
                ]
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
    }
}

full_test_messages_catalog_2: MESSAGE_CATALOG = {
    "info": {
        "info.excluded": {
            "global": {
                "Horace van der Gelder": None
            }
        },
        code_for_testing: {
            "global": copy.deepcopy(im_test_additions),
            scope_test_tag: copy.deepcopy(im_another_test_addition)
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


full_test_messages_catalog_3: MESSAGE_CATALOG = {
    "info": {
        code_for_testing: {
            scope_test_tag: copy.deepcopy(im_yetanother_test_addition)
        }
    }
}

critical_test = "new_test_2"
full_test_messages_by_test_1: MESSAGES_BY_TEST = {
    "new_test_1": copy.deepcopy(full_test_messages_catalog_1),
    critical_test: copy.deepcopy(full_test_messages_catalog_2)
}

full_test_messages_by_test_2: MESSAGES_BY_TEST = {
    "new_test_3": copy.deepcopy(full_test_messages_catalog_3)
}

critical_target = "new_target_1"
full_test_messages_by_target: MESSAGES_BY_TARGET = {
    critical_target: copy.deepcopy(full_test_messages_by_test_1),
    "new_target_2": copy.deepcopy(full_test_messages_by_test_2)
}


def test_get_all_messages_of_type():
    reporter = ValidationReporter()
    # Load the reporter with several messages
    # across multiple test and target contexts
    reporter.add_messages(new_messages=full_test_messages_by_target)
    messages: MESSAGE_PARTITION = reporter.get_all_messages_of_type(MessageType.info)
    print(messages, file=sys.stderr, flush=True)
    assert all([code in ["info.excluded", "info.compliant", code_for_testing] for code in messages])
    info_excluded_scoped_messages: SCOPED_MESSAGES = messages["info.excluded"]
    assert "global" in info_excluded_scoped_messages and info_excluded_scoped_messages["global"] is not None
    assert all(
        [
            identifier in ["Dolly Gallagher Levi", "Horace van der Gelder"]
            for identifier in info_excluded_scoped_messages["global"].keys()
        ]
    )
    info_compliant_messages: SCOPED_MESSAGES = messages["info.compliant"]
    assert "global" in info_compliant_messages and info_compliant_messages["global"] is None

    # In the SCOPED_MESSAGES associated with 'code_for_testing',
    # Check for Jack in the Beanstalk Giant messages...
    _check_unfriendly_giant(messages[code_for_testing])
    # ...then, for Humpty Dumpty messages...
    _check_humpty_dumpty(messages[code_for_testing])


def test_prefix_accessors():
    reporter = ValidationReporter()
    assert reporter.report_header().startswith("Validation Report\n")
    assert reporter.get_default_target() == "Target"
    reporter.reset_default_target("test_prefix_accessors")
    assert reporter.get_default_target() == "test_prefix_accessors"


def test_get_message_type():
    reporter = ValidationReporter()
    assert reporter.get_message_type("info.compliant") == MessageType.info
    assert reporter.get_message_type("skipped.test") == MessageType.skipped
    assert reporter.get_message_type("warning.graph.empty") == MessageType.warning
    assert reporter.get_message_type("error.trapi.response.empty") == MessageType.error
    assert reporter.get_message_type("critical.trapi.validation") == MessageType.critical
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
    messages_by_code: MESSAGE_PARTITION = reporter1.get_messages_of_type(MessageType.info)
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
        source_trail="infores:monarch"
    )
    reporter2.report(
        code="error.knowledge_graph.edge.predicate.abstract",
        identifier="biolink:contributor",
        edge_id="Tim->biolink:contributor->Translator",
        source_trail="infores:monarch"
    )
    messages_by_code: MESSAGE_PARTITION = reporter2.get_messages_of_type(MessageType.error)
    assert len(messages_by_code) > 0
    assert "error.knowledge_graph.edge.predicate.abstract" in messages_by_code
    assert "infores:monarch" in messages_by_code['error.knowledge_graph.edge.predicate.abstract']
    assert "global" not in messages_by_code['error.knowledge_graph.edge.predicate.abstract']


def _validate_full_messages(
        reporter: ValidationReporter,
        message_type: MessageType,
        full_message: str
) -> None:
    # DRY helper function for validating fully annotated messages
    messages_by_code: MESSAGE_PARTITION = reporter.get_all_messages_of_type(message_type)
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
    reporter2.report("warning.trapi.response.message.results.empty")
    reporter2.report("error.knowledge_graph.edges.empty")
    reporter1.merge(reporter2)

    # No prefix...
    reporter3 = ValidationReporter()
    reporter3.report("error.trapi.response.message.query_graph.missing")
    reporter1.merge(reporter3)

    # testing addition a few raw batch messages
    reporter1.add_messages(full_test_messages_by_target)

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
            "SKIPPED - Test: Test case skipped for a test asset, for a specified reason"
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
    assert critical_target in obj["messages"]
    assert critical_test in obj["messages"][critical_target]
    assert "critical" in obj["messages"][critical_target][critical_test]
    assert "critical.trapi.validation" in obj["messages"][critical_target][critical_test]["critical"]

    messages_by_target: SCOPED_MESSAGES = \
        obj["messages"][critical_target][critical_test]["critical"]["critical.trapi.validation"]
    assert messages_by_target, "Empty 'critical.trapi.validation' messages set?"
    assert "9.1.1" in messages_by_target["global"]
    message_subset: List = messages_by_target["global"]["9.1.1"]
    assert "Fire, Ambulance or Police?" \
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
