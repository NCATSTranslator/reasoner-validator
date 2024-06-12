"""
Unit tests for the generic (shared) components of the SRI Testing Framework
"""
from typing import List, Dict, Optional
from sys import stderr

import logging

from copy import deepcopy

import pytest

from dictdiffer import diff

from reasoner_validator.trapi import (
    TRAPI_1_3_0,
    TRAPI_1_4_2
)
from reasoner_validator.validator import TRAPIResponseValidator

from tests import (
    LATEST_TRAPI_RELEASE,
    LATEST_BIOLINK_MODEL_VERSION,
    PATCHED_140_SCHEMA_FILEPATH,
    SAMPLE_NODES_WITH_ATTRIBUTES,
    DEFAULT_KL_AND_AT_ATTRIBUTES
)
from tests.test_validation_report import check_messages


logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


@pytest.mark.parametrize(
    "identifier,find_aliases,code",
    [
        (   # Query 0 - Canonical namespace 'orphanet' CURIE, returns itself
            #           and another alias, without validation error
            "orphanet:33110",
            ["orphanet:33110", "MONDO:0011096"],
            ""
        ),
        (   # Query 1 - Input CURIE differs in namespace letter case from
            # the 'orphanet' lower case returned by NodeNormalization.
            # Returns itself, plus the identifier with canonical 'orphanet'
            # plus at least another alias, but with a validation warning
            "ORPHANET:33110",
            ["ORPHANET:33110", "orphanet:33110", "MONDO:0011096"],
            "warning.trapi.response.message.knowledge_graph.node.identifier.namespace.non_canonical"
        ),
        (   # Query 2 - only CURIEs can be resolved to aliases
            # but just logs a warning but returns the identifier
            "not-a-curie",
            None,
            "error.trapi.response.message.knowledge_graph.node.identifier.not_curie"
        ),
        (   # Query 3 - valid CURIE but Node Normalization
            # doesn't know anything about it, so just return itself
            "ncats.drug:9100L32L2N",
            ["ncats.drug:9100L32L2N"],
            "warning.trapi.response.message.knowledge_graph.node.identifier.no_aliases"
        ),
    ]
)
def test_get_aliases(identifier: str, find_aliases: Optional[List[str]], code: str):
    validator: TRAPIResponseValidator = TRAPIResponseValidator()
    aliases: Optional[List[str]] = validator.get_aliases(identifier)
    if find_aliases is not None:
        assert aliases is not None and identifier in aliases, "Original CURIE missing in aliases?"
        for alias in find_aliases:
            assert alias in aliases, f"Expected alias {alias} missing in aliases?"
    check_messages(validator, code)


TYPE_2_DIABETES_CURIE = "MONDO:0005148"
METFORMIN_CURIE = "RXCUI:1043563"

_TEST_QG_1 = {
    "nodes": {
        "type-2 diabetes": {"ids": [TYPE_2_DIABETES_CURIE]},
        "drug": {
            "categories": ["biolink:Drug"]
        }
    },
    "edges": {
        "treats": {
            "subject": "drug",
            "predicates": ["biolink:ameliorates_condition"],
            "object": "type-2 diabetes"
        }
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
            ] + DEFAULT_KL_AND_AT_ATTRIBUTES,
        }
    }

_TEST_KG_1 = {
    "nodes": SAMPLE_NODES_WITH_ATTRIBUTES,
    "edges": _TEST_EDGES_1
}


