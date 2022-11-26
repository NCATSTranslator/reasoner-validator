"""Testing Validation Report methods"""
from typing import Optional, Dict, Tuple, List
import pytest

from reasoner_validator.report import ValidationReporter
from reasoner_validator.validation_codes import CodeDictionary

TEST_TRAPI_VERSION = "1.3.0"
TEST_BIOLINK_VERSION = "2.4.8"


def check_messages(validator: ValidationReporter, code, no_errors: bool = False):
    messages: Dict[str, List[Dict]] = validator.get_messages()
    if code:
        # TODO: 'code' should be found in code.yaml
        # value: Optional[Tuple[str, str]] = CodeDictionary.get_code_subtree(code)
        # assert value is not None
        message_type = validator.get_message_type(code)
        if message_type == "error":
            assert any([error['code'] == code for error in messages['errors']])
        elif message_type == "warning":
            assert any([warning['code'] == code for warning in messages['warnings']])
        elif message_type == "info":
            assert any([info['code'] == code for info in messages['information']])
    else:
        if no_errors:
            # just don't want any hard errors; info and warnings are ok?
            assert not validator.has_errors(), f"Unexpected error messages seen {messages}"
        else:
            # no expected at all? Assert the absence of such messages?
            assert not validator.has_messages(), f"Unexpected messages seen {messages}"


def test_check_basic_get_code_subtree():
    assert CodeDictionary.get_code_subtree("") is None
    assert CodeDictionary.get_code_subtree("info") is not None
    assert CodeDictionary.get_code_subtree("warning") is not None
    assert CodeDictionary.get_code_subtree("error") is not None
    assert CodeDictionary.get_code_subtree("foo.bar") is None


def test_get_code_subtree_is_leaf():

    result = CodeDictionary.get_code_subtree("info.compliant", is_leaf=True)
    assert result is not None
    message_type, leaf = result
    assert leaf is not None
    assert isinstance(leaf, Dict)
    assert all([key in [CodeDictionary.MESSAGE, CodeDictionary.DESCRIPTION] for key in leaf])
    assert leaf[CodeDictionary.MESSAGE] == "Biolink Model-compliant TRAPI Message."
    assert leaf[CodeDictionary.DESCRIPTION].startswith("Specified TRAPI message completely satisfies")

    assert CodeDictionary.get_code_subtree("info.compliant", is_leaf=False) is None


def test_get_code_subtree_facet_message():

    result = CodeDictionary.get_code_subtree("info.compliant", facet="message", is_leaf=True)
    assert result is not None
    message_type, leaf = result
    assert leaf is not None
    assert isinstance(leaf, Dict)
    assert CodeDictionary.MESSAGE in leaf
    assert leaf[CodeDictionary.MESSAGE] == "Biolink Model-compliant TRAPI Message."
    assert CodeDictionary.DESCRIPTION not in leaf

    result = CodeDictionary.get_code_subtree("info.query_graph.node.category", facet="message")
    assert result is not None
    message_type, subtree = result
    assert subtree is not None
    assert isinstance(subtree, Dict)
    assert all([key in ["abstract", "mixin"] for key in subtree])
    assert CodeDictionary.MESSAGE in subtree["abstract"]
    assert subtree["abstract"][CodeDictionary.MESSAGE] == "'{name}' is abstract."
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

    result = CodeDictionary.get_code_subtree("info.query_graph.node.category", facet="description")
    assert result is not None
    message_type, subtree = result
    assert subtree is not None
    assert isinstance(subtree, Dict)
    assert all([key in ["abstract", "mixin"] for key in subtree])
    assert CodeDictionary.DESCRIPTION in subtree["mixin"]
    assert subtree["mixin"][CodeDictionary.DESCRIPTION] == \
           "TRAPI Message Query Graphs can have 'mixin' category classes."
    assert CodeDictionary.MESSAGE not in subtree["mixin"]


def test_get_code_subtree_internal_subtree():
    assert CodeDictionary.get_code_subtree("warning") is not None

    result = CodeDictionary.get_code_subtree("warning.knowledge_graph")
    assert result is not None
    message_type, subtree = result
    assert isinstance(subtree, Dict)
    assert message_type == "warning"
    assert subtree is not None
    assert all([key in ["node", "predicate", "edge"] for key in subtree])

    assert CodeDictionary.get_code_subtree("error") is not None
    assert CodeDictionary.get_code_subtree("foo.bar") is None


