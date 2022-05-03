"""
Unit tests for the generic (shared) components of the SRI Testing Framework
"""
import sys
from typing import Optional, Tuple
from pprint import PrettyPrinter
import logging
import pytest

from bmt import Toolkit

from biolink import (
    set_biolink_model_toolkit,
    get_toolkit,
    check_biolink_model_compliance_of_query_graph,
    check_biolink_model_compliance_of_knowledge_graph
)

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

pp = PrettyPrinter(indent=4)


LATEST_BIOLINK_MODEL = "2.2.16"  # "Latest" Biolink Model Version


def test_set_default_biolink_versioned_global_environment():
    set_biolink_model_toolkit()
    tk: Optional[Toolkit] = get_toolkit()
    assert tk
    model_version = tk.get_model_version()
    logger.debug(f"\ntest_set_default_global_environment(): Biolink Model version is: '{str(model_version)}'")
    assert model_version == Toolkit().get_model_version()


def test_set_specific_biolink_versioned_global_environment():
    set_biolink_model_toolkit(biolink_version="2.2.16")
    tk: Optional[Toolkit] = get_toolkit()
    assert tk
    assert tk.get_model_version() == "2.2.16"


@pytest.mark.parametrize(
    "query",
    [
        (
            LATEST_BIOLINK_MODEL,
            # Query 0: Sample small valid TRAPI Query Graph
            {
                "nodes": {
                    "type-2 diabetes": {"ids": ["MONDO:0005148"]},
                    "drug": {"categories": ["biolink:Drug"]}
                },
                "edges": {
                    "treats": {"subject": "drug", "predicates": ["biolink:treats"], "object": "type-2 diabetes"}
                }
            },
            ""  # This should pass without errors
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 1: Empty query graph - caught by missing 'nodes' key
            {},
            ""  # Query Graphs can have empty 'nodes'
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 2: Empty nodes dictionary
            {
                "nodes": dict()
            },
            ""  # Query Graphs can have empty 'nodes'
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 3: Empty edges - caught by missing 'edges' dictionary
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:Gene"
                       ]
                    }
                }
            },
            ""  # Query Graphs can have empty 'edges'
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 4 Empty edges dictionary
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:Gene"
                       ]
                    }
                },
                "edges": dict()
            },
            ""  # Query Graphs can have empty 'edges'
        )
    ]
)
def test_check_biolink_model_compliance_of_query_graph(query: Tuple):
    set_biolink_model_toolkit(biolink_version=query[0])
    #  check_biolink_model_compliance_of_query_graph(graph: Dict) -> Tuple[str, Optional[List[str]]]
    model_version, errors = check_biolink_model_compliance_of_query_graph(graph=query[1])
    assert model_version == get_toolkit().get_model_version()
    print(f"\nErrors:\n{pp.pformat(errors)}\n", file=sys.stderr, flush=True)
    assert any([error == query[2] for error in errors]) if query[2] or errors else True


