"""Test validation."""
from sys import stderr
from typing import Tuple, Dict

import pytest

from jsonschema.exceptions import ValidationError

from reasoner_validator.trapi import TRAPISchemaValidator, openapi_to_jsonschema


PRE_1_4_0_TEST_VERSIONS = "1.2", "1.2.0", "1.3", "1.3.0"

# last 'version' in the list is a branch name, i.e. master?
LATEST_TEST_VERSIONS = "1", "1.4", "1.4.0", "1.4.0-beta", "master"

ALL_TEST_VERSIONS = PRE_1_4_0_TEST_VERSIONS + LATEST_TEST_VERSIONS


@pytest.mark.parametrize(
    "query",
    [
        (  # query 0
            {
                'allOf':
                    [{'$ref': '#/components/schemas/CURIE'}],
                'description': 'something',
                'nullable': True
            },
            "1.3.0"
        ),
        (  # query 1
            {
                'oneOf':
                    [{'$ref': '#/components/schemas/CURIE'}],
                'description': 'something',
                'nullable': True
            },
            "1.3.0"
        ),
        (  # query 2
            {
                'description': 'something',
                'nullable': True,
                '$ref': '#/components/schemas/CURIE'
            },
            "1.3.0"
        ),
        (  # query 3
            {
                'allOf':
                    [{'$ref': '#/components/schemas/CURIE'}],
                'description': 'something',
                'nullable': True
            },
            # this version keeps the 'allOf' but
            # buries it further downwards... Do we care?
            LATEST_TEST_VERSIONS[2]
        ),
        (  # query 4
            {
                'oneOf':
                    [{'$ref': '#/components/schemas/CURIE'}],
                'description': 'something',
                'nullable': True
            },
            LATEST_TEST_VERSIONS[2]
        ),
        (  # query 5
            {
                'description': 'something',
                'nullable': True,
                '$ref': '#/components/schemas/CURIE'
            },
            LATEST_TEST_VERSIONS[2]
        )
    ]
)
def test_openapi_to_jsonschema(query: Tuple[Dict, str]):
    print(f"\nEntering openapi_to_jsonschema(schema: {str(query)})", file=stderr)
    openapi_to_jsonschema(schema=query[0], version=query[1])
    assert "oneOf" in query[0]  # the 'oneOf' creeps in one way or another
    print(f"\nExiting openapi_to_jsonschema(schema: {str(query)})", file=stderr)


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
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


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
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


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
def test_nullable(trapi_version):
    """Test nullable categories property."""
    qnode = {
        "categories": None
    }
    TRAPISchemaValidator(trapi_version=trapi_version).validate(qnode, "QNode")
    # I cannot really trigger anything using 'with pytest.raises(ValidationError)'
    # since QNode has 'additionalProperties: true' but no 'required:' properties


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
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


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
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


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
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


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
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


@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test__trapi_pre_1_4_0_message_results_component_validation(trapi_version):
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


@pytest.mark.parametrize("trapi_version", LATEST_TEST_VERSIONS)
def test_latest_trapi_message_results_component_validation(trapi_version):
    """Test Message.Results component in TRAPIValidator(trapi_version=query).validate()."""
    #     Result:
    #       type: object
    #       description: >-
    #         A Result object specifies the nodes and edges in the knowledge graph
    #         that satisfy the structure or conditions of a user-submitted query
    #         graph. It must contain a NodeBindings object (list of query graph node
    #         to knowledge graph node mappings) and an EdgeBindings object (list of
    #         query graph edge to knowledge graph edge mappings).
    #       properties:
    #         node_bindings:
    #           type: object
    #           description: >-
    #             The dictionary of Input Query Graph to Result Knowledge Graph node
    #             bindings where the dictionary keys are the key identifiers of the
    #             Query Graph nodes and the associated values of those keys are
    #             instances of NodeBinding schema type (see below). This value is an
    #             array of NodeBindings since a given query node may have multiple
    #             knowledge graph Node bindings in the result.
    #           additionalProperties:
    #             type: array
    #             items:
    #               $ref: '#/components/schemas/NodeBinding'
    #         analyses:
    #           type: array
    #           description: >-
    #             The list of all Analysis components that contribute to the result.
    #             See below for Analysis components.
    #           items:
    #             $ref: '#/components/schemas/Analysis'
    #       additionalProperties: true
    #       required:
    #         - node_bindings
    #         - analyses
    # where an Analysis object is:
    #     Analysis:
    #       type: object
    #       description: >-
    #         An analysis is a dictionary that contains information about
    #         the result tied to a particular service. Each Analysis is
    #         generated by a single reasoning service, and describes the
    #         outputs of analyses performed by the reasoner on a particular
    #         Result (e.g. a result score), along with provenance information
    #         supporting the analysis (e.g. method or data that supported
    #         generation of the score).
    #       properties:
    #         reasoner_id:
    #           $ref: '#/components/schemas/CURIE'
    #           description: The id of the service generating and using this Anlysis
    #         score:
    #           type: number
    #           format: float
    #           example: 163.233
    #           description: >-
    #             A numerical score associated with this result indicating the
    #             relevance or confidence of this result relative to others in the
    #             returned set. Higher MUST be better.
    #           nullable: true
    #         edge_bindings:
    #           type: object
    #           description: >-
    #             The dictionary of input Query Graph to Knowledge Graph edge
    #             bindings where the dictionary keys are the key identifiers of the
    #             Query Graph edges and the associated values of those keys are
    #             instances of EdgeBinding schema type (see below). This value is an
    #             array of EdgeBindings since a given query edge may resolve to
    #             multiple Knowledge Graph Edges.
    #           additionalProperties:
    #             type: array
    #             items:
    #               $ref: '#/components/schemas/EdgeBinding'
    #         support_graphs:
    #           type: array
    #           description: >-
    #             This is a list of references to Auxiliary Graph instances
    #             that supported the analysis of a Result as performed by the
    #             reasoning service. Each item in the list is the key of a
    #             single Auxiliary Graph.
    #           nullable: true
    #           items:
    #             type: string
    #         scoring_method:
    #           type: string
    #           description: >-
    #             An identifier and link to an explanation for the method used
    #             to generate the score
    #           nullable: true
    #         attributes:
    #           type: array
    #           description: >-
    #             The attributes of this particular Analysis.
    #           items:
    #             $ref: '#/components/schemas/Attribute'
    #           nullable: true
    #       additionalProperties: true
    #       required:
    #         - reasoner_id
    #         - edge_bindings
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    sample_message_result = {
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
        "analyses": [
            {
                "reasoner_id": "infores:arax",
                "edge_bindings": {
                    "ab": [
                        {
                            "attributes": None,
                            "id": "uuid:7884e454-d09c-11ec-b00f-0242ac110002"
                        }
                    ]
                },
                "score": None
            }
        ]
    }

    validator.validate(sample_message_result, "Result")
    with pytest.raises(ValidationError):
        validator.validate({
            # missing required: node_bindings, edge_bindings
            "foo": {},
            "bar": {},
        }, "Result")


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
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


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
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
def test_pre_1_4_0_trapi_message_edge_component_validation(trapi_version):
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
def test_latest_trapi_message_edge_component_validation(trapi_version):
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
