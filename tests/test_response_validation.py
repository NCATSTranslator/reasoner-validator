"""
Unit tests for the generic (shared) components of the SRI Testing Framework
"""
from typing import Tuple,  Dict, Union
import logging
import pytest

from reasoner_validator import TRAPIResponseValidator
from tests.test_validation_report import check_messages

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


_TEST_QG = {
    "nodes": {
        "type-2 diabetes": {"ids": ["MONDO:0005148"]},
        "drug": {
            "categories": ["biolink:Drug"]
        }
    },
    "edges": {
        "treats": {
            "subject": "drug",
            "predicates": ["biolink:treats"],
            "object": "type-2 diabetes"
        }
    }
}
_TEST_KG = {
    # Sample nodes
    'nodes': {
        "NCBIGene:29974": {
           "categories": [
               "biolink:Gene"
           ]
        },
        "PUBCHEM.COMPOUND:597": {
            "name": "cytosine",
            "categories": [
                "biolink:SmallMolecule"
            ],
            "attributes": [
                {
                    "attribute_source": "infores:chembl",
                    "attribute_type_id": "biolink:highest_FDA_approval_status",
                    "attributes": [],
                    "original_attribute_name": "max_phase",
                    "value": "FDA Clinical Research Phase 2",
                    "value_type_id": "biolink:FDA_approval_status_enum"
                }
            ]
        }
    },
    # Sample edge
    'edges': {
       "edge_1": {
           "subject": "NCBIGene:29974",
           "predicate": "biolink:interacts_with",
           "object": "PUBCHEM.COMPOUND:597",
           "attributes": [
               {
                   "attribute_source": "infores:hmdb",
                   "attribute_type_id": "biolink:primary_knowledge_source",
                   "attributes": [],
                   "description": "MolePro's HMDB target transformer",
                   "original_attribute_name": "biolink:primary_knowledge_source",
                   "value": "infores:hmdb",
                   "value_type_id": "biolink:InformationResource"
               },
               {
                   "attribute_source": "infores:hmdb",
                   "attribute_type_id": "biolink:aggregator_knowledge_source",
                   "attributes": [],
                   "description": "Molecular Data Provider",
                   "original_attribute_name": "biolink:aggregator_knowledge_source",
                   "value": "infores:molepro",
                   "value_type_id": "biolink:InformationResource"
               }
            ]
        }
    }
}


@pytest.mark.parametrize(
    "query",
    [
        (   # Query 0 - Completely empty Response.Message
            {},
            None,
            None,
            # "Validate TRAPI Response: ERROR - Response returned an empty Message Query Graph!"
            "error.response.message.empty"
        ),
        (   # Query 1 - Response.Message also devoid of content, missing QGraph trapped first....
            {
                "knowledge_graph": None,
                "results": None
            },
            None,
            None,
            # "Validate TRAPI Response: ERROR - TRAPI Message is missing its Query Graph!"
            "error.response.query_graph.missing"
        ),
        (   # Query 2 - Response.Message also devoid of content, null QGraph trapped first....
            {
                "query_graph": None,
                "knowledge_graph": None,
                "results": None
            },
            None,
            None,
            # "Validate TRAPI Response: ERROR - Response returned an null or empty Message Query Graph!"
            "error.response.query_graph.empty"
        ),
        (
            # Query 3 - Partly empty Response.Message with a modest but
            #           workable query graph? Missing KG trapped next?
            {
                "query_graph": _TEST_QG,
                # "knowledge_graph": None,
                "results": None
            },
            None,
            None,
            # "Validate TRAPI Response: ERROR - TRAPI Message is missing its Knowledge Graph component?"
            "error.response.knowledge_graph.missing"
        ),
        (
            # Query 4 - Partly empty Response.Message with a modest
            #           but workable query graph? Empty KG trapped next?
            {
                "query_graph": _TEST_QG,
                "knowledge_graph": None,
                "results": None
            },
            None,
            None,
            # "Validate TRAPI Response: WARNING - Response returned an empty Message Knowledge Graph?"
            "warning.response.knowledge_graph.empty"
        ),
        (
            # Query 5 - Partly empty Response.Message with a modest but workable
            #           query and knowledge graphs? Missing Results detected next?
            {
                "query_graph": _TEST_QG,
                "knowledge_graph": _TEST_KG,
                # "results": None
            },
            None,
            None,
            # "Validate TRAPI Response: ERROR - TRAPI Message is missing its Results component!"
            "error.response.results.missing"
        ),
        (
            # Query 6 - Partly empty Response.Message with a modest but workable query and
            #           knowledge graphs? Null valued Results detected next - just issue a warning?
            {
                "query_graph": _TEST_QG,
                "knowledge_graph": _TEST_KG,
                "results": None
            },
            None,
            None,
            # "Validate TRAPI Response: WARNING -Response returned empty Message.results?"
            "warning.response.results.empty"
        ),
        (
            # Query 7 - Partly empty Response.Message with a modest but workable
            #           query and knowledge graphs? Non-array Results detected next?
            {
                "query_graph": _TEST_QG,
                "knowledge_graph": _TEST_KG,
                "results": {"invalid results"}
            },
            None,
            None,
            # "Validate TRAPI Response: ERROR - Response returned a non-array Message.results!"
            "error.response.results.non_array"
        ),
        (
            # Query 8 - Partly empty Response.Message with a modest but workable query and
            #           knowledge graphs? Empty Results detected next - just issue a warning?
            {
                "query_graph": _TEST_QG,
                "knowledge_graph": _TEST_KG,
                "results": []
            },
            None,
            None,
            # "Validate TRAPI Response: ERROR - Response returned empty Message.results?"
            "warning.response.results.empty"
        )
    ]
)
def test_check_biolink_model_compliance_of_trapi_response(query: Tuple[Union[Dict, str]]):
    validator: TRAPIResponseValidator = TRAPIResponseValidator(
        trapi_version=query[1],
        biolink_version=query[2]
    )
    validator.check_compliance_of_trapi_response(message=query[0])
    check_messages(validator, query[3])