def test_get_entry():
    assert CodeDictionary.get_code_entry("") is None

    code_entry: Optional[Dict] = CodeDictionary.get_code_entry("info.compliant")
    assert code_entry is not None
    assert CodeDictionary.MESSAGE in code_entry
    assert code_entry[CodeDictionary.MESSAGE] == "Biolink Model-compliant TRAPI Message."

    # Higher level subtrees, not terminal leaf entries?
    assert CodeDictionary.get_code_entry("info") is None
    assert CodeDictionary.get_code_entry("info.query_graph") is None
    assert CodeDictionary.get_code_entry("info.query_graph.node") is None
    assert CodeDictionary.get_code_entry("warning") is None
    assert CodeDictionary.get_code_entry("error") is None

    # Unknown code?
    assert CodeDictionary.get_code_entry("foo.bar") is None


def test_get_message_template():
    assert CodeDictionary.get_message_template("") is None
    assert CodeDictionary.get_message_template("info.compliant") == "Biolink Model-compliant TRAPI Message."
    assert CodeDictionary.get_message_template("error.trapi.request.invalid") == \
           "{context} could not generate a valid TRAPI query request object because {reason}!"
    assert CodeDictionary.get_message_template("foo.bar") is None


def test_get_description():
    assert CodeDictionary.get_description("") is None
    assert CodeDictionary.get_description("info.compliant").\
        startswith("Specified TRAPI message completely satisfies")
    assert CodeDictionary.get_description("info.attribute_type_id.non_biolink_prefix").\
        startswith("Non-Biolink CURIEs are tolerated as term value")
    assert CodeDictionary.get_description("foo.bar") is None


def test_message_display():
    assert CodeDictionary.display(
        code="info.compliant"
    ) == "INFO - Biolink Model-compliant TRAPI Message."
    assert CodeDictionary.display(
        code="error.knowledge_graph.nodes.empty"
    ) == "ERROR - Knowledge Graph Nodes: No nodes found!"
    assert CodeDictionary.display(
        code="info.input_edge.node.category.abstract",
        name="NAME"
    ) == "INFO - Input Edge Node Category: 'NAME' is abstract."


def test_validator_reporter_message_display():
    reporter = ValidationReporter(prefix="Test Validation Report", trapi_version=TEST_TRAPI_VERSION)
    assert reporter.display(
        code="info.input_edge.node.category.abstract",
        name="NAME"
    ) == "Test Validation Report: INFO - Input Edge Node Category: 'NAME' is abstract."


def test_unknown_message_code():
    with pytest.raises(AssertionError):
        CodeDictionary.display(code="foo.bar")


def test_message_report():
    reporter = ValidationReporter(prefix="First Validation Report", trapi_version=TEST_TRAPI_VERSION)
    reporter.report(code="info.compliant")
    reporter.report(
        code="info.input_edge.predicate.abstract",
        name="NAME"
    )
    report: Dict[str, List[Dict]] = reporter.get_messages()
    assert 'information' in report
    assert len(report['information']) > 0
    messages: List[str] = [CodeDictionary.display(**coded_message) for coded_message in report['information']]
    assert "INFO - Biolink Model-compliant TRAPI Message." in messages
    assert "INFO - Input Edge Predicate: 'NAME' is abstract." in messages


