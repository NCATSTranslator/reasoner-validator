"""
Unit tests for the generic (shared) components of the SRI Testing Framework
"""
import sys
from typing import Tuple
from pprint import PrettyPrinter
import logging
import pytest

from bmt import Toolkit

from reasoner_validator.biolink import (
    TrapiGraphType,
    BiolinkValidator,
    check_biolink_model_compliance_of_input_edge,
    check_biolink_model_compliance_of_query_graph,
    check_biolink_model_compliance_of_knowledge_graph
)

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

pp = PrettyPrinter(indent=4)


LATEST_BIOLINK_MODEL = "2.2.16"  # "Latest" Biolink Model Version


def test_set_default_biolink_versioned_global_environment():
    validator = BiolinkValidator(graph_type=TrapiGraphType.Knowledge_Graph)
    model_version = validator.get_biolink_model_version()
    logger.debug(f"\ntest_set_default_global_environment(): Biolink Model version is: '{str(model_version)}'")
    assert model_version == Toolkit().get_model_version()


def test_set_specific_biolink_versioned_global_environment():
    validator = BiolinkValidator(
        graph_type=TrapiGraphType.Knowledge_Graph,
        biolink_version="1.8.2"
    )
    assert validator.get_biolink_model_version() == "1.8.2"


@pytest.mark.parametrize(
    "query",
    [
        (   # Query 0 - Valid edge object
            LATEST_BIOLINK_MODEL,  # Biolink Model Version
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            ""
        ),
        (   # Query 1 - Invalid subject category
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:NotACategory',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            "Edge Error: 'subject' category 'biolink:NotACategory' is unknown?"
        ),
        (   # Query 2 - Invalid object category
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:NotACategory',
                'predicate': 'biolink:subclass_of',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            "Edge Error: 'object' category 'biolink:NotACategory' is unknown?"
        ),
        (   # Query 3 - Invalid predicate
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:not_a_predicate',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            "Edge Error: predicate 'biolink:not_a_predicate' is unknown?"
        ),
        (   # Query 4 - Unmappable subject namespace
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'FOO:0005453',
                'object': 'UBERON:0035769'
            },
            "Edge Error: namespace prefix of 'subject' identifier 'FOO:0005453' " +
            "is unmapped to 'biolink:AnatomicalEntity'?"
        ),
        (   # Query 5 - Unmappable object namespace
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'UBERON:0005453',
                'object': 'BAR:0035769'
            },
            "Edge Error: namespace prefix of 'object' identifier 'BAR:0035769' " +
            "is unmapped to 'biolink:AnatomicalEntity'?"
        ),
        (   # Query 6 - Valid other model
            "1.8.2",
            {
                'subject_category': 'biolink:ChemicalSubstance',
                'object_category': 'biolink:Protein',
                'predicate': 'biolink:entity_negatively_regulates_entity',
                'subject': 'DRUGBANK:DB00945',
                'object': 'UniProtKB:P23219'
            },
            ""
        )
    ]
)
def test_check_biolink_model_compliance_of_input_edge(query: Tuple):
    model_version, errors = check_biolink_model_compliance_of_input_edge(edge=query[1], biolink_version=query[0])
    print(f"Model {model_version} Errors:\n{pp.pformat(errors)}\n", file=sys.stderr, flush=True)
    assert any([error == query[2] for error in errors]) if query[2] or errors else True


