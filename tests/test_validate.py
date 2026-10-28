"""Test validation."""
from sys import stderr
from typing import Tuple, List, Dict, Optional
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
    ALL_TEST_VERSIONS,
    TRAPI_2_0_COMPLIANT_QUERY_TEMPLATE
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


def test_load_master_schema():
    """Test load_schema('master')."""
    schema = load_schema("master")
    assert schema, "TRAPI Schema for ('master') branch is not available?"


def test_message():
    reporter = TRAPISchemaValidator(
        default_test="test_message",
        default_target="Test Message"
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


@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_post_trapi_2_0_edgebindings(trapi_version: str):
    """Test TRAPIValidator(trapi_version=query).validate_EdgeBinding()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    validator.validate({
        "ids": ["hello"]
    }, "EdgeBinding")
    with pytest.raises(ValidationError):
        validator.validate({
            "foo": {},
        }, "EdgeBinding")


SAMPLE_QUERY = {
        "message": {
        },
        "log_level": "INFO",
        "workflow": [{}]
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
                "allowlist": {
                    "allowlist": ["infores:aragorn"]
                }
            }
        }
    }
]


SAMPLE_WORKFLOW_1_5 = [
    {
        "id": "sort_results_score",
        "parameters": {
            "ascending_or_descending": "ascending"
        }
    },
    {
        "id": "lookup",
        "runner_parameters": {
            "allowlist":  ["infores:aragorn"]
        }
    }
]


def _query_trapi_workflow_properties_template(trapi_version: str, sample_workflow: List[Dict]):
    """Test flawed TRAPI Query workflow properties."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    query = deepcopy(SAMPLE_QUERY)
    query["workflow"] = sample_workflow
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
    # TODO: TRAPI validation doesn't seem to detect
    #       non-compliance with allowlist "minLength": 1
    # with pytest.raises(ValidationError):
    #     faulty_query_wf = deepcopy(query)
    #     # ...and if 'runner_parameters' object "allowlist" or "denylist"
    #     # is present, they must have a non-empty value, of at least one infores CURIE.
    #     faulty_query_wf["workflow"] = [
    #         {
    #             "id": "lookup",
    #             "runner_parameters": {
    #                 "allowlist": []
    #             }
    #         }
    #     ]
    #     validator.validate(faulty_query_wf, "Query")


@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_workflow_properties(trapi_version: str):
    _query_trapi_workflow_properties_template(trapi_version, SAMPLE_WORKFLOW_1_5)


@pytest.mark.parametrize("trapi_version", ALL_TEST_VERSIONS)
def test_nullable_async_query_level_properties(trapi_version: str):
    """Test nullable TRAPI Query level properties."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    async_trapi_query: dict = deepcopy(TRAPI_2_0_COMPLIANT_QUERY_TEMPLATE)
    async_trapi_query["callback"] = "http://mykp.ncats.io/callback"
    validator.validate(async_trapi_query, "AsyncQuery")
    with pytest.raises(ValidationError):
        validator.validate({
            "foo": {},  # missing required: callback, message
        }, "AsyncQuery")



@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_message_results_component_validation(trapi_version: str):
    """Test Message.Results component in TRAPIValidator(trapi_version=query).validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    sample_message_result = {
        "node_bindings": {
            "a": {"ids": ["SGD:S000000065"]},
            "b": {"ids": ["GO:1905776"]}
        },
        "analyses": [
            {
                "resource_id": "infores:arax",
                "edge_bindings": {
                    "ab": {
                        "ids": ["uuid:7884e454-d09c-11ec-b00f-0242ac110002"]
                    }
                }
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


@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_message_node_binding_component_validation(trapi_version: str):
    """Test NodeBinding component in TRAPIValidator(trapi_version=query).validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    sample_node_binding = {"ids": ["SGD:S000000065"]}

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
        "value": "value"
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
            # these three attributes don't have 'nullable: true' so they should have values
            "attribute_type_id": None,
            "value": None
        }, "Attribute")


SAMPLE_RETRIEVAL_SOURCE = {
    # required, infores CURIE to an Information Resource
    "resource_id": "infores:molepro",

    # required, string drawn from the TRAPI ResourceRoleEnum
    # values that were formerly recorded as TRAPI attributes
    # are now presented as first class edge annotation
    "resource_role": "primary_knowledge_source"
}


SAMPLE_TEST_EDGE = {
    "subject": "MONDO:0011382",   # subject must be a CURIE
    "predicate": "biolink:related_to",  # subject must be a biolink Predicate CURIE
    "object": "UniProtKB:P00738",   # subject must be a CURIE
    "sources": [  # an array of RetrievalSource
        SAMPLE_RETRIEVAL_SOURCE
    ],
    "knowledge_level": "logical_entailment",
    "agent_type": "automated_agent"
}


@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_post_2_0_trapi_good_message_edge_component_validation(trapi_version: str):
    """Test 'good' Message.KnowledgeGraph.Edge component in
       TRAPIValidator(trapi_version="LATEST_TEST_VERSIONS").validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    validator.validate(SAMPLE_TEST_EDGE, "Edge")


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
        null_subject: Dict[str, Optional] = SAMPLE_TEST_EDGE.copy()
        null_subject["subject"] = None
        validator.validate(null_subject, "Edge")
    with pytest.raises(ValidationError):
        null_predicate: Dict[str, Optional] = SAMPLE_TEST_EDGE.copy()
        null_predicate["predicate"] = None
        validator.validate(null_predicate, "Edge")


@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_flawed_message_edge_component_validation(trapi_version: str):
    """Test invalid Message.KnowledgeGraph.Edge.predicate in
       TRAPIValidator(trapi_version="LATEST_TEST_VERSIONS").validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    with pytest.raises(ValidationError):
        faulty_predicate = SAMPLE_TEST_EDGE.copy()
        # predicate is not a Biolink predicate term CURIE
        faulty_predicate["predicate"] = "not-a-biolink-predicate-CURIE"
        validator.validate(faulty_predicate, "Edge")


@pytest.mark.parametrize("trapi_version", LATEST_TEST_RELEASES)
def test_latest_trapi_more_flawed_message_edge_retrieval_sources_component_validation(trapi_version: str):
    """Test various invalid Message.KnowledgeGraph.Edge.sources values in
       TRAPIValidator(trapi_version="LATEST_TEST_VERSIONS").validate()."""
    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    with pytest.raises(ValidationError):
        faulty_target_provenance = SAMPLE_TEST_EDGE.copy()
        # "target_provenance" is not an array (of RetrievalSource objects)
        faulty_target_provenance["target_provenance"] = "not-an-array"
        validator.validate(faulty_target_provenance, "Edge")
    with pytest.raises(ValidationError):
        faulty_target_provenance = SAMPLE_TEST_EDGE.copy()
        # items in the "target_provenance" array must be a non-empty array of (RetrievalSource) objects
        faulty_target_provenance["target_provenance"] = list()
        validator.validate(faulty_target_provenance, "Edge")
    with pytest.raises(ValidationError):
        faulty_target_provenance = SAMPLE_TEST_EDGE.copy()
        # items in the "target_provenance" array must be (RetrievalSource) objects
        faulty_target_provenance["target_provenance"] = ["not-a-json-object"]
        validator.validate(faulty_target_provenance, "Edge")
    with pytest.raises(ValidationError):
        faulty_target_provenance = SAMPLE_TEST_EDGE.copy()
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
