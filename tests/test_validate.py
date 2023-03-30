"""Test validation."""
from sys import stderr
import pytest

from jsonschema.exceptions import ValidationError

from reasoner_validator.trapi import TRAPISchemaValidator, openapi_to_jsonschema


PRE_1_4_0_TEST_VERSIONS = "1.4.0-beta",   # "1.2", "1.2.0", "1.3", "1.3.0"

# last 'version' is a branch name, i.e. master?
LATEST_TEST_VERSIONS = "1", "1.4.0-beta", "master"


@pytest.mark.parametrize(
    "query",
    [
            {
                'allOf':
                    [{'$ref': '#/components/schemas/CURIE'}],
                'description': 'something',
                'nullable': True
            },
            {
                'oneOf':
                    [{'$ref': '#/components/schemas/CURIE'}],
                'description': 'something',
                'nullable': True
            },
            {
                'description': 'something',
                'nullable': True,
                '$ref': '#/components/schemas/CURIE'
            }
    ]
)
def test_openapi_to_jsonschema(query):
    print(f"\nEntering openapi_to_jsonschema(schema: {str(query)})", file=stderr)
    openapi_to_jsonschema(query)
    print(f"\nExiting openapi_to_jsonschema(schema: {str(query)})", file=stderr)


@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test_query_and_version_completion(trapi_version):
    """Test TRAPIValidator(trapi_version=query).validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    validator.validate({
        "message": {},
    }, "Query")
    with pytest.raises(ValidationError):
        validator.validate({
            "foo": {},
            "bar": {},
        }, "Query")


@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test_edgebinding(trapi_version):
    """Test TRAPIValidator(trapi_version=query).validate_EdgeBinding()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    validator.validate({
        "id": "hello",
    }, "EdgeBinding")
    with pytest.raises(ValidationError):
        validator.validate({
            "foo": {},
        }, "EdgeBinding")


@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test_nullable(trapi_version):
    """Test nullable categories property."""
    qnode = {
        "categories": None
    }
    TRAPISchemaValidator(trapi_version=trapi_version).validate(qnode, "QNode")
    # I cannot really trigger anything using 'with pytest.raises(ValidationError)'
    # since QNode has 'additionalProperties: true' but no 'required:' properties


@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test_nullable_message_properties(trapi_version):
    """Test nullable message properties."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    message = {
        "knowledge_graph": None,
        "query_graph": None,
        "results": None,
    }
    validator.validate(message, "Message")
    with pytest.raises(ValidationError):
        validator.validate({
            "foo": {},  # additionalProperties: false and 'foo' is not a documented property...
        }, "Message")


@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test_nullable_query_level_properties(trapi_version):
    """Test nullable TRAPI Query level properties."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    trapi_query = {
        "message": {
            "knowledge_graph": None,
            "query_graph": None,
            "results": None,
        },
        "log_level": None,
        "workflow": None
    }
    validator.validate(trapi_query, "Query")
    with pytest.raises(ValidationError):
        validator.validate({
            "foo": {},  # missing required: message
        }, "Query")


@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test_nullable_async_query_level_properties(trapi_version):
    """Test nullable TRAPI Query level properties."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
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
    validator.validate(async_trapi_query, "AsyncQuery")
    with pytest.raises(ValidationError):
        validator.validate({
            "foo": {},  # missing required: callback, message
        }, "AsyncQuery")


@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test_nullable_response_properties(trapi_version):
    """Test nullable TRAPI Query level properties."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    async_trapi_query = {
        "message": {
            "knowledge_graph": None,
            "query_graph": None,
            "results": None,
        },
        "workflow": None
    }
    validator.validate(async_trapi_query, "Response")
    with pytest.raises(ValidationError):
        validator.validate({
            "foo": {},  # missing required: message
        }, "Response")


# TODO: this test may not pass until TRAPI 1.3 query_id spec is fixed?
@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test_message_results_component_validation(trapi_version):
    """Test Message.Results component in TRAPIValidator(trapi_version=query).validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
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
    validator.validate(sample_message_result, "Result")
    with pytest.raises(ValidationError):
        validator.validate({
            # missing required: node_bindings, edge_bindings
            "foo": {},
            "bar": {},
        }, "Result")


# TODO: this test may not pass until TRAPI 1.3 query_id spec is fixed?
@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test_message_node_binding_component_validation(trapi_version):
    """Test NodeBinding component in TRAPIValidator(trapi_version=query).validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    sample_node_binding = {
        "id": "SGD:S000000065",
        # 'qnode_id' is not formally specified in spec but it is an
        # example of an additionalProperties: true permitted field
        "qnode_id": "SGD:S000000065",
        "query_id": None
    }

    validator.validate(sample_node_binding, "NodeBinding")
    with pytest.raises(ValidationError):
        validator.validate({
            # missing required: id
            "foo": {},
            "bar": {},
        }, "NodeBinding")


@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test_message_attribute_component_validation(trapi_version):
    """Test Attribute component in TRAPIValidator(trapi_version=query).validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    sample_attribute = {
        "attribute_type_id": "some_attribute",
        "value": "value",
        "value_type_id": None
    }
    validator.validate(sample_attribute, "Attribute")
    with pytest.raises(ValidationError):
        validator.validate({
            # missing required: attribute_type_id, value; plus, 'additionalProperties: false'
            "foo": {},
            "bar": {},
        }, "Attribute")
    with pytest.raises(ValidationError):
        validator.validate({
            # these two attributes don't have 'nullable: true' so they should have values
            "attribute_type_id": None,
            "value": None
        }, "Attribute")


@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test_message_edge_component_pre_1_4_0_trapi_validation(trapi_version):
    """Test Attribute component in TRAPIValidator(trapi_version=query).validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    sample_attribute = {
        "subject": "aSubject",
        "predicate": None,
        "object": "anObject"
    }
    validator.validate(sample_attribute, "Edge")
    with pytest.raises(ValidationError):
        validator.validate({
            # missing required and not null: subject, predicate, object
            "foo": {},
            "bar": {},
        }, "Edge")
    with pytest.raises(ValidationError):
        validator.validate({
            # subject, object are not nullable, so...
            "subject": None,
            "object": None
        }, "Edge")


@pytest.mark.parametrize("trapi_version", LATEST_TEST_VERSIONS)
def test_message_edge_component_latest_trapi_validation(trapi_version):
    """Test Attribute component in TRAPIValidator(trapi_version=query).validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    sample_attribute = {
        "subject": "aSubject",
        "predicate": "biolink:related_to",
        "object": "anObject",
        "sources": "need-to-somehow-provide-a-retrieval-source"
    }
    validator.validate(sample_attribute, "Edge")
    with pytest.raises(ValidationError):
        validator.validate({
            # missing required and not null: subject, predicate, object
            "foo": {},
            "predicate": None,
            "bar": {},
        }, "Edge")
    with pytest.raises(ValidationError):
        validator.validate({
            # subject, object are not nullable, so...
            "subject": None,
            "object": None
        }, "Edge")