@pytest.mark.parametrize(
    "query",
    [
        (
            LATEST_BIOLINK_MODEL,
            # Query 0: Sample small valid TRAPI Query Graph
            {
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
            },
            ""  # This should pass without errors
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 1: Empty query graph
            {},
            ""  # Query Graphs can have empty 'nodes'
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 2: Empty nodes dictionary
            {
                "nodes": {}
            },
            ""  # Query Graphs can have empty 'nodes'
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 3: Empty edges
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
            # Query 4: Empty edges dictionary
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:Gene"
                       ]
                    }
                },
                "edges": {}
            },
            ""  # Query Graphs can have empty 'edges'
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 5: Node "ids" not a List
            {
                "nodes": {
                    "type-2 diabetes": {"ids": "MONDO:0005148"}
                },
                "edges": {}
            },
            "Query Graph Error: Node 'type-2 diabetes.ids' slot value is not an array?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 6: Node "ids" is an empty array
            {
                "nodes": {
                    "type-2 diabetes": {"ids": []}
                },
                "edges": {}
            },
            "Query Graph Error: Node 'type-2 diabetes.ids' slot array is empty?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 7: Node "categories" not a array
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": "biolink:Gene"
                    }
                },
                "edges": {}
            },
            "Query Graph Error: Node 'NCBIGene:29974.categories' slot value is not an array?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 8: Node "categories" is an empty array?
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": []
                    }
                },
                "edges": {}
            },
            "Query Graph Error: Node 'NCBIGene:29974.categories' slot array is empty?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 9: Node "categories" is an empty array?
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": ["biolink:InvalidCategory"]
                    }
                },
                "edges": {}
            },
            "Query Graph Error: 'biolink:InvalidCategory' for node 'NCBIGene:29974' " +
            "is not a recognized Biolink Model category?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 10: Sample small valid TRAPI Query Graph with null predicates (allowed)
            {
                "nodes": {
                    "type-2 diabetes": {"ids": ["MONDO:0005148"]},
                    "drug": {
                        "categories": ["biolink:Drug"]
                    }
                },
                "edges": {
                    "treats": {
                        "subject": "drug",
                        # "predicates": ["biolink:treats"],
                        "object": "type-2 diabetes"
                    }
                }
            },
            ""  # Predicates slot can be null... This should pass without errors?
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 11: ... but if present, predicates must be an array!
            {
                "nodes": {
                    "type-2 diabetes": {"ids": ["MONDO:0005148"]},
                    "drug": {
                        "categories": ["biolink:Drug"]
                    }
                },
                "edges": {
                    "treats": {
                        "subject": "drug",
                        "predicates": "biolink:treats",
                        "object": "type-2 diabetes"
                    }
                }
            },
            "Query Graph Error: Edge 'drug--biolink:treats->type-2 diabetes' predicate slot value is not an array?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 12: ... but if present, predicates must have at least one predicate in the array
            {
                "nodes": {
                    "type-2 diabetes": {"ids": ["MONDO:0005148"]},
                    "drug": {
                        "categories": ["biolink:Drug"]
                    }
                },
                "edges": {
                    "treats": {
                        "subject": "drug",
                        "predicates": [],
                        "object": "type-2 diabetes"
                    }
                }
            },
            "Query Graph Error: Edge 'drug--[]->type-2 diabetes' predicate slot value is an empty array?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 13: ... but if present, predicates must be valid for the specified Biolink Model version
            {
                "nodes": {
                    "type-2 diabetes": {"ids": ["MONDO:0005148"]},
                    "drug": {
                        "categories": ["biolink:Drug"]
                    }
                },
                "edges": {
                    "treats": {
                        "subject": "drug",
                        "predicates": ["biolink:invalid_predicate"],
                        "object": "type-2 diabetes"
                    }
                }
            },
            "Query Graph Error: 'biolink:invalid_predicate' is an unknown Biolink Model predicate?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 14: 'Subject' id used in edge is mandatory
            {
                "nodes": {
                    "drug": {
                        "categories": ["biolink:Drug"]
                    },
                    "type-2 diabetes": {"ids": ["MONDO:0005148"]}
                },
                "edges": {
                    "treats": {
                        "predicates": ["biolink:treats"],
                        "object": "type-2 diabetes"
                    }
                }
            },
            "Query Graph Error: Edge 'None--['biolink:treats']->type-2 diabetes' " +
            "has a missing or empty 'subject' slot value?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 15: 'Subject' id used in edge is missing from the nodes catalog?
            {
                "nodes": {
                    "type-2 diabetes": {"ids": ["MONDO:0005148"]}
                },
                "edges": {
                    "treats": {
                        "subject": "drug",
                        "predicates": ["biolink:treats"],
                        "object": "type-2 diabetes"
                    }
                }
            },
            "Query Graph Error: Edge 'subject' id 'drug' is missing from the nodes catalog?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 16: 'Object' id used in edge is mandatory
            {
                "nodes": {
                    "drug": {
                        "categories": ["biolink:Drug"]
                    },
                    "type-2 diabetes": {"ids": ["MONDO:0005148"]}
                },
                "edges": {
                    "treats": {
                        "subject": "drug",
                        "predicates": ["biolink:treats"]
                    }
                }
            },
            "Query Graph Error: Edge 'drug--['biolink:treats']->None' has a missing or empty 'object' slot value?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 17: 'Object' id used in edge is missing from the nodes catalog?
            {
                "nodes": {
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
            },
            "Query Graph Error: Edge 'object' id 'type-2 diabetes' is missing from the nodes catalog?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 18: Node 'is_set' value is not a boolean
            {
                "nodes": {
                    "type-2 diabetes": {"ids": ["MONDO:0005148"]},
                    "drug": {
                        "categories": ["biolink:Drug"],
                        "is_set": "should-be-a-boolean"
                    }
                },
                "edges": {
                    "treats": {
                        "subject": "drug",
                        "predicates": ["biolink:treats"],
                        "object": "type-2 diabetes"
                    }
                }
            },
            "Query Graph Error: Node 'drug.is_set' slot is not a boolean value?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 19: Unmapped node ids against any of the specified Biolink Model categories
            {
                "nodes": {
                    "type-2 diabetes": {
                        "ids": ["FOO:12345", "BAR:67890"],
                        "categories": ["biolink:Disease", "biolink:Gene"]
                    },
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
            },
            "Query Graph Error: Node 'type-2 diabetes.ids' have ['FOO:12345', 'BAR:67890'] " +
            "that are unmapped to any of the Biolink Model categories ['biolink:Disease', 'biolink:Gene']?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 20: Sample small valid TRAPI Query Graph
            {
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
            },
            ""  # This should pass without errors
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 21: Sample small valid TRAPI Query Graph
            {
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
            },
            ""  # This should pass without errors
        )
    ]
)
def test_check_biolink_model_compliance_of_query_graph(query: Tuple):
    model_version, errors = check_biolink_model_compliance_of_query_graph(graph=query[1], biolink_version=query[0])
    print(f"Model {model_version} Errors:\n{pp.pformat(errors)}\n", file=sys.stderr, flush=True)
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
            "Knowledge Graph Error: No nodes found?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 2: Empty nodes dictionary
            {
                "nodes": {}
            },
            "Knowledge Graph Error: No nodes found?"
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
            "Knowledge Graph Error: No edges found?"
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
                "edges": {}
            },
            "Knowledge Graph Error: No edges found?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 5: missing node 'categories' slot
            {
                "nodes": {
                    "NCBIGene:29974": {}
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
            # ditto for predicate and object... but identical code pattern thus we only test missing subject id here
            "Knowledge Graph Error: Edge 'None--biolink:interacts_with->NCBIGene:29974' " +
            "has a missing or empty 'subject' slot value?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 10: 'subject' id is missing from the nodes catalog
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
            "Knowledge Graph Error: Edge 'subject' id 'NCBIGene:12345' is missing from the nodes catalog?"
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
            "Knowledge Graph Error: 'biolink:unknown_predicate' is an unknown Biolink Model predicate?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 12: 'object' id is missing from the nodes catalog
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
            "Knowledge Graph Error: Edge 'object' id 'PUBCHEM.COMPOUND:678' is missing from the nodes catalog?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 13: edge has missing or empty attributes
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
        ),
        (
            "1.8.2",
            # Query 14:  # An earlier Biolink Model Version won't recognize a category not found in its version
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
                            "biolink:SmallMolecule"  # Not valid in latest model?
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
            "Knowledge Graph Error: 'biolink:SmallMolecule' for node " +
            "'PUBCHEM.COMPOUND:597' is not a recognized Biolink Model category?"
        )
    ]
)
def test_check_biolink_model_compliance_of_knowledge_graph(query: Tuple):
    model_version, errors = check_biolink_model_compliance_of_knowledge_graph(graph=query[1], biolink_version=query[0])
    print(f"Model {model_version} Errors:\n{pp.pformat(errors)}\n", file=sys.stderr, flush=True)
    assert any([error == query[2] for error in errors]) if query[2] or errors else True
