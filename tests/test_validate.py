"""Test validation."""
from sys import stderr
from typing import Tuple, Dict, Optional
from copy import deepcopy

import pytest

from jsonschema.exceptions import ValidationError

from reasoner_validator.trapi import (
    TRAPISchemaValidator,
    openapi_to_jsonschema,
    load_schema,
    LATEST_TRAPI_RELEASE
)
from tests import (
    LATEST_TEST_RELEASES,
    PRE_1_4_0_TEST_VERSIONS,
    ALL_TEST_VERSIONS,
    PRE_1_5_0_TEST_VERSIONS, TRAPI_1_4_TEST_VERSIONS
)


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
            LATEST_TEST_RELEASES[2]
        ),
        (  # query 4
            {
                'oneOf':
                    [{'$ref': '#/components/schemas/CURIE'}],
                'description': 'something',
                'nullable': True
            },
            LATEST_TEST_RELEASES[2]
        ),
        (  # query 5
            {
                'description': 'something',
                'nullable': True,
                '$ref': '#/components/schemas/CURIE'
            },
            LATEST_TEST_RELEASES[2]
        )
    ]
)
def test_openapi_to_jsonschema(query: Tuple[Dict, str]):
    print(f"\nEntering openapi_to_jsonschema(schema: {str(query)})", file=stderr)
    openapi_to_jsonschema(schema=query[0], version=query[1])
    assert "oneOf" in query[0]  # the 'oneOf' creeps in one way or another
    print(f"\nExiting openapi_to_jsonschema(schema: {str(query)})", file=stderr)


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
def test_load_schema(trapi_version: str):
    """Test load_schema(trapi_version)."""
    schema = load_schema(trapi_version)
    assert schema, f"TRAPI Schema for release '{trapi_version}' is not available?"


@pytest.mark.skip("May 9, 2024 master branch of ReasonerAPI has a schema bug which crashes this test")
def test_load_master_schema():
    """Test load_schema('master')."""
    schema = load_schema("master")
    assert schema, "TRAPI Schema for ('master') branch is not available?"


def test_message():
    reporter = TRAPISchemaValidator(
        default_test="test_message",
        default_target="Test Message",
        trapi_version=LATEST_TRAPI_RELEASE
    )
    assert reporter.get_trapi_version() == LATEST_TRAPI_RELEASE
    assert not reporter.has_messages()
    reporter.report("info.compliant")
    assert reporter.has_messages()
    reporter.dump()


@pytest.mark.parametrize(
    "trapi_version",
    ALL_TEST_VERSIONS
)
def test_query_and_version_completion(trapi_version: str):
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


@pytest.mark.parametrize("trapi_version", PRE_1_5_0_TEST_VERSIONS)
def test_trapi_pre_1_5_edgebinding(trapi_version: str):
    """Test TRAPIValidator(trapi_version=query).validate_EdgeBinding()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    validator.validate({
        "id": "hello",
    }, "EdgeBinding")
    with pytest.raises(ValidationError):
        validator.validate({
            "foo": {},
        }, "EdgeBinding")


@pytest.mark.skip(reason="Not updated to work correctly with TRAPI 1.5.0")
@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_trapi_1_5_edgebinding(trapi_version: str):
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
def test_nullable(trapi_version: str):
    """Test nullable categories property."""
    qnode = {
        "categories": None
    }
    TRAPISchemaValidator(trapi_version=trapi_version).validate(qnode, "QNode")
    # I cannot really trigger anything using 'with pytest.raises(ValidationError)'
    # since QNode has 'additionalProperties: true' but no 'required:' properties


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
def test_nullable_message_properties(trapi_version: str):
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
def test_nullable_query_level_properties(trapi_version: str):
    """Test nullable TRAPI Query level properties."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    trapi_query = {
        "message": {
            "knowledge_graph": None,
            "query_graph": None,
            "results": None,
        },
        "log_level": "INFO",
        "workflow": None
    }
    validator.validate(trapi_query, "Query")
    with pytest.raises(ValidationError):
        validator.validate({
            "foo": {},  # missing required: message
        }, "Query")


SAMPLE_QUERY = {
        "message": {
        },
        "log_level": "INFO"
    }


SAMPLE_WORKFLOW_1_0_0 = [
    {
        "id": "sort_results_score",
        "parameters": {
            "ascending_or_descending": "ascending"
        }
    },
    {
        "id": "fill",
        "parameters": {
            "allowlist": [
                "infores:aragorn"
            ]
        }
    }
]


