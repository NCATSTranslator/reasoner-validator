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


_TEST_QG_1 = {
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

# Sample nodes
_TEST_NODES_1 = {
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
    }

# Sample edge 1
_TEST_EDGES_1 = {
       "edge_1": {
           "subject": "NCBIGene:29974",
           "predicate": "biolink:physically_interacts_with",
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
                   "attribute_source": "infores:molepro",
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

_TEST_KG_1 = {
    'nodes': _TEST_NODES_1,
    'edges': _TEST_EDGES_1
}

_TEST_RESULTS_1 = [
        {
            "node_bindings": {
                "type-2 diabetes": [{"id": "MONDO:0005148"}],
                "drug": [{"id": "CHEBI:6801"}]
            },
            "edge_bindings": {
                "treats": [{"id": "df87ff82"}]
            }
        }
    ]

# Sample edge 2
_TEST_EDGES_2 = {
       "edge_1": {
           "subject": "NCBIGene:29974",
           "predicate": "biolink:physically_interacts_with",
           "object": "PUBCHEM.COMPOUND:597",
           "attributes": [
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

_TEST_KG_2 = {
    'nodes': _TEST_NODES_1,
    'edges': _TEST_EDGES_2
}

_TEST_QG_2 = {
    "nodes": {
        "paper": {
            "categories": ["biolink:InformationContentEntity"]
        },
        "author": {
            "ids": ["ORCID:0000-0002-4447-5978"]
        }
    },
    "edges": {
        "citation": {
            "subject": "paper",
            "predicates": ["biolink:contributor"],
            "object": "author"
        }
    }
}

_TEST_NODES_2 = {
        "PMID:11156626": {
            "name": "A SNP resource for human chromosome 22: " +
                    "extracting dense clusters of SNPs from the genomic sequence",
            "categories": [
                "biolink:InformationContentEntity"
            ],
        },
        "ORCID:0000-0002-4447-5978": {
            "categories": [
                "biolink:AdministrativeEntity"
            ]
        }
    }

# Sample edge 3
_TEST_EDGES_3 = {
       "edge_1": {
           "subject": "PMID:11156626",
           "predicate": "biolink:contributor",
           "object": "ORCID:0000-0002-4447-5978",
           "attributes": [
                {
                    "attribute_type_id": "biolink:primary_knowledge_source",
                    "value": "infores:automat-text-mining-provider"
                }
            ]
        }
    }

_TEST_KG_3 = {
    'nodes': _TEST_NODES_2,
    'edges': _TEST_EDGES_3
}

_TEST_RESULTS_2 = [
        {
            "node_bindings": {
                "paper": [{"id": "PMID:11156626"}],
                "author": [{"id": "ORCID:0000-0002-4447-5978"}]
            },
            "edge_bindings": {
                "citation": [{"id": "edge1"}]
            }
        }
    ]


@pytest.mark.parametrize(
    "query",
    [
        (   # Query 0 - Completely empty Response.Message
            {
                "message": {

                }
            },
            None,
            None,
            None,
            None,
            # "Validate TRAPI Response: ERROR - Response returned an empty Message Query Graph!"
            "error.trapi.response.message.empty"
        ),
        (   # Query 1 - Response.Message also devoid of content, missing QGraph trapped first....
            {
                "message": {
                    "knowledge_graph": None,
                    "results": None
                }
            },
            None,
            None,
            None,
            None,
            # "Validate TRAPI Response: ERROR - TRAPI Message is missing its Query Graph!"
            "error.trapi.response.query_graph.missing"
        ),
        (   # Query 2 - Response.Message also devoid of content, null QGraph trapped first....
            {
                "message": {
                    "query_graph": None,
                    "knowledge_graph": None,
                    "results": None
                }
            },
            None,
            None,
            None,
            None,
            # "Validate TRAPI Response: ERROR - Response returned an null or empty Message Query Graph!"
            "error.trapi.response.query_graph.empty"
        ),
        (
            # Query 3 - Partly empty Response.Message with a modest but
            #           workable query graph? Missing KG trapped next?
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    # "knowledge_graph": None,
                    "results": None
                }
            },
            None,
            None,
            None,
            None,
            # "Validate TRAPI Response: ERROR - TRAPI Message is missing its Knowledge Graph component?"
            "error.trapi.response.knowledge_graph.missing"
        ),
        (
            # Query 4 - Partly empty Response.Message with a modest
            #           but workable query graph? Empty KG trapped next?
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": None,
                    "results": None
                }
            },
            None,
            None,
            None,
            None,
            # "Validate TRAPI Response: WARNING - Response returned an empty Message Knowledge Graph?"
            "warning.response.knowledge_graph.empty"
        ),
        (
            # Query 5 - Partly empty Response.Message with a modest but workable
            #           query and knowledge graphs? Missing Results detected next?
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    # "results": None
                }
            },
            None,
            None,
            None,
            None,
            # "Validate TRAPI Response: ERROR - TRAPI Message is missing its Results component!"
            "error.trapi.response.results.missing"
        ),
        (
            # Query 6 - Partly empty Response.Message with a modest but workable query and
            #           knowledge graphs? Null valued Results detected next - just issue a warning?
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": None
                }
            },
            None,
            None,
            None,
            None,
            # "Validate TRAPI Response: WARNING -Response returned empty Message.results?"
            "warning.response.results.empty"
        ),
        (
            # Query 7 - Partly empty Response.Message with a modest but workable
            #           query and knowledge graphs? Non-array Results detected next?
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": {"invalid results"}
                }
            },
            None,
            None,
            None,
            None,
            # "Validate TRAPI Response: ERROR - the 'Response.Message.Results' field
            # is not TRAPI schema validated since it has the wrong format!"
            "error.trapi.validation"
        ),
        (
            # Query 8 - Partly empty Response.Message with a modest but workable query and
            #           knowledge graphs? Empty Results detected next - just issue a warning?
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": []
                }
            },
            None,
            None,
            None,
            None,
            # "Validate TRAPI Response: ERROR - Response returned empty Message.results?"
            "warning.response.results.empty"
        ),
        (
            # Query 9 - Full Message, without 'sources' and 'strict_validation': False - should pass?
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                }
            },
            None,
            None,
            None,
            None,
            ""
        ),
        (
            # Query 10 - Full Message, with strict validation - still passes
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                }
            },
            None,
            None,
            None,
            True,
            ""
        ),
        (
            # Query 11 - Full Message, with strict validation and non-null sources that match
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                }
            },
            None,
            None,
            {
                "ara_source": None,
                "kp_source": "infores:hmdb",
                "kp_source_type": "primary"
            },
            True,
            ""
        ),
        (
            # Query 12 - Full Message, with strict validation and a non-null kp_source_type that doesn't match
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                }
            },
            None,
            None,
            {
                "ara_source": None,
                "kp_source": "infores:molepro",
                "kp_source_type": "primary"
            },
            True,
            "warning.knowledge_graph.edge.provenance.kp.missing"
        ),
        (
            # Query 13 - Full Message, with strict validation and a non-null ara_source that doesn't match
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                }
            },
            None,
            None,
            {
                "ara_source": "infores:aragorn",
                "kp_source": "infores:hmdb",
                "kp_source_type": "primary"
            },
            True,
            "warning.knowledge_graph.edge.provenance.ara.missing"
        ),
        (
            # Query 14 - Full Message, with strict validation and a non-null sources data that matches
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                }
            },
            None,
            None,
            {
                "ara_source": "infores:molepro",
                "kp_source": "infores:hmdb",
                "kp_source_type": "primary"
            },
            True,
            ""
        ),
        (
            # Query 15 - Full Message, with strict validation and a non-null sources KP that matches
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                }
            },
            None,
            None,
            {
                "ara_source": None,
                "kp_source": "infores:molepro",
                "kp_source_type": "aggregator"
            },
            True,
            ""
        ),
        (
            # Query 16 - Full Message, with strict validation and a non-null kp_source_type results in missing primary
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_2,
                    "results": _TEST_RESULTS_1
                }
            },
            None,
            None,
            {
                "ara_source": None,
                "kp_source": "infores:molepro",
                "kp_source_type": "aggregator"
            },
            True,
            "warning.knowledge_graph.edge.provenance.missing_primary"
        ),
        (
            # Query 17 - Full Message, with non-strict validation
            {
                "message": {
                    "query_graph": _TEST_QG_2,
                    "knowledge_graph": _TEST_KG_3,
                    "results": _TEST_RESULTS_2
                }
            },
            None,
            None,
            None,
            False,
            ""
        ),
        (
            # Query 18 - Full Message, WITH strict validation - abstract category?
            {
                "message": {
                    "query_graph": _TEST_QG_2,
                    "knowledge_graph": _TEST_KG_3,
                    "results": _TEST_RESULTS_2
                }
            },
            None,
            None,
            None,
            True,
            "error.query_graph.node.category.abstract"
        ),
        (
            # Query 19 - Full Message, WITH strict validation - abstract predicate?
            {
                "message": {
                    "query_graph": _TEST_QG_2,
                    "knowledge_graph": _TEST_KG_3,
                    "results": _TEST_RESULTS_2
                }
            },
            None,
            None,
            None,
            True,
            "error.query_graph.edge.predicate.abstract"
        ),
        (
            # Query 20 - Valid full Message, under strict validation.
            #            Message is valid, but the 'workflow' field is not an array?
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                },
                "workflow": "workflows-not-an-array"
            },
            None,
            None,
            None,
            True,
            # "Validate TRAPI Response: ERROR - TRAPI schena error: the 'workflow' field must be an array"
            "error.trapi.validation"
        ),
        (
            # Query 21 - Valid full Message, under strict validation.
            #            Message is valid, the 'workflow' field is an array,
            #            but the single list entry is an invalid workflow spec?
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                },
                "workflow": ["not-a-valid-workflow-spec"]
            },
            None,
            None,
            None,
            True,
            # "Validate TRAPI Response: ERROR - TRAPI schena error: the 'workflow' field must be an array of
            # a 'workflow' JSON objects, with contents as defined by the workflow schema.
            "error.trapi.validation"
        ),
        (
            # Query 22 - Valid full Message, under strict validation.
            #            Message is valid, the 'workflow' field is an array,
            #            but the single list entry is in the workflow schema
            #            and has at least the one required field 'id'
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                },
                "workflow": [{"id": "annotate"}]
            },
            None,
            None,
            None,
            True,
            ""   # this simple workflow spec should pass?
        ),
        (
            # Query 23 - Valid full Message, under strict validation. Message is valid, the 'workflow' field is array,
            #            but the single list entry is an elaborated 'real world' workflow spec,
            #            but one entry overlay_compute_ngd is incomplete - doesn't fully validate!
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                },
                "workflow": [
                    {  # 'real' world workflow spec from E. Deutsch
                      "id": "fill",
                      "parameters": {
                        "allowlist": [
                          "infores-rtx-kg2"
                        ]
                      }
                    },
                    {
                      "id": "bind"
                    },
                    {
                      "id": "overlay_compute_ngd",
                      "parameters": {
                        "virtual_relation_label": "ngd1"
                      }
                    },
                    {
                      "id": "score"
                    },
                    {
                      "id": "complete_results"
                    }
                ]
            },
            None,
            None,
            None,
            True,
            # "Validate TRAPI Response: ERROR - TRAPI schema validation error: the 'workflow'
            # field entry overlay_compute_ngd is missing a required parameter 'qnodes_keys'
            "error.trapi.validation"
        ),
        (
            # Query 24 - Valid full Message, under strict validation. Message is valid, the 'workflow' field is array,
            #            but the single list entry is an elaborated 'real world' workflow spec
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                },
                "workflow": [
                    {  # 'real' world workflow spec from E. Deutsch
                      "id": "fill",
                      "parameters": {
                        "allowlist": [
                          "infores-rtx-kg2"
                        ]
                      }
                    },
                    {
                      "id": "bind"
                    },
                    {
                      "id": "overlay_compute_ngd",
                      "parameters": {
                        "virtual_relation_label": "ngd1",
                        "qnode_keys": ["type-2 diabetes", "drug"]
                      }
                    },
                    {
                      "id": "score"
                    },
                    {
                      "id": "complete_results"
                    }
                ]
            },
            None,
            None,
            None,
            True,
            ""   # this simple workflow spec should pass?
        ),
        (
            # Query 25 - Valid full Message, under strict validation. Message is valid,
            #            the 'workflow' field is an array, but runner_parameters is None.
            #            This is technically invalid but we have a code patch which should filter it out (for now)
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                },
                "workflow": [
                    {
                        "id": "lookup",
                        "runner_parameters": None,
                        "parameters": None
                    }
                ]
            },
            None,
            None,
            None,
            True,
            ""   # this filtered workflow spec should pass
        )
    ]
)
def test_check_biolink_model_compliance_of_trapi_response(query: Tuple[Union[Dict, str]]):
    validator: TRAPIResponseValidator = TRAPIResponseValidator(
        trapi_version=query[1],
        biolink_version=query[2],
        sources=query[3],
        strict_validation=query[4]
    )
    validator.check_compliance_of_trapi_response(response=query[0])
    check_messages(validator, query[5], no_errors=True)