_TEST_RESULTS_1 = [
    {
        "node_bindings": {
            "type-2 diabetes": [{"id": TYPE_2_DIABETES_CURIE}],
            "drug": [{"id": METFORMIN_CURIE}]
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
    "nodes": SAMPLE_NODES_WITH_ATTRIBUTES,
    "edges": _TEST_EDGES_2
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
    "nodes": _TEST_NODES_2,
    "edges": _TEST_EDGES_3
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
    "nodes": SAMPLE_NODES_WITH_ATTRIBUTES,
    "edges": _TEST_EDGES_4
}

_TEST_KG_EDGE_SOURCES = [
    {
        "resource_id": "infores:chebi",
        "resource_role": "primary_knowledge_source",
        "upstream_resource_ids": []
    },
    {
        "resource_id": "infores:biothings-explorer",
        "resource_role": "aggregator_knowledge_source",
        "upstream_resource_ids": [
            "infores:chebi"
        ]
    },
    {
        "resource_id": "infores:molepro",
        "resource_role": "aggregator_knowledge_source",
        "upstream_resource_ids": [
            "infores:biothings-explorer"
        ]
    },
    {
        "resource_id": "infores:arax",
        "resource_role": "aggregator_knowledge_source",
        "upstream_resource_ids": [
            "infores:molepro"
        ]
    }
]

# From Implementation Guidelines circa June 2023
_TEST_TRAPI_1_4_2_FULL_SAMPLE = {
    "schema_version": "1.5.0",
    "message": {
        "query_graph": {
            "nodes": {
                "type-2 diabetes": {"ids": [TYPE_2_DIABETES_CURIE]},
                "drug": {"categories": ["biolink:Drug"]}
            },
            "edges": {
                "treats": {"subject": "drug", "predicates": ["biolink:ameliorates_condition"],
                           "object": "type-2 diabetes"}
            }
        },
        "knowledge_graph": {
            "nodes": {
                TYPE_2_DIABETES_CURIE: {"name": "type-2 diabetes", "categories": ["biolink:Disease"]},
                METFORMIN_CURIE: {"name": "metformin", "categories": ["biolink:Drug"]}
            },
            "edges": {
                "df87ff82": {
                    "subject": METFORMIN_CURIE,
                    "predicate": "biolink:ameliorates_condition",
                    "object": TYPE_2_DIABETES_CURIE,
                    "sources": _TEST_KG_EDGE_SOURCES
                }
            }
        },
        "auxiliary_graphs": {
            "a0": {
                "edges": [
                    "e02",
                    "e12"
                ]
            },
            "a1": {
                "edges": [
                    "extra_edge0"
                ]
            },
            "a2": {
                "edges": [
                    "extra_edge1"
                ]
            }
        },
        "results": [
            {
                "node_bindings": {
                    "type-2 diabetes": [{"id": TYPE_2_DIABETES_CURIE}],
                    "drug": [{"id": METFORMIN_CURIE}]
                },
                "analyses": [
                    {
                        "resource_id": "infores:ara0",
                        "edge_bindings": {"treats": [{"id": "df87ff82"}]},
                        "support_graphs": [],
                        "score": 0.7
                    }
                ]
            }
        ]
    }
}

_TEST_TRAPI_1_4_2_FULL_SAMPLE_WITHOUT_AUX_GRAPH = deepcopy(_TEST_TRAPI_1_4_2_FULL_SAMPLE)
_TEST_TRAPI_1_4_2_FULL_SAMPLE_WITHOUT_AUX_GRAPH["message"].pop("auxiliary_graphs")

_TEST_TRAPI_1_4_2_FULL_SAMPLE_WITH_SCHEMA_VERSION = deepcopy(_TEST_TRAPI_1_4_2_FULL_SAMPLE)
_TEST_TRAPI_1_4_2_FULL_SAMPLE_WITH_SCHEMA_VERSION["schema_version"] = "1.3.0"

_TEST_TRAPI_1_4_2_FULL_SAMPLE_WITH_BIOLINK_VERSION = {
    "biolink_version": "2.2.0",
    "message": {
        "query_graph": {
            "nodes": {
                "type-2 diabetes": {"ids": [TYPE_2_DIABETES_CURIE]},
                "drug": {"categories": ["biolink:Drug"]}
            },
            "edges": {
                "treats": {
                    "subject": "type-2 diabetes",
                    "predicates": ["biolink:treated_by"],
                    "object": "drug"
                }
            }
        },
        "knowledge_graph": {
            "nodes": {
                TYPE_2_DIABETES_CURIE: {"name": "type-2 diabetes", "categories": ["biolink:Disease"]},
                METFORMIN_CURIE: {"name": "metformin", "categories": ["biolink:Drug"]}
            },
            "edges": {
                "df87ff82": {
                    "subject": TYPE_2_DIABETES_CURIE,
                    "predicate": "biolink:treated_by",
                    "object": METFORMIN_CURIE,
                    "sources": _TEST_KG_EDGE_SOURCES
                }
            }
        },
        "auxiliary_graphs": {
            "a0": {
                "edges": [
                    "e02",
                    "e12"
                ]
            },
            "a1": {
                "edges": [
                    "extra_edge0"
                ]
            },
            "a2": {
                "edges": [
                    "extra_edge1"
                ]
            }
        },
        "results": [
            {
                "node_bindings": {
                    "type-2 diabetes": [{"id": TYPE_2_DIABETES_CURIE}],
                    "drug": [{"id": METFORMIN_CURIE}]
                },
                "analyses": [
                    {
                        "resource_id": "infores:ara0",
                        "edge_bindings": {"treats": [{"id": "df87ff82"}]},
                        "support_graphs": [],
                        "score": 0.7
                    }
                ]
            }
        ]
    }
}

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


# this unit test checks that the original response object is returned verbatim
def test_conservation_of_response_object():
    validator: TRAPIResponseValidator = TRAPIResponseValidator()
    input_response = deepcopy(_TEST_TRAPI_1_4_2_FULL_SAMPLE)
    reference_response = deepcopy(_TEST_TRAPI_1_4_2_FULL_SAMPLE)
    assert input_response == reference_response
    validator.check_compliance_of_trapi_response(response=input_response)
    assert not list(diff(input_response, reference_response))


@pytest.mark.parametrize(
    "trapi_version,outcome",
    [
        ("1.3.0", False),
        ("1.4.0", True),
        ("1.4.2", True),
        ("1.5.0-beta", True),
        ("1.5.0", True),

        # since the latest default (as of test creation)
        # is 1.5 something, then 'None' should also be true
        (None, True)
    ]
)
def test_is_trapi_1_4_or_later(trapi_version: Optional[str], outcome: bool):
    validator: TRAPIResponseValidator = TRAPIResponseValidator(trapi_version=trapi_version)
    assert validator.is_trapi_1_4_or_later() is outcome


@pytest.mark.parametrize(
    "edges_limit,number_of_nodes_returned,number_of_edges_returned",
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
def test_sample_graph(edges_limit: int, number_of_nodes_returned: int, number_of_edges_returned: int):
    validator: TRAPIResponseValidator = TRAPIResponseValidator()
    kg_sample: Dict = validator.sample_graph(graph=TEST_GRAPH, edges_limit=edges_limit)
    assert kg_sample
    assert len(kg_sample["nodes"]) == number_of_nodes_returned
    assert len(kg_sample["edges"]) == number_of_edges_returned


@pytest.mark.parametrize(
    "response,trapi_version,biolink_version,target_provenance,strict_validation,code",
    [
        (   # Query 0 - Completely empty Response.Message
            {
                "message": {

                }
            },
            TRAPI_1_3_0,
            None,
            None,
            False,
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
            TRAPI_1_3_0,
            None,
            None,
            False,
            # "Validate TRAPI Response: ERROR - TRAPI Message is missing its Query Graph!"
            "error.trapi.response.message.query_graph.missing"
        ),
        (   # Query 2 - Response.Message also devoid of content, null QGraph trapped first....
            {
                "message": {
                    "query_graph": None,
                    "knowledge_graph": None,
                    "results": None
                }
            },
            TRAPI_1_3_0,
            None,
            None,
            False,
            # "Validate TRAPI Response: ERROR - Response returned a null or empty Message Query Graph!"
            "error.trapi.response.message.query_graph.empty"
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
            TRAPI_1_3_0,
            None,
            None,
            False,
            # "Validate TRAPI Response: ERROR - TRAPI Message is missing its Knowledge Graph component?"
            "error.trapi.response.message.knowledge_graph.missing"
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
            TRAPI_1_3_0,
            None,
            None,
            False,
            # "Validate TRAPI Response: WARNING - Response returned an empty Message Knowledge Graph?"
            "warning.trapi.response.message.knowledge_graph.empty"
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
            TRAPI_1_3_0,
            None,
            None,
            False,
            # "Validate TRAPI Response: ERROR - TRAPI Message is missing its Results component!"
            "error.trapi.response.message.results.missing"
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
            TRAPI_1_3_0,
            None,
            None,
            False,
            # "Validate TRAPI Response: WARNING -Response returned empty Message.results?"
            "warning.trapi.response.message.results.empty"
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
            TRAPI_1_3_0,
            None,
            None,
            False,
            # "Validate TRAPI Response: ERROR - Response returned a non-array Message.Results!
            "error.trapi.response.message.results.not_array"
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
            TRAPI_1_3_0,
            None,
            None,
            False,
            # "Validate TRAPI Response: ERROR - Response returned empty Message.results?"
            "warning.trapi.response.message.results.empty"
        ),
        (
            # Query 9 - Full Message, without "sources" and "strict_validation": False - should pass?
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                }
            },
            TRAPI_1_3_0,
            None,
            None,
            False,
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
            TRAPI_1_3_0,
            None,
            None,
            True,
            ""
        ),
        (
            # Query 11 - Full Message, with "strict validation" and non-null sources" that match
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                }
            },
            TRAPI_1_3_0,
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
            TRAPI_1_3_0,
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
            TRAPI_1_3_0,
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
            # Query 14 - Full Message, with "strict validation" and a non-null "sources" data that matches
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                }
            },
            TRAPI_1_3_0,
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
            # Query 15 - Full Message, with "strict validation" and a non-null "sources" KP that matches
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                }
            },
            TRAPI_1_3_0,
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
            TRAPI_1_3_0,
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
            #            non-null kp_source_type results, has multiple "primary knowledge sources"
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_4,
                    "results": _TEST_RESULTS_1
                }
            },
            TRAPI_1_3_0,
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
            #            Both knowledge graph nodes have "mixin" categories,
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
            TRAPI_1_3_0,
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
            TRAPI_1_3_0,
            None,
            None,
            True,
            "error.query_graph.edge.predicate.abstract"
        ),
        (
            # Query 20 - Valid full Message, under strict validation.
            #            Message is valid, but the "workflow" field is not an array?
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                },
                "workflow": "workflows-not-an-array"
            },
            TRAPI_1_3_0,
            None,
            None,
            True,
            # "Validate TRAPI Response: ERROR - TRAPI schema error: the "workflow" field must be an array"
            "critical.trapi.validation"
        ),
        (
            # Query 21 - Valid full Message, under strict validation.
            #            Message is valid, the "workflow" field is an array,
            #            but the single list entry is an invalid workflow spec?
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                },
                "workflow": ["not-a-valid-workflow-spec"]
            },
            TRAPI_1_3_0,
            None,
            None,
            True,
            # Validate TRAPI Response: ERROR - TRAPI schema error: the "workflow" field must be an array of
            # a "workflow" JSON objects, with contents as defined by the workflow schema.
            "critical.trapi.validation"
        ),
        (
            # Query 22 - Valid full Message, under strict validation.
            #            Message is valid, the "workflow" field is an array,
            #            but the single list entry is in the workflow schema
            #            and has at least the one required field "id"
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                },
                "workflow": [{"id": "annotate"}]
            },
            TRAPI_1_3_0,
            None,
            None,
            True,
            ""   # this simple workflow spec should pass?
        ),
        (
            # Query 23 - Valid full Message, under strict validation. Message is valid, the "workflow" field is array,
            #            but the single list entry is an elaborated "real world" workflow spec,
            #            but one entry overlay_compute_ngd is incomplete - doesn't fully validate!
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                },
                "workflow": [
                    {  # "real" world workflow spec from E. Deutsch
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
            TRAPI_1_3_0,
            None,
            None,
            True,
            # "Validate TRAPI Response: ERROR - TRAPI schema validation error: the "workflow"
            # field entry overlay_compute_ngd is missing a required parameter "qnodes_keys"
            "critical.trapi.validation"
        ),
        (
            # Query 24 - Valid full Message, under strict validation. Message is valid, the "workflow" field is array,
            #            but the single list entry is an elaborated "real world" workflow spec
            {
                "message": {
                    "query_graph": _TEST_QG_1,
                    "knowledge_graph": _TEST_KG_1,
                    "results": _TEST_RESULTS_1
                },
                "workflow": [
                    {  # "real" world workflow spec from E. Deutsch
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
            TRAPI_1_3_0,
            None,
            None,
            True,
            ""   # this simple workflow spec should pass?
        ),
        (
            # Query 25 - Valid full Message, under strict validation. Message is valid,
            #            the "workflow" field is an array, but runner_parameters is None.
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
            TRAPI_1_3_0,
            None,
            None,
            True,
            # TRAPI Response workflow sanitization restored - this should pass
            ""
        ),
        (   # Query 26 - We throw a full TRAPI JSON example here (taken directly from the
            #            TRAPI implementation guidelines...) just for fun and profit
            _TEST_TRAPI_1_4_2_FULL_SAMPLE,
            TRAPI_1_4_2,
            None,
            None,
            True,
            ""   # this filtered workflow spec should pass
        ),
        (   # Query 27 - We throw a full TRAPI JSON example here (taken directly from the TRAPI implementation
            #            guidelines...) but add the 'schema_version' just for fun and profit
            _TEST_TRAPI_1_4_2_FULL_SAMPLE_WITH_SCHEMA_VERSION,
            None,
            "4.1.4",
            None,
            True,
            "critical.trapi.validation"   # trying to validate a 1.4.2 schema against 1.3.0 will fail!
        ),
        (   # Query 28 - We throw a full TRAPI JSON example here (taken directly from the TRAPI implementation
            #            guidelines...) but explicitly specify the 'biolink_version == 2.5.8' just for fun and profit
            _TEST_TRAPI_1_4_2_FULL_SAMPLE_WITH_BIOLINK_VERSION,
            TRAPI_1_4_2,
            None,
            None,
            True,
            # Validation with 2.4.8 generates a warning
            "warning.knowledge_graph.edge.predicate.non_canonical"
        )
    ]
)
def test_check_biolink_model_compliance_of_trapi_response(
        response: Dict,
        trapi_version: str,
        biolink_version: str,
        target_provenance: Dict,
        strict_validation: bool,
        code
):
    validator: TRAPIResponseValidator = TRAPIResponseValidator(
        trapi_version=trapi_version,
        biolink_version=biolink_version,
        strict_validation=strict_validation,
        target_provenance=target_provenance
    )
    validator.check_compliance_of_trapi_response(response=response)
    check_messages(validator, code, no_errors=True)


@pytest.mark.parametrize(
    "response,trapi_version,biolink_version,sources,strict_validation,code",
    [
        (   # Query 0 - Completely empty Response.Message
            {
                "message": {

                }
            },
            TRAPI_1_3_0,
            None,
            None,
            False,
            ""
        ),
        (   # Query 1 - Response.Message also devoid of content, missing QGraph trapped first....
            {
                "message": {
                    "knowledge_graph": None,
                    "results": None
                }
            },
            TRAPI_1_3_0,
            None,
            None,
            False,
            ""
        ),
        (   # Query 2 - Response.Message also devoid of content, null QGraph trapped first....
            {
                "message": {
                    "query_graph": None,
                    "knowledge_graph": None,
                    "results": None
                }
            },
            TRAPI_1_3_0,
            None,
            None,
            False,
            ""
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
            TRAPI_1_3_0,
            None,
            None,
            False,
            ""
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
            TRAPI_1_3_0,
            None,
            None,
            False,
            ""
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
            TRAPI_1_3_0,
            None,
            None,
            False,
            ""
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
            TRAPI_1_3_0,
            None,
            None,
            False,
            ""
        ),
        (
            # Query 7 - Full fake sample Response from TRAPI 1.4.0 implementation guidelines
            _TEST_TRAPI_1_4_2_FULL_SAMPLE,
            # 25 June 2023 1.4.0 trapi_version with
            # defective auxiliary_graphs schema model
            # now temporarily patched?
            TRAPI_1_4_2,
            None,
            None,
            False,
            ""  # would be a "critical.trapi.validation" if the schema was unpatched
        ),
        (
            # Query 8 - Full fake sample Response from TRAPI 1.4.0 implementation guidelines
            _TEST_TRAPI_1_4_2_FULL_SAMPLE,
            # patched 1.4.0 test schema - fixed critical
            # TRAPI schema parsing error with auxiliary_graphs
            PATCHED_140_SCHEMA_FILEPATH,
            None,
            None,
            False,
            ""
        ),
        (
            # Query 9 - Sample Response from TRAPI 1.4.0 implementation guidelines without auxiliary_graph
            _TEST_TRAPI_1_4_2_FULL_SAMPLE_WITHOUT_AUX_GRAPH,
            # 25 June 2023 1.4.0 trapi_version with
            # defective auxiliary_graphs schema model
            TRAPI_1_4_2,
            None,
            None,
            False,
            ""  # nullable: true allows this outcome
        ),
        (
            # Query 10 - Sample Response from TRAPI 1.4.0 implementation guidelines without auxiliary_graph
            _TEST_TRAPI_1_4_2_FULL_SAMPLE_WITHOUT_AUX_GRAPH,
            # patched 1.4.0 test schema - fixed critical
            # TRAPI schema parsing error with auxiliary_graphs
            PATCHED_140_SCHEMA_FILEPATH,
            None,
            None,
            False,
            ""  # should still work if nullable: true
        )
    ]
)
def test_check_biolink_model_compliance_of_trapi_response_suppressing_empty_data_warnings(
        response, trapi_version, biolink_version, sources, strict_validation, code
):
    validator: TRAPIResponseValidator = TRAPIResponseValidator(
        trapi_version=trapi_version,
        biolink_version=biolink_version,
        target_provenance=sources,
        strict_validation=strict_validation,
        suppress_empty_data_warnings=True
    )
    validator.check_compliance_of_trapi_response(response=response)
    check_messages(validator, code, no_errors=True)


_TEST_TRAPI_1_4_2_FULL_SAMPLE_WITH_REPORTABLE_ERRORS = deepcopy(_TEST_TRAPI_1_4_2_FULL_SAMPLE)
sample_message = _TEST_TRAPI_1_4_2_FULL_SAMPLE_WITH_REPORTABLE_ERRORS["message"]
sample_qgraph = sample_message["query_graph"]
sample_kg = sample_message["knowledge_graph"]
sample_kg_node_missing_category = sample_kg["nodes"][TYPE_2_DIABETES_CURIE].pop("categories")
sample_kg_edge_missing_node_subject = sample_kg["edges"]["df87ff82"].pop("subject")
sample_kg_edge_abstract_predicate = sample_kg["edges"]["df87ff82"]["predicate"] = "biolink:not_a_predicate"


@pytest.mark.parametrize(
    "response",
    [
        _TEST_TRAPI_1_4_2_FULL_SAMPLE,
        _TEST_TRAPI_1_4_2_FULL_SAMPLE_WITH_REPORTABLE_ERRORS
    ]
)
def test_dump_report_of_biolink_model_compliance_of_trapi_response_with_errors(response: Dict):
    validator: TRAPIResponseValidator = TRAPIResponseValidator()
    validator.check_compliance_of_trapi_response(response=response)
    validator.dump(file=stderr)
    print("\n"+"="*80+"\n", file=stderr)


@pytest.mark.parametrize(
    "source_categories,target_categories,category_matched",
    [
        (   # query 0 - empty lists don't have anything to match?
            [], [], None
        ),
        (   # query 1 - exact matches should be true
            ["biolink:Gene"],
            ["biolink:Gene"],
            "biolink:Gene"
        ),
        (   # query 2 - biolink:Protein is **not** directly matched in the
            #           'source' hierarchy (even though its parents could overlap)
            ["biolink:Gene"],
            ["biolink:Drug"],
            None
        ),
        (   # query 3 - but a 'target' category list with at least one exact
            #           match of category to source will also be matched,
            #           even if other target entries don't match
            ["biolink:Gene"],
            ["biolink:Gene",
             "biolink:Drug"],
            "biolink:Gene"
        ),
        (   # query 4 - 'target' category matches at least one
            #           parent of the list of 'source' categories
            ["biolink:Gene"],
            ["biolink:BiologicalEntity"],
            "biolink:BiologicalEntity"
        ),
        (   # query 5 - a 'target' category list matches at least
            #           one match to a parent of the list of the
            #           'source' categories, will be matched,
            #           even if other target entries don't match
            #
            ["biolink:Gene"],
            ["biolink:BiologicalEntity", "biolink:Drug"],
            "biolink:BiologicalEntity"
        )
    ]
)
def test_category_matched(
        source_categories: List[str],
        target_categories: List[str],
        category_matched: Optional[str]
):
    validator = TRAPIResponseValidator()
    assert validator.category_matched(
        source_categories,
        target_categories,
    ) == category_matched


@pytest.mark.parametrize(
    "sample_node_id,subject_category,node_details,output_category,code",
    [
        (   # Query 0 - Exact match between knowledge graph node
            #           categories and target test case category
            "CHEBI:6801",
            "biolink:Drug",
            {"name": "metformin", "categories": ["biolink:Drug"]},
            "biolink:Drug",
            ""
        ),
        (   # Query 1 - Knowledge graph node details lack a
            #           'categories' field, so cannot match it
            TYPE_2_DIABETES_CURIE,
            "biolink:Disease",
            {"name": "type-2 diabetes"},
            None,
            "error.trapi.response.message.knowledge_graph.node.category.unmatched"
        ),

        (
            # Query 2 - No knowledge graph node category overlaps with the
            #           test case category (or any parent category thereof)
            "NCBIGene:7486",  # WRN RecQ like helicase [ Homo sapiens (human) ]
            "biolink:Gene",
            {"name": "WRN", "categories": ["biolink:Drug"]},
            None,
            "error.trapi.response.message.knowledge_graph.node.category.unmatched"
        ),
        (
            # Query 3 - At least one knowledge graph node category overlaps with at least a
            #           parent (ancestor) of the test case category (but is deemed "imprecise")
            "NCBIGene:7486",  # WRN RecQ like helicase [ Homo sapiens (human) ]
            "biolink:Gene",
            {"name": "WRN", "categories": ["biolink:BiologicalEntity"]},
            "biolink:BiologicalEntity",
            "warning.trapi.response.message.knowledge_graph.node.category.imprecise"
        ),
        (
            # Query 4 - Knowledge graph node 'categories' and test case category don't overlap
            "NCBIGene:7486",  # WRN RecQ like helicase [ Homo sapiens (human) ]
            "biolink:BiologicalEntity",
            {"name": "WRN", "categories": ["biolink:Gene"]},
            "biolink:BiologicalEntity",
            ""
        )
    ]
)
def test_testcase_node_category_found(
        sample_node_id: str,
        subject_category: str,
        node_details: Dict,
        output_category: Optional[str],
        code: str
):
    # should work for both kinds of targets,
    # but here, we just test 'subject'. We also
    # just use one fixed 'node_id' and the
    # distinct parametric tests are only varied with
    # respect to testcase and node_details categories
    validator = TRAPIResponseValidator(
        trapi_version=LATEST_TRAPI_RELEASE,
        biolink_version=LATEST_BIOLINK_MODEL_VERSION
    )
    testcase: Dict = {
        "idx": 0,
        'subject_id': subject_id,
        "subject_category": subject_category,
    }
    category: Optional[str] = validator.testcase_node_category_found(
            "subject",
            sample_node_id,
            testcase,
            node_details
    )
    assert category == output_category
    check_messages(validator, code)


@pytest.mark.skip(reason="Incomplete test")
def test_testcase_node_found():
    validator = TRAPIResponseValidator(
        trapi_version=LATEST_TRAPI_RELEASE,
        biolink_version=LATEST_BIOLINK_MODEL_VERSION
    )
    #     def testcase_node_found(
    #             self,
    #             target: str,
    #             target_id_aliases: List[str],
    #             testcase: Dict,
    #             nodes: Dict
    #     ) -> Optional[Tuple[str, str, Optional[str]]]:
    target: str = ""
    target_id_aliases: List[str] = []
    testcase: Dict = {}
    nodes: Dict = {}
    validator.testcase_node_found(target, target_id_aliases, testcase, nodes)


@pytest.mark.parametrize(
    "testcase,response",
    [
        (dict(), {"empty": "nonsense"}),
        ({"empty": "nonsense"}, dict()),
    ]
)
def test_empty_case_input_found_in_response(testcase, response):
    validator = TRAPIResponseValidator()
    with pytest.raises(AssertionError):
        validator.testcase_input_found_in_response(testcase, response)


#
# case: Dict parameter contains something like:
#
SAMPLE_TEST_CASE = {
    "idx": 0,
    "subject_id": TYPE_2_DIABETES_CURIE,
    "subject_category": "biolink:Disease",
    "predicate_id": 'biolink:treated_by',
    "object_id": METFORMIN_CURIE,
    "object_category": "biolink:Drug"
}
#
# the contents for which ought to be returned in
# the TRAPI Knowledge Graph, with a Result mapping?
#
SAMPLE_QUERY_GRAPH = {
    "nodes": {
        "diabetes mellitus": {
            "ids": ["MONDO:0005015"]  # generic 'diabetes mellitus' MONDO term
        },
        "drug": {
            "categories": ["biolink:Drug"]
        }
    },
    "edges": {
        "treated_by": {
            "subject": "diabetes mellitus",
            "predicates": ["biolink:treated_by"],
            "object": "drug"
        }
    }
}

SAMPLE_TEST_NODES = {
    TYPE_2_DIABETES_CURIE: {"name": "type-2 diabetes", "categories": ["biolink:Disease"]},
    METFORMIN_CURIE: {"name": "metformin", "categories": ["biolink:Drug"]}
}

SAMPLE_TEST_EDGES = {
    "df879999": {
        "subject": TYPE_2_DIABETES_CURIE,
        "predicate": "biolink:treated_by",
        "object": METFORMIN_CURIE
    }
}
SAMPLE_TEST_GRAPH = {
    "nodes": SAMPLE_TEST_NODES,
    "edges": SAMPLE_TEST_EDGES
}

SAMPLE_TEST_RESULTS = [
    {
        "node_bindings": {
            "diabetes mellitus": [
                {
                    "id": TYPE_2_DIABETES_CURIE,  # actually bound knowledge graph node is 'type 2 diabetes mellitus'
                    "query_id": "MONDO:0005015"   # QNode identifier is the MONDO parent concept of 'diabetes mellitus'
                }
            ],
            "drug": [{"id": METFORMIN_CURIE}]
        },
        "analyses": [
            {
                "resource_id": "infores:ara0",
                "edge_bindings": {
                    "treated_by": [
                        {"id": "df879999"}
                    ]
                },
                "support_graphs": [],
                "score": 0.7
            }
        ]
    }
]

SAMPLE_TEST_INCOMPLETE_RESULTS = [
    {
        "node_bindings": {
            "diabetes mellitus": [{"id": TYPE_2_DIABETES_CURIE}],
            "drug": [{"id": METFORMIN_CURIE}]
        },
        "analyses": [
            {
                "resource_id": "infores:ara0",
                # not pointing to an edge in the existing sample KG
                "edge_bindings": {"treated_by": [{"id": "abcde999"}]},
                "support_graphs": [],
                "score": 0.7
            }
        ]
    }
]


@pytest.mark.parametrize(
    "testcase,response,code",
    [
        (   # Query 0 -  fully validating response
            SAMPLE_TEST_CASE,
            {
                "message": {
                    "query_graph": SAMPLE_QUERY_GRAPH,
                    "knowledge_graph": SAMPLE_TEST_GRAPH,
                    "results": SAMPLE_TEST_RESULTS
                }
            },
            ""
        ),
        (   # Query 1 - missing message 'query_graph' property key
            SAMPLE_TEST_CASE,
            {
                "message": {
                    # "query_graph": SAMPLE_QUERY_GRAPH,
                    "knowledge_graph": SAMPLE_TEST_GRAPH,
                    "results": SAMPLE_TEST_RESULTS
                }
            },
            "error.trapi.response.message.query_graph.missing"
        ),
        (   # Query 2 - empty query_graph
            SAMPLE_TEST_CASE,
            {
                "message": {
                    "query_graph": {},
                    "knowledge_graph": SAMPLE_TEST_GRAPH,
                    "results": SAMPLE_TEST_RESULTS
                }
            },
            "error.trapi.response.message.query_graph.empty"
        ),
        (   # Query 3 - missing message 'knowledge_graph' property key
            SAMPLE_TEST_CASE,
            {
                "message": {
                    "query_graph": SAMPLE_QUERY_GRAPH,
                    "results": SAMPLE_TEST_RESULTS
                }
            },
            "error.trapi.response.message.knowledge_graph.missing"
        ),
        (  # Query 4 - empty message 'knowledge_graph' value
           #           is an error for OneHop testcase output
                SAMPLE_TEST_CASE,
                {
                    "message": {
                        "query_graph": SAMPLE_QUERY_GRAPH,
                        "knowledge_graph": {},
                        "results": SAMPLE_TEST_RESULTS
                    }
                },
                "error.trapi.response.message.knowledge_graph.empty"
        ),
        (   # Query 5 - missing message 'results' property key
            SAMPLE_TEST_CASE,
            {
                "message": {
                    "query_graph": SAMPLE_QUERY_GRAPH,
                    "knowledge_graph": SAMPLE_TEST_RESULTS
                }
            },
            "error.trapi.response.message.results.missing"
        ),
        (   # Query 6 - empty message 'results' property value
            #           is an error for OneHop testcase output
            SAMPLE_TEST_CASE,
            {
                "message": {
                    "query_graph": SAMPLE_QUERY_GRAPH,
                    "knowledge_graph": SAMPLE_TEST_RESULTS,
                    "results": []
                }
            },
            "error.trapi.response.message.results.empty"
        ),
        (   # Query 7 - missing message 'subject' node
            SAMPLE_TEST_CASE,
            {
                "message": {
                    "query_graph": SAMPLE_QUERY_GRAPH,
                    "knowledge_graph": {
                        "nodes": {
                            # TYPE_2_DIABETES_CURIE: {
                            #     "name": "type-2 diabetes",
                            #     "categories": [
                            #         "biolink:Disease"
                            #     ]
                            # },
                            METFORMIN_CURIE: {
                                "name": "metformin",
                                "categories": [
                                    "biolink:Drug"
                                ]
                            }
                        },
                        "edges": SAMPLE_EDGES
                    },
                    "results": SAMPLE_TEST_RESULTS
                }
            },
            "error.trapi.response.message.knowledge_graph.node.missing"
        ),
        (   # Query 8 - the test case 'subject' node category is not an exact match
            #           against the knowledge graph edge category; however, the
            #           testcase category has a parent category which does match
            #           the knowledge graph, so we just issue a suitable warning.
            SAMPLE_TEST_CASE,
            {
                "message": {
                    "query_graph": SAMPLE_QUERY_GRAPH,
                    "knowledge_graph": {
                        "nodes": {
                            TYPE_2_DIABETES_CURIE: {
                                "name": "type-2 diabetes",
                                "categories": [
                                    "biolink:DiseaseOrPhenotypicFeature"
                                ]
                            },
                            METFORMIN_CURIE: {
                                "name": "metformin",
                                "categories": [
                                    "biolink:Drug"
                                ]
                            }
                        },
                        "edges": SAMPLE_TEST_EDGES
                    },
                    "results": SAMPLE_TEST_RESULTS
                }
            },
            "warning.trapi.response.message.knowledge_graph.node.category.imprecise"
        ),
        (   # Query 9 - missing message 'object' node
            SAMPLE_TEST_CASE,
            {
                "message": {
                    "query_graph": SAMPLE_QUERY_GRAPH,
                    "knowledge_graph": {
                        "nodes": {
                            TYPE_2_DIABETES_CURIE: {
                                "name": "type-2 diabetes",
                                "categories": [
                                    "biolink:Disease"
                                ]
                            },
                            # METFORMIN_CURIE: {
                            #     "name": "metformin",
                            #     "categories": [
                            #         "biolink:Drug"
                            #     ]
                            # }
                        },
                        "edges": SAMPLE_TEST_EDGES
                    },
                    "results": SAMPLE_TEST_RESULTS
                }
            },
            "error.trapi.response.message.knowledge_graph.node.missing"
        ),
        (   # Query 10 - missing message edge
            SAMPLE_TEST_CASE,
            {
                "message": {
                    "query_graph": SAMPLE_QUERY_GRAPH,
                    "knowledge_graph": {
                        "nodes": {
                            TYPE_2_DIABETES_CURIE: {"name": "type-2 diabetes", "categories": ["biolink:Disease"]},
                            METFORMIN_CURIE: {"name": "metformin", "categories": ["biolink:Drug"]}
                        },
                        "edges": {}
                    },
                    "results": SAMPLE_TEST_RESULTS
                }
            },
            "error.trapi.response.message.knowledge_graph.edge.missing"
        ),
        (   # Query 11 -  missing specific result in messages results matching input values
            SAMPLE_TEST_CASE,
            {
                "message": {
                    "query_graph": SAMPLE_QUERY_GRAPH,
                    "knowledge_graph": SAMPLE_TEST_GRAPH,
                    "results": SAMPLE_TEST_INCOMPLETE_RESULTS
                }
            },
            "error.trapi.response.message.result.missing"
        )
    ]
)
def test_case_input_found_in_response(testcase, response, code):
    validator = TRAPIResponseValidator(
        trapi_version=LATEST_TRAPI_RELEASE,
        biolink_version=LATEST_BIOLINK_MODEL_VERSION
    )
    outcome: bool = validator.testcase_input_found_in_response(testcase=testcase, response=response)
    assert not outcome if code.startswith("error") else True
    check_messages(validator, code)