@pytest.mark.parametrize("trapi_version", PRE_1_4_0_TEST_VERSIONS)
def test_query_trapi_pre_1_4_0_workflow_properties(trapi_version: str):
    """Test flawed TRAPI Query workflow properties with pre-TRAPI 1.4.0."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    query = deepcopy(SAMPLE_QUERY)
    query["workflow"] = SAMPLE_WORKFLOW_1_0_0
    validator.validate(query, "Query")
    with pytest.raises(ValidationError):
        faulty_query_wf = deepcopy(query)
        # 'workflow' value is not an array?
        faulty_query_wf["workflow"] = "not_an_array"
        validator.validate(faulty_query_wf, "Query")
    with pytest.raises(ValidationError):
        faulty_query_wf = deepcopy(query)
        # Items in the 'workflow' array must be workflow spec JSON objects
        # defined in the schema https://standards.ncats.io/operation/1.3.2/schema
        faulty_query_wf["workflow"] = [
            "not_a_workflow_object"
        ]
        validator.validate(faulty_query_wf, "Query")
    with pytest.raises(ValidationError):
        faulty_query_wf = deepcopy(query)
        # Items in the 'workflow' array must be well-formed workflow spec JSON objects
        # as defined in the schema https://standards.ncats.io/operation/1.3.2/schema.
        # To start, in a workflow object the 'id' object key is mandatory ...
        faulty_query_wf["workflow"] = [
            {
                "runner_parameters": "missing-id"
            }
        ]
        validator.validate(faulty_query_wf, "Query")


SAMPLE_WORKFLOW_1_3_4 = [
    {
        "id": "sort_results_score",
        "parameters": {
            "ascending_or_descending": "ascending"
        }
    },
    {
        "id": "lookup",
        "runner_parameters": {
            "allowlist": {
                "allowlist": ["infores:aragorn"]
            }
        }
    }
]


@pytest.mark.parametrize("trapi_version", TRAPI_1_4_TEST_VERSIONS)
def test_pre_1_5_query_latest_trapi_workflow_properties(trapi_version: str):
    """Test flawed TRAPI Query workflow properties."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    query = deepcopy(SAMPLE_QUERY)
    query["workflow"] = SAMPLE_WORKFLOW_1_3_4
    validator.validate(query, "Query")
    with pytest.raises(ValidationError):
        faulty_query_wf = deepcopy(query)
        # ...and the 'id' object key should have a schema-defined enum as its value,...
        faulty_query_wf["workflow"] = [
            {
                "id": "not-a-workflow-enum"
            }
        ]
        validator.validate(faulty_query_wf, "Query")
    with pytest.raises(ValidationError):
        faulty_query_wf = deepcopy(query)
        # ...and if 'runner_parameters' key is present and has a non-empty value,
        # it needs oneOf the "allowlist" or "denylist" keys...
        faulty_query_wf["workflow"] = [
            {
                "id": "sort_results_score",
                "runner_parameters": {}
            }
        ]
        validator.validate(faulty_query_wf, "Query")
    with pytest.raises(ValidationError):
        faulty_query_wf = deepcopy(query)
        # ...and if 'runner_parameters' object "allowlist" or "denylist"
        # is present, they must have a non-empty value, of at least one infores CURIE.
        faulty_query_wf["workflow"] = [
            {
                "id": "lookup",
                "runner_parameters": {
                    "allowlist": []
                }
            }
        ]
        validator.validate(faulty_query_wf, "Query")


