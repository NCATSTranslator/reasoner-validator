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

PRE_TRAPI_1_4_0 = "1.3.0"

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
            ],
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
           ],
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
           ],
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


# Sample edge 2
_TEST_EDGES_4 = {
       "edge_1": {
           "subject": "NCBIGene:29974",
           "predicate": "biolink:physically_interacts_with",
           "object": "PUBCHEM.COMPOUND:597",
           "attributes": [
               {
                   "attribute_type_id": "biolink:aggregator_knowledge_source",
                   "value": "infores:molepro"
               },
               {
                   "attribute_type_id": "biolink:primary_knowledge_source",
                   "value": "infores:automat-text-mining-provider"
               },
               {
                   "attribute_type_id": "biolink:primary_knowledge_source",
                   "value": "infores:hmdb"
               }
           ],
        }
    }


_TEST_KG_4 = {
    'nodes': _TEST_NODES_1,
    'edges': _TEST_EDGES_4
}


@pytest.mark.parametrize(
    "query",
    [
        (   # Query 0 - No 'workflow' key
            {},
        ),
        (   # Query 1 - Null 'workflow' key value
            {
                'workflow': None
            },
        ),
        (  # Query 2 - Null 'workflow' key list
            {
                'workflow': []
            },
        ),
        (  # Query 3 - 'runner_parameters' is Null
            {
                'workflow': [
                    {
                        'runner_parameters': None,
                        'id': 'sort_results_score',
                        'parameters': {"ascending_or_descending": "ascending"}
                    }
                ]
            },
        ),
        (  # Query 4 - 'parameters' is Null
            {
                'workflow': [
                    {'runner_parameters': {'allowlist': ["infores:aragorn"]}, 'id': 'lookup', 'parameters': None}
                ]
            },
        ),
        (  # Query 5 - both 'parameters' and 'runner_parameters' are Null
            {
                'workflow': [
                    {'runner_parameters': None, 'id': 'lookup', 'parameters': None}
                ]
            },
        )
    ]
)
def test_sanitize_trapi_query(query: Tuple):
    validator: TRAPIResponseValidator = TRAPIResponseValidator()
    response: Dict = validator.sanitize_trapi_query(response=query[0])
    # assert response == query[1]


NUM_SAMPLE_NODES = 5

SAMPLE_NODES: Dict = dict()
for node_id in range(1, NUM_SAMPLE_NODES):
    SAMPLE_NODES[f"n{node_id}"] = dict()

SAMPLE_EDGES: Dict = dict()
for subject_id in SAMPLE_NODES:
    for object_id in SAMPLE_NODES:
        if subject_id != object_id:
            SAMPLE_EDGES[f"e{subject_id}{object_id}"] = {
                "subject": subject_id,
                "predicate": "biolink:related_to",
                "object": object_id
            }

TEST_GRAPH: Dict = {
    "nodes": SAMPLE_NODES,
    "edges": SAMPLE_EDGES
}


@pytest.mark.parametrize(
    "query",
    [
        (   # Query 0 - unlimited sample whole graph
            0,  # edges_limit
            len(SAMPLE_NODES),  # number of nodes returned
            len(SAMPLE_EDGES)   # number of edges returned
        ),
        (   # Query 1 - sample just 2 edges
            2,  # edges_limit
            3,  # number of nodes returned
            2   # number of edges returned
        ),
        (   # Query 2 - sample just edge_value is negative number (functionally equivalent to zero)
            -1,  # edges_limit
            len(SAMPLE_NODES),  # number of nodes returned
            len(SAMPLE_EDGES)   # number of edges returned
        )
    ]
)
def test_sample_graph(query: Tuple[int, int, int]):
    validator: TRAPIResponseValidator = TRAPIResponseValidator()
    kg_sample: Dict = validator.sample_graph(graph=TEST_GRAPH, edges_limit=query[0])
    assert kg_sample
    assert len(kg_sample["nodes"]) == query[1]
    assert len(kg_sample["edges"]) == query[2]


@pytest.mark.parametrize(
    "query",
    [
        (   # Query 0 - Completely empty Response.Message
            {
                "message": {

                }
            },
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            # Query 16 - Full Message, with strict validation and
            #            a non-null kp_source_type results in missing primary
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_2,
                    "results": _TEST_RESULTS_1
                }
            },
            PRE_TRAPI_1_4_0,  # trapi_version
            None,
            {
                "ara_source": None,
                "kp_source": "infores:molepro",
                "kp_source_type": "aggregator"
            },
            True,
            "error.knowledge_graph.edge.provenance.missing_primary"
        ),
        (
            # Query 17 - Full Message, with strict validation and
            #            non-null kp_source_type results, has multiple primary knowledge sources
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_4,
                    "results": _TEST_RESULTS_1
                }
            },
            PRE_TRAPI_1_4_0,  # trapi_version
            None,
            {
                "ara_source": None,
                "kp_source": "infores:molepro",
                "kp_source_type": "aggregator"
            },
            True,
            "warning.knowledge_graph.edge.provenance.multiple_primary"
        ),
        (
            # Query 18 - Full Message, with non-strict validation.
            #            Both knowledge graph nodes have 'mixin' categories,
            #            the list of categories for knowledge graphs
            #            must have at least one concrete category,
            #            hence, a validation error is now reported:
            {
                "message": {
                    "query_graph": _TEST_QG_2,
                    "knowledge_graph": _TEST_KG_3,
                    "results": _TEST_RESULTS_2
                }
            },
            PRE_TRAPI_1_4_0,  # trapi_version
            None,
            None,
            False,
            "error.knowledge_graph.node.categories.not_concrete"
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
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
            PRE_TRAPI_1_4_0,  # trapi_version
            None,
            None,
            True,
            ""   # this simple workflow spec should pass?
        ),
        (
            # Query 25 - Valid full Message, under strict validation. Message is valid,
            #            the 'workflow' field is an array, but runner_parameters is None.
            #            This is technically invalid, but we have a code patch which should filter it out (for now)
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
            PRE_TRAPI_1_4_0,  # trapi_version
            None,
            None,
            True,
            ""   # this filtered workflow spec should pass
        )
    ]
)
def test_check_biolink_model_compliance_of_trapi_response(query: Tuple):
    validator: TRAPIResponseValidator = TRAPIResponseValidator(
        trapi_version=query[1],
        biolink_version=query[2],
        sources=query[3],
        strict_validation=query[4]
    )
    validator.check_compliance_of_trapi_response(response=query[0])
    check_messages(validator, query[5], no_errors=True)