def test_messages():
    # Loading and checking a first reporter
    reporter1 = ValidationReporter(prefix="First Validation Report", trapi_version=TEST_TRAPI_VERSION)
    assert reporter1.get_trapi_version() == TEST_TRAPI_VERSION
    assert reporter1.get_biolink_version() is None
    assert not reporter1.has_messages()
    reporter1.report("info.compliant")
    assert reporter1.has_messages()
    assert reporter1.has_information()
    assert not reporter1.has_warnings()
    assert not reporter1.has_errors()
    reporter1.report("warning.graph.empty")
    assert reporter1.has_warnings()
    reporter1.report("error.knowledge_graph.nodes.empty")
    assert reporter1.has_errors()

    # Testing merging of messages from a second reporter
    reporter2 = ValidationReporter(prefix="Second Validation Report", biolink_version=TEST_BIOLINK_VERSION)
    assert reporter2.get_trapi_version() == TEST_TRAPI_VERSION
    assert reporter2.get_biolink_version() == TEST_BIOLINK_VERSION
    reporter2.report("info.query_graph.edge.predicate.mixin", context="some_context", name="biolink:this_is_a_mixin")
    reporter2.report("warning.response.results.empty")
    reporter2.report("error.knowledge_graph.edges.empty")
    reporter1.merge(reporter2)
    assert reporter1.get_trapi_version() == TEST_TRAPI_VERSION
    assert reporter1.get_biolink_version() == TEST_BIOLINK_VERSION
    
    # No prefix...
    reporter3 = ValidationReporter()
    reporter3.report("error.trapi.response.query_graph.missing")
    reporter1.merge(reporter3)
    assert reporter1.get_trapi_version() == TEST_TRAPI_VERSION
    assert reporter1.get_biolink_version() == TEST_BIOLINK_VERSION

    # testing addition a few raw batch messages
    new_messages: Dict[str, List[Dict]] = {
            "information": [
                {
                    'code': "info.input_edge.predicate.abstract",
                    'context': "Well,... hello",
                    'name': "Dolly"
                }
            ],
            "warnings": [
                {
                    'code': "warning.knowledge_graph.node.unmapped_prefix",
                    'node_id': "Will Robinson",
                    'categories': "Lost in Space"
                }
            ],
            "errors": [
                {
                    'code': "error.trapi.validation",
                    'trapi_version': "6.6.6",
                    'exception': "Dave, this can only be due to human error!"
                }
            ]
    }
    reporter1.add_messages(new_messages)

    # Verify what we have
    messages: Dict[str, List[Dict]] = reporter1.get_messages()

    assert "information" in messages
    assert len(messages['information']) > 0
    information: List[str] = [CodeDictionary.display(**coded_message) for coded_message in messages['information']]
    assert "INFO - Input Edge Predicate: 'Dolly' is abstract." in information

    assert "warnings" in messages
    assert len(messages['warnings']) > 0
    warnings: List[str] = [CodeDictionary.display(**coded_message) for coded_message in messages['warnings']]
    assert "WARNING - Knowledge Graph Node Unmapped: 'Will Robinson' is unmapped " + \
           "to the target categories: Lost in Space?" in warnings

    assert "errors" in messages
    assert len(messages['errors']) > 0
    errors: List[str] = [CodeDictionary.display(**coded_message) for coded_message in messages['errors']]
    assert "ERROR - Trapi: TRAPI 6.6.6 Query: 'Dave, this can only be due to human error!'" in errors
    
    obj = reporter1.to_dict()
    assert obj["trapi_version"] == TEST_TRAPI_VERSION
    assert obj["biolink_version"] == TEST_BIOLINK_VERSION
    assert "messages" in obj
    assert "errors" in obj["messages"]
    assert "error.trapi.validation" in [entry['code'] for entry in obj["messages"]["errors"]]
    assert "Dave, this can only be due to human error!"\
           in [
               entry['exception'] for entry in obj["messages"]["errors"] if 'exception' in entry
           ]


def test_validator_method():

    reporter = ValidationReporter(
        prefix="Test Validator Method",
        trapi_version=TEST_TRAPI_VERSION,
        biolink_version=TEST_BIOLINK_VERSION
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
        validator.report("error.knowledge_graph.edge.provenance.infores.missing", infores="foo:bar")
        assert len(case) == 2
        assert case['some parameter'] == "some parameter value"
        assert case['another parameter'] == "some other parameter value"
        validator.report("warning.graph.empty", context="Fake")

    reporter.apply_validation(validator_method, test_data, **test_parameters)

    messages: Dict[str, List[Dict]] = reporter.get_messages()

    assert "warnings" in messages
    assert len(messages['warnings']) > 0
    warnings: List[str] = [CodeDictionary.display(**coded_message) for coded_message in messages['warnings']]
    assert "WARNING - Graph: Fake data is empty?" in warnings

    assert "errors" in messages
    assert len(messages['errors']) > 0
    errors: List[str] = [CodeDictionary.display(**coded_message) for coded_message in messages['errors']]
    assert "ERROR - Knowledge Graph Edge Provenance Infores: " + \
           "Edge has provenance value 'foo:bar' which is not a well-formed InfoRes CURIE!" in errors


# has_validation_errors(root_key: str = 'validation', case: Optional[Dict] = None)
@pytest.mark.parametrize(
    "query",
    [
        (
                'validation',
                {
                    "validation": {
                        "trapi_version": "1.3",
                        "biolink_version": "2.4.7",
                        "messages": {
                            "information": [],
                            "warnings": [],
                            "errors": [
                                ""
                            ]
                        }
                    }
                },
                True
        ),
        (
                "validation",
                {
                    "validation": {
                        "trapi_version": "1.3",
                        "biolink_version": "2.4.7",
                        "messages": {
                            "information": [],
                            "warnings": [
                                {
                                    'code': "warning.deprecated",
                                    'context': "Input",
                                    "name": "biolink:ChemicalSubstance"
                                },
                                {
                                    'code': "warning.predicate.non_canonical",
                                    'predicate': "biolink:participates_in"
                                }
                            ],
                            "errors": []
                        }
                    }
                },
                False
        ),
    ]
)
def test_has_validation_errors(query: Tuple):
    reporter = ValidationReporter()
    assert reporter.has_validation_errors(tag=query[0], case=query[1]) == query[2]