@pytest.mark.skip(reason="Not updated to work correctly with TRAPI 1.5.0")
@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_1_5_query_latest_trapi_workflow_properties(trapi_version: str):
    """Test flawed TRAPI Query workflow properties."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    query = deepcopy(SAMPLE_QUERY)
    query["workflow"] = SAMPLE_WORKFLOW_1_3_4
    validator.validate(query, "Query")
    with pytest.raises(ValidationError):
        faulty_query_wf = deepcopy(query)
        # ...and the 'id' object key should have a schema-defined enum as its value,...
        faulty_query_wf["workflow"] = [
            {
                "id": "not-a-workflow-enum"
            }
        ]
        validator.validate(faulty_query_wf, "Query")
    with pytest.raises(ValidationError):
        faulty_query_wf = deepcopy(query)
        # ...and if 'runner_parameters' key is present and has a non-empty value,
        # it needs oneOf the "allowlist" or "denylist" keys...
        faulty_query_wf["workflow"] = [
            {
                "id": "sort_results_score",
                "runner_parameters": {}
            }
        ]
        validator.validate(faulty_query_wf, "Query")
    with pytest.raises(ValidationError):
        faulty_query_wf = deepcopy(query)
        # ...and if 'runner_parameters' object "allowlist" or "denylist"
        # is present, they must have a non-empty value, of at least one infores CURIE.
        faulty_query_wf["workflow"] = [
            {
                "id": "lookup",
                "runner_parameters": {
                    "allowlist": []
                }
            }
        ]
        validator.validate(faulty_query_wf, "Query")


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
def test_nullable_async_query_level_properties(trapi_version: str):
    """Test nullable TRAPI Query level properties."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    async_trapi_query = {
        "callback": "http://mykp.ncats.io/callback",
        "message": {
            "knowledge_graph": None,
            "query_graph": None,
            "results": None,
        },
        "log_level": "INFO",
        "workflow": None
    }
    validator.validate(async_trapi_query, "AsyncQuery")
    with pytest.raises(ValidationError):
        validator.validate({
            "foo": {},  # missing required: callback, message
        }, "AsyncQuery")


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
def test_nullable_response_properties(trapi_version: str):
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
def test_trapi_pre_1_4_0_message_results_component_validation(trapi_version: str):
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


@pytest.mark.parametrize("trapi_version", TRAPI_1_4_TEST_VERSIONS)
def test_trapi_1_4_message_results_component_validation(trapi_version: str):
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
    #         resource_id:
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
    #         - resource_id
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
                "resource_id": "infores:arax",
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


@pytest.mark.skip(reason="Not updated to work correctly with TRAPI 1.5.0")
@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_message_results_component_validation(trapi_version: str):
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
    #         resource_id:
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
    #         - resource_id
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
                "resource_id": "infores:arax",
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