@pytest.mark.parametrize(
    "query",
    [
        (
            LATEST_BIOLINK_MODEL,  # Biolink Model Version

            # Query 0: Sample full valid TRAPI Knowledge Graph
            {
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
            },
            ""
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 1: Empty graph - caught by missing 'nodes' key
            {},
            "TRAPI Error: No nodes found in the Knowledge Graph?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 2: Empty nodes dictionary
            {
                "nodes": dict()
            },
            "TRAPI Error: No nodes found in the Knowledge Graph?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 3: Empty edges - caught by missing 'edges' dictionary
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:Gene"
                       ]
                    }
                }
            },
            "TRAPI Error: No edges found in the Knowledge Graph?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 4 Empty edges dictionary
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:Gene"
                       ]
                    }
                },
                "edges": dict()
            },
            "TRAPI Error: No edges found in the Knowledge Graph?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 5: 'categories' tag value is ill-formed: should be a list
            {
                "nodes": {
                    "NCBIGene:29974": dict()
                },
                "edges": {
                   "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "fake-attribute-id"}]
                    }
                }
            },
            "Knowledge Graph Error: Node 'NCBIGene:29974' is missing its 'categories'?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 6: 'categories' tag value is ill-formed: should be a list
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": "biolink:Gene"
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "fake-attribute-id"}]
                    }
                }
            },
            "Knowledge Graph Error: The value of node 'NCBIGene:29974.categories' should be an array?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 7: invalid category specified
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:Nonsense_Category"
                       ]
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "fake-attribute-id"}]
                    }
                }
            },
            "Knowledge Graph Error: 'biolink:Nonsense_Category' for node " +
            "'NCBIGene:29974' is not a recognized Biolink Model category?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 8: invalid node CURIE prefix namespace, for specified category
            {
                "nodes": {
                    "FOO:1234": {
                       "categories": [
                           "biolink:Gene"
                       ]
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "FOO:1234",
                        "predicate": "biolink:interacts_with",
                        "object": "FOO:1234",
                        "attributes": [{"attribute_type_id": "fake-attribute-id"}]
                    }
                }
            },
            "Knowledge Graph Error: For all node categories [biolink:Gene] of " +
            "'FOO:1234', the CURIE prefix namespace remains unmapped?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 9: missing or empty subject, predicate, object values
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:Gene"
                       ]
                    }
                },
                "edges": {
                    "edge_1": {
                        # "subject": "",
                        "predicate": "biolink:interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "fake-attribute-id"}]
                    }
                }
            },
            # ditto for predicate and object... but identical code pattern thus we only test the subject id here
            "Knowledge Graph Error: Edge 'None--biolink:interacts_with->NCBIGene:29974' " +
            "has a missing or empty subject slot?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 10: subject id is missing from the nodes catalog
            {
                "nodes": {
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
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "NCBIGene:12345",
                        "predicate": "biolink:interacts_with",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"attribute_type_id": "fake-attribute-id"}]
                    }
                }
            },
            "Knowledge Graph Error: Edge subject id 'NCBIGene:12345' is missing from the nodes catalog?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 11: predicate is unknown
            {
                "nodes": {
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
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:unknown_predicate",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"attribute_type_id": "fake-attribute-id"}]
                    }
                }
            },
            "Knowledge Graph Error: 'biolink:unknown_predicate' is an unknown Biolink Model predicate"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 12: object id is missing from the nodes catalog
            {
                "nodes": {
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
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:interacts_with",
                        "object": "PUBCHEM.COMPOUND:678",
                        "attributes": [{"attribute_type_id": "fake-attribute-id"}]
                    }
                }
            },
            "Knowledge Graph Error: Edge object id 'PUBCHEM.COMPOUND:678' is missing from the nodes catalog?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 13: object id is missing from the nodes catalog
            {
                "nodes": {
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
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:interacts_with",
                        "object": "PUBCHEM.COMPOUND:597",
                        # "attributes": [{"attribute_type_id": "fake-attribute-id"}]
                    }
                }
            },
            "Knowledge Graph Error: Edge 'NCBIGene:29974--biolink:interacts_with->PUBCHEM.COMPOUND:597' " +
            "has missing or empty attributes?"
        )
    ]
)
def test_check_biolink_model_compliance_of_knowledge_graph(query: Tuple):
    set_biolink_model_toolkit(biolink_version=query[0])
    # check_biolink_model_compliance_of_knowledge_graph(graph: Dict) -> Tuple[str, Optional[List[str]]]:
    model_version, errors = check_biolink_model_compliance_of_knowledge_graph(graph=query[1])
    assert model_version == get_toolkit().get_model_version()
    print(f"\nErrors:\n{pp.pformat(errors)}\n", file=sys.stderr, flush=True)
    assert any([error == query[2] for error in errors]) if query[2] or errors else True
