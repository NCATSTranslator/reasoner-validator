"""Test validation."""
import pytest

from jsonschema.exceptions import ValidationError

from reasoner_validator import validate
from reasoner_validator.util import latest

TEST_VERSIONS = "1", "1.2", "1.2.0", "1.3", "1.3.0"


@pytest.mark.parametrize("query", TEST_VERSIONS)
def test_query_and_version_completion(query):
    """Test validate()."""
    validate({
        "message": {},
    }, "Query", query)
    with pytest.raises(ValidationError):
        validate({
            "foo": {},
            "bar": {},
        }, "Query", query)


@pytest.mark.parametrize("query", TEST_VERSIONS)
def test_edgebinding(query):
    """Test validate_EdgeBinding()."""
    validate({
        "id": "hello",
    }, "EdgeBinding", query)
    with pytest.raises(ValidationError):
        validate({
            "foo": {},
        }, "EdgeBinding", query)


@pytest.mark.parametrize("query", TEST_VERSIONS)
def test_nullable(query):
    """Test nullable categories property."""
    qnode = {
        "categories": None
    }
    validate(qnode, "QNode", query)
    # I cannot really trigger anything using 'with pytest.raises(ValidationError)'
    # since QNode has 'additionalProperties: true' but no 'required:' properties


@pytest.mark.parametrize("query", TEST_VERSIONS)
def test_nullable_message_properties(query):
    """Test nullable message properties."""
    message = {
        "knowledge_graph": None,
        "query_graph": None,
        "results": None,
    }
    validate(message, "Message", query)
    with pytest.raises(ValidationError):
        validate({
            "foo": {},  # additionalProperties: false and 'foo' is not a documented property...
        }, "Message", query)


@pytest.mark.parametrize("query", TEST_VERSIONS)
def test_nullable_query_level_properties(query):
    """Test nullable TRAPI Query level properties."""
    trapi_query = {
        "message": {
            "knowledge_graph": None,
            "query_graph": None,
            "results": None,
        },
        "log_level": None,
        "workflow": None
    }
    validate(trapi_query, "Query", query)
    with pytest.raises(ValidationError):
        validate({
            "foo": {},  # missing required: message
        }, "Query", query)


@pytest.mark.parametrize("query", TEST_VERSIONS)
def test_nullable_async_query_level_properties(query):
    """Test nullable TRAPI Query level properties."""
    async_trapi_query = {
        "callback": "http://mykp.ncats.io/callback",
        "message": {
            "knowledge_graph": None,
            "query_graph": None,
            "results": None,
        },
        "log_level": None,
        "workflow": None
    }
    validate(async_trapi_query, "AsyncQuery", query)
    with pytest.raises(ValidationError):
        validate({
            "foo": {},  # missing required: callback, message
        }, "AsyncQuery", query)


@pytest.mark.parametrize("query", TEST_VERSIONS)
def test_nullable_response_properties(query):
    """Test nullable TRAPI Query level properties."""
    async_trapi_query = {
        "message": {
            "knowledge_graph": None,
            "query_graph": None,
            "results": None,
        },
        "workflow": None
    }
    validate(async_trapi_query, "Response", query)
    with pytest.raises(ValidationError):
        validate({
            "foo": {},  # missing required: message
        }, "Response", query)


# TODO: this test may not pass until TRAPI 1.3 query_id spec is fixed?
@pytest.mark.parametrize("query", TEST_VERSIONS)
def test_message_results_component_validation(query):
    """Test Message.Results component in validate()."""
    sample_message_result = {
        "edge_bindings": {
            "ab": [
                {
                    "attributes": None,
                    "id": "uuid:7884e454-d09c-11ec-b00f-0242ac110002"
                }
            ]
        },
        "node_bindings": {
            "a": [
                {
                    "attributes": None,
                    "id": "SGD:S000000065",
                    "qnode_id": "SGD:S000000065",
                    "query_id": None
                }
            ],
            "b": [
                {
                    "attributes": None,
                    "id": "GO:1905776",
                    "query_id": None
                }
            ]
        },
        "score": None
    }
    validate(sample_message_result, "Result", query)
    with pytest.raises(ValidationError):
        validate({
            # missing required: node_bindings, edge_bindings
            "foo": {},
            "bar": {},
        }, "Result", query)


# TODO: this test may not pass until TRAPI 1.3 query_id spec is fixed?
@pytest.mark.parametrize("query", TEST_VERSIONS)
def test_message_node_binding_component_validation(query):
    """Test NodeBinding component in validate()."""
    sample_node_binding = {
        "id": "SGD:S000000065",
        # 'qnode_id' is not formally specified in spec but it is an
        # example of an additionalProperties: true permitted field
        "qnode_id": "SGD:S000000065",
        "query_id": None
    }

    validate(sample_node_binding, "NodeBinding", query)
    with pytest.raises(ValidationError):
        validate({
            # missing required: id
            "foo": {},
            "bar": {},
        }, "NodeBinding", query)


@pytest.mark.parametrize("query", TEST_VERSIONS)
def test_message_attribute_component_validation(query):
    """Test Attribute component in validate()."""
    sample_attribute = {
        "attribute_type_id": "some_attribute",
        "value": "value",
        "value_type_id": None
    }
    validate(sample_attribute, "Attribute", query)
    with pytest.raises(ValidationError):
        validate({
            # missing required: attribute_type_id, value; plus, 'additionalProperties: false'
            "foo": {},
            "bar": {},
        }, "Attribute", query)
    with pytest.raises(ValidationError):
        validate({
            # these two attributes don't have 'nullable: true' so they should have values
            "attribute_type_id": None,
            "value": None
        }, "Attribute", query)


@pytest.mark.parametrize("query", TEST_VERSIONS)
def test_message_edge_component_validation(query):
    """Test Attribute component in validate()."""
    sample_attribute = {
        "subject": "aSubject",
        "predicate": None,
        "object": "anObject"
    }
    validate(sample_attribute, "Edge", query)
    with pytest.raises(ValidationError):
        validate({
            # missing required: subject, object
            "foo": {},
            "bar": {},
        }, "Edge", query)
    with pytest.raises(ValidationError):
        validate({
            # subject, object are not nullable, so...
            "subject": None,
            "object": None
        }, "Edge", query)