@pytest.mark.parametrize("trapi_version", PRE_1_5_0_TEST_VERSIONS)
def test_message_pre_1_5_node_binding_component_validation(trapi_version: str):
    """Test NodeBinding component in TRAPIValidator(trapi_version=query).validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    sample_node_binding = {
        "id": "SGD:S000000065",
        # 'qnode_id' is not formally specified in spec, but it is an
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


@pytest.mark.skip(reason="Not updated to work correctly with TRAPI 1.5.0")
@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_message_node_binding_component_validation(trapi_version: str):
    """Test NodeBinding component in TRAPIValidator(trapi_version=query).validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    sample_node_binding = {
        "id": "SGD:S000000065",
        # 'qnode_id' is not formally specified in spec, but it is an
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
def test_message_attribute_component_validation(trapi_version: str):
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
def test_pre_1_4_0_trapi_message_edge_component_validation(trapi_version: str):
    """Test 'good' Message.KnowledgeGraph.Edge component in
       TRAPIValidator(trapi_version="PRE_1_4_0_TEST_VERSIONS").validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    sample_edge = {
        "subject": "aSubject",
        "predicate": None,  # the predicate could be missing in pre-1.4.0 schemata
        "object": "anObject"
    }
    validator.validate(sample_edge, "Edge")
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


SAMPLE_RETRIEVAL_SOURCE = {
    # required, infores CURIE to an Information Resource
    "resource_id": "infores:molepro",

    # required, string drawn from the TRAPI ResourceRoleEnum
    # values that were formerly recorded as TRAPI attributes
    # are now presented as first class edge annotation
    "resource_role": "primary_knowledge_source"
}


SAMPLE_LATEST_TEST_EDGE = {
    "subject": "MONDO:0011382",   # subject must be a CURIE
    "predicate": "biolink:related_to",  # subject must be a biolink Predicate CURIE
    "object": "UniProtKB:P00738",   # subject must be a CURIE
    "sources": [  # an array of RetrievalSource
        SAMPLE_RETRIEVAL_SOURCE
    ]
}


@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_good_message_edge_component_validation(trapi_version: str):
    """Test 'good' Message.KnowledgeGraph.Edge component in
       TRAPIValidator(trapi_version="LATEST_TEST_VERSIONS").validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    validator.validate(SAMPLE_LATEST_TEST_EDGE, "Edge")


@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_missing_key_message_edge_component_validation(trapi_version: str):
    """Test Message.KnowledgeGraph.Edge components missing their required keys
       in TRAPIValidator(trapi_version="LATEST_TEST_VERSIONS").validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    with pytest.raises(ValidationError):
        validator.validate({
            # missing required 'subject', 'predicate', 'object' and "sources"
            "foo": {},
            "bar": {},
        }, "Edge")


@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_null_message_edge_component_validation(trapi_version: str):
    """Test Message.KnowledgeGraph.Edge components having null values in
       TRAPIValidator(trapi_version="LATEST_TEST_VERSIONS").validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    with pytest.raises(ValidationError):
        null_subject: Dict[str, Optional] = SAMPLE_LATEST_TEST_EDGE.copy()
        null_subject["subject"] = None
        validator.validate(null_subject, "Edge")
    with pytest.raises(ValidationError):
        null_predicate: Dict[str, Optional] = SAMPLE_LATEST_TEST_EDGE.copy()
        null_predicate["predicate"] = None
        validator.validate(null_predicate, "Edge")


@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_flawed_message_edge_component_validation(trapi_version: str):
    """Test invalid Message.KnowledgeGraph.Edge.predicate in
       TRAPIValidator(trapi_version="LATEST_TEST_VERSIONS").validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    with pytest.raises(ValidationError):
        faulty_predicate = SAMPLE_LATEST_TEST_EDGE.copy()
        # predicate is not a Biolink predicate term CURIE
        faulty_predicate["predicate"] = "not-a-biolink-predicate-CURIE"
        validator.validate(faulty_predicate, "Edge")


@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_more_flawed_message_edge_retrieval_sources_component_validation(trapi_version: str):
    """Test various invalid Message.KnowledgeGraph.Edge.sources values in
       TRAPIValidator(trapi_version="LATEST_TEST_VERSIONS").validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    with pytest.raises(ValidationError):
        faulty_target_provenance = SAMPLE_LATEST_TEST_EDGE.copy()
        # "target_provenance" is not an array (of RetrievalSource objects)
        faulty_target_provenance["target_provenance"] = "not-an-array"
        validator.validate(faulty_target_provenance, "Edge")
    with pytest.raises(ValidationError):
        faulty_target_provenance = SAMPLE_LATEST_TEST_EDGE.copy()
        # items in the "target_provenance" array must be a non-empty array of (RetrievalSource) objects
        faulty_target_provenance["target_provenance"] = list()
        validator.validate(faulty_target_provenance, "Edge")
    with pytest.raises(ValidationError):
        faulty_target_provenance = SAMPLE_LATEST_TEST_EDGE.copy()
        # items in the "target_provenance" array must be (RetrievalSource) objects
        faulty_target_provenance["target_provenance"] = ["not-a-json-object"]
        validator.validate(faulty_target_provenance, "Edge")
    with pytest.raises(ValidationError):
        faulty_target_provenance = SAMPLE_LATEST_TEST_EDGE.copy()
        # items in the "target_provenance" array must be RetrievalSource objects
        faulty_target_provenance["target_provenance"] = [{"not-an-RetrievalSource-key": "something"}]
        validator.validate(faulty_target_provenance, "Edge")


@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_more_flawed_message_edge_retrieval_sources_component_validation(trapi_version: str):
    """Test various invalid Message.KnowledgeGraph.Edge.sources values in
       TRAPIValidator(trapi_version="LATEST_TEST_VERSIONS").validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    with pytest.raises(ValidationError):
        faulty_rs = SAMPLE_RETRIEVAL_SOURCE.copy()
        # items in the "target_provenance" array must be
        # RetrievalSource objects with a 'resource' key
        faulty_rs.pop("resource_id")
        validator.validate(faulty_rs, "RetrievalSource")
    with pytest.raises(ValidationError):
        faulty_rs = SAMPLE_RETRIEVAL_SOURCE.copy()
        # items in the "target_provenance" array must be
        # RetrievalSource objects with a 'resource' key
        faulty_rs.pop("resource_role")
        validator.validate(faulty_rs, "RetrievalSource")
    with pytest.raises(ValidationError):
        faulty_rs = SAMPLE_RETRIEVAL_SOURCE.copy()
        # items in the "target_provenance" array must be
        # RetrievalSource objects with a 'resource' key
        faulty_rs["resource_role"] = "not_a_ResourceRoleEnum_enum_value"
        validator.validate(faulty_rs, "RetrievalSource")
