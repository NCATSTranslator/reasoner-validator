"""
Unit tests for the generic (shared) components of the SRI Testing Framework
"""
from typing import Tuple, Optional, Dict, List
from sys import stderr
from copy import deepcopy
from pprint import PrettyPrinter
import logging
import pytest
from bmt import Toolkit
from linkml_runtime.linkml_model import SlotDefinition

from reasoner_validator import TRAPISchemaValidator
from reasoner_validator.trapi import TRAPI_1_3_0, TRAPI_1_4_0_BETA, LATEST_TRAPI_RELEASE
from reasoner_validator.biolink import (
    TRAPIGraphType,
    BiolinkValidator,
    get_biolink_model_toolkit,
    check_biolink_model_compliance_of_input_edge,
    check_biolink_model_compliance_of_query_graph,
    check_biolink_model_compliance_of_knowledge_graph
)
from tests.test_validation_report import check_messages

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

pp = PrettyPrinter(indent=4)

# January 25, 2023 - as of reasoner-validator 3.1.0,
# we don't pretend to totally support Biolink Models any earlier than 3.1.1.
# If earlier biolink model compliance testing is desired,
# then perhaps reasoner-validator version 3.0.5 or earlier can be used.
LATEST_BIOLINK_MODEL_VERSION = "3.2.0"

# special case of signalling suppression of validation
SUPPRESS_BIOLINK_MODEL_VALIDATION = "suppress"


def test_set_default_biolink_versioned_global_environment():
    validator = BiolinkValidator(graph_type=TRAPIGraphType.Knowledge_Graph)
    model_version = validator.get_biolink_version()
    print(
        f"\ntest_set_default_global_environment(): Biolink Model version is: '{str(model_version)}'",
        file=stderr, flush=True
    )
    assert model_version == Toolkit().get_model_version()


def test_set_specific_biolink_versioned_global_environment():
    validator = BiolinkValidator(
        graph_type=TRAPIGraphType.Knowledge_Graph,
        biolink_version="1.8.2"
    )
    assert validator.get_biolink_version() == "1.8.2"


def test_minimum_required_biolink_version():
    # Setting Validator to BLM release 2.2.0
    validator = BiolinkValidator(
        graph_type=TRAPIGraphType.Knowledge_Graph,
        biolink_version="2.2.0"
    )
    # 2.2.0 >= 1.8.2 - True!
    assert validator.minimum_required_biolink_version("1.8.2")
    # 2.2.0 >= 2.2.0 - True!
    assert validator.minimum_required_biolink_version("2.2.0")
    # 2.2.0 >= 2.4.8 - False!
    assert not validator.minimum_required_biolink_version("2.4.8")


def test_inverse_predicate():
    tk: Toolkit = get_biolink_model_toolkit("2.2.0")
    predicate = tk.get_element("biolink:related_to")
    assert predicate['symmetric']
    predicate = tk.get_element("biolink:active_in")
    assert not predicate['symmetric']
    assert isinstance(predicate, SlotDefinition)
    assert not tk.get_inverse(predicate.name)
    tk: Toolkit = get_biolink_model_toolkit("v2.4.8")
    predicate = tk.get_element("biolink:active_in")
    assert not predicate['symmetric']
    assert isinstance(predicate, SlotDefinition)
    assert tk.get_inverse(predicate.name) == "has active component"


BLM_VERSION_PREFIX = f"Biolink Validation of"
INPUT_EDGE_PREFIX = f"{BLM_VERSION_PREFIX} Input Edge"
QUERY_GRAPH_PREFIX = f"{BLM_VERSION_PREFIX} Query Graph"
KNOWLEDGE_GRAPH_PREFIX = f"{BLM_VERSION_PREFIX} Knowledge Graph"


@pytest.mark.parametrize(
    "query",
    [
        (   # Query 0 - Valid edge object
            LATEST_BIOLINK_MODEL_VERSION,  # Biolink Model Version
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject_id': 'UBERON:0005453',
                'object_id': 'UBERON:0035769'
            },
            ""
        ),
        (   # Query 1 - Valid edge object, using original 'subject' and 'object' JSON tags
            LATEST_BIOLINK_MODEL_VERSION,  # Biolink Model Version
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            ""  # should still no generate an error message
        ),
        (   # Query 2 - Missing subject category
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject_id': 'UBERON:0005453',
                'object_id': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Subject has a missing Biolink category!"
            "error.input_edge.node.category.missing"
        ),
        (   # Query 3 - Invalid subject category
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:NotACategory',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject_id': 'UBERON:0005453',
                'object_id': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Subject element 'biolink:NotACategory' is unknown!"
            "error.input_edge.node.category.unknown"
        ),
        (   # Query 4 - Missing object category
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject_id': 'UBERON:0005453',
                'object_id': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Object has a missing Biolink category!"
            "error.input_edge.node.category.missing"
        ),
        (   # Query 5 - Invalid object category
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:NotACategory',
                'predicate': 'biolink:subclass_of',
                'subject_id': 'UBERON:0005453',
                'object_id': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Object element 'biolink:NotACategory' is unknown!"
            "error.input_edge.node.category.unknown"
        ),
        (   # Query 6 - Missing predicate
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'subject_id': 'UBERON:0005453',
                'object_id': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Predicate is missing or empty!"
            "error.input_edge.predicate.missing"
        ),
        (   # Query 7- Empty predicate
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': '',
                'subject_id': 'UBERON:0005453',
                'object_id': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Predicate is missing or empty!"
            "error.input_edge.predicate.missing"
        ),
        (   # Query 8 - Predicate is deprecated
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:Drug',
                'object_category': 'biolink:Protein',
                'predicate': 'biolink:increases_amount_or_activity_of',
                'subject_id': 'NDC:0002-8215-01',  # a form of insulin
                'object_id': 'MONDO:0005148'  # type 2 diabetes?
            },
            # f"{INPUT_EDGE_PREFIX}: WARNING - Predicate element " +
            # "'binds' is deprecated?"  # in Biolink 3.1.1
            "warning.input_edge.predicate.deprecated"
        ),
        (   # Query 9 - Predicate is abstract
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:InformationContentEntity',
                'object_category': 'biolink:Agent',
                'predicate': 'biolink:contributor',
                'subject_id': 'PMID:1234',
                'object_id': 'ORCID:56789'
            },
            # f"{INPUT_EDGE_PREFIX}: INFO - Predicate element 'biolink:contributor' is abstract."
            "info.input_edge.predicate.abstract"
        ),
        (   # Query 10 - Predicate is a mixin
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:Drug',
                'object_category': 'biolink:BiologicalProcess',
                'predicate': 'biolink:decreases_amount_or_activity_of',
                'subject_id': 'NDC:50090‑0766',  # Metformin
                'object_id': 'GO:0006094'  # Gluconeogenesis
            },
            # f"{INPUT_EDGE_PREFIX}: INFO - Predicate element 'biolink:decreases_amount_or_activity_of' is a mixin."
            "info.input_edge.predicate.mixin"
        ),
        (   # Query 11 - Unknown predicate element
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:not_a_predicate',
                'subject_id': 'UBERON:0005453',
                'object_id': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Predicate element 'biolink:not_a_predicate' is unknown!"
            "error.input_edge.predicate.unknown"
        ),
        (   # Query 12 - Invalid or unknown predicate
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:has_unit',
                'subject_id': 'UBERON:0005453',
                'object_id': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Predicate element 'biolink:has_unit' is invalid!"
            "error.input_edge.predicate.invalid"
        ),
        (   # Query 13 - Non-canonical directed predicate
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:SmallMolecule',
                'object_category': 'biolink:Disease',
                'predicate': 'biolink:affected_by',
                'subject_id': 'DRUGBANK:DB00331',
                'object_id': 'MONDO:0005148'
            },
            # f"{INPUT_EDGE_PREFIX}: WARNING - Edge predicate 'biolink:affected_by' is non-canonical?"
            "warning.input_edge.predicate.non_canonical"
        ),
        (   # Query 14 - Missing subject
            LATEST_BIOLINK_MODEL_VERSION,  # Biolink Model Version
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'object_id': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Subject node identifier is missing!"
            "error.input_edge.node.id.missing"
        ),
        (   # Query 15 - Unmappable subject namespace
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject_id': 'FOO:0005453',
                'object_id': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: WARNING - Subject node identifier 'FOO:0005453' " +
            # "is unmapped to 'biolink:AnatomicalEntity'?"
            "warning.input_edge.node.id.unmapped_to_category"
        ),
        (   # Query 16 - missing object
            LATEST_BIOLINK_MODEL_VERSION,  # Biolink Model Version
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject_id': "UBERON:0005453"
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Object node identifier is missing!"
            "error.input_edge.node.id.missing"
        ),
        (   # Query 17 - Unmappable object namespace
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject_id': 'UBERON:0005453',
                'object_id': 'BAR:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: WARNING - Object node identifier 'BAR:0035769' " +
            # "is unmapped to 'biolink:AnatomicalEntity'?"
            "warning.input_edge.node.id.unmapped_to_category"
        ),
        (   # Query 18 - Valid other model
            "1.8.2",
            {
                'subject_category': 'biolink:ChemicalSubstance',
                'object_category': 'biolink:Protein',
                'predicate': 'biolink:entity_negatively_regulates_entity',
                'subject_id': 'DRUGBANK:DB00945',
                'object_id': 'UniProtKB:P23219'
            },
            ""
        ),
        # (   # Query xx - Deprecated node category - no example of this in BIolink 3.1.1
        #     LATEST_BIOLINK_MODEL,
        #     {
        #         'subject_category': 'biolink:Nutrient',
        #         'object_category': 'biolink:Protein',
        #         'predicate': 'biolink:physically_interacts_with',
        #         'subject': 'CHEBI:27300',
        #         'object': 'Orphanet:120464'
        #     },
        #     # f"{INPUT_EDGE_PREFIX}: WARNING - Subject 'biolink:Nutrient' is deprecated?"
        #     "warning.input_edge.node.category.deprecated"
        # ),
        (   # Query 19 - Issue a warning for input_edge data with a category that is a mixin?
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:GeneOrGeneProduct',
                'object_category': 'biolink:Protein',
                'predicate': 'biolink:related_to',
                'subject_id': 'HGNC:9604',
                'object_id': 'UniProtKB:P23219'
            },
            "warning.input_edge.node.category.not_concrete"
        ),
        (   # Query 20 - Issue a warning for input_edge data with a category that is abstract?
            LATEST_BIOLINK_MODEL_VERSION,
            {
                'subject_category': 'biolink:AdministrativeEntity',
                'object_category': 'biolink:Agent',
                'predicate': 'biolink:related_to',
                'subject_id': 'isbn:1234',
                'object_id': 'ORCID:1234'
            },
            "warning.input_edge.node.category.not_concrete"
        )
    ]
)
def test_check_biolink_model_compliance_of_input_edge(query: Tuple):
    validator: BiolinkValidator = check_biolink_model_compliance_of_input_edge(edge=query[1], biolink_version=query[0])
    check_messages(validator, query[2])


@pytest.mark.parametrize(
    "query",
    [
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 0: Sample small valid TRAPI Query Graph
            {
                "edges": {
                    "t_edge": {
                        "attribute_constraints": [],
                        "exclude": None,
                        "knowledge_type": "inferred",
                        "object": "on",
                        "option_group_id": None,
                        "predicates": [
                            "biolink:treats"
                        ],
                        "qualifier_constraints": [],
                        "subject": "sn"
                    }
                },
                "nodes": {
                    "on": {
                        "categories": [
                            "biolink:Disease"
                        ],
                        "constraints": [],
                        "ids": [
                            "MONDO:0015564"
                        ],
                        "is_set": False,
                        "option_group_id": None
                    },
                    "sn": {
                        "categories": [
                            "biolink:ChemicalEntity"
                        ],
                        "constraints": [],
                        "ids": None,
                        "is_set": False,
                        "option_group_id": None
                    }
                }
            }
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 1: Simpler small valid TRAPI Query Graph
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
            }
        )
    ]
)
def test_conservation_of_query_graph(query: Tuple):
    """
    This test checks for internal glitch where the query graph is somehow deleted
    """
    original_graph: Dict = deepcopy(query[1])
    check_biolink_model_compliance_of_query_graph(graph=query[1], biolink_version=query[0])
    assert query[1] == original_graph


@pytest.mark.parametrize(
    "query",
    [
        (
            LATEST_BIOLINK_MODEL_VERSION,
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
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 1: Empty query graph
            {},
            # Query Graphs can have empty 'nodes', so we should just issue a warning
            # f"{QUERY_GRAPH_PREFIX}: WARNING - Empty graph!"
            "warning.graph.empty"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 2: Empty nodes dictionary
            {
                "nodes": {}
            },
            ""  # Query Graphs can have empty 'nodes'
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
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
            LATEST_BIOLINK_MODEL_VERSION,
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
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 5: Node "ids" not a List
            {
                "nodes": {
                    "type-2 diabetes": {"ids": "MONDO:0005148"}
                },
                "edges": {}
            },
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Node 'type-2 diabetes.ids' slot value is not an array!"
            "error.query_graph.node.ids.not_array"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 6: Node "ids" is an empty array
            {
                "nodes": {
                    "type-2 diabetes": {"ids": []}
                },
                "edges": {}
            },
            ""
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 7: Node "categories" not a array
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": "biolink:Gene"
                    }
                },
                "edges": {}
            },
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Node 'NCBIGene:29974.categories' slot value is not an array!"
            "error.query_graph.node.categories.not_array"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 8: Node "categories" is an empty array?
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": ["biolink:InvalidCategory"]
                    }
                },
                "edges": {}
            },
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Query Graph Node element 'biolink:InvalidCategory' is unknown!"
            "error.query_graph.node.category.unknown"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 9: Sample small valid TRAPI Query Graph with null predicates (allowed)
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
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 10: ... but if present, predicates must be an array!
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
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Edge 'drug--biolink:treats->type-2 diabetes' " +
            # f"predicate slot value is not an array!"
            "error.query_graph.edge.predicate.not_array"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 11: ... but if present, predicates must have at least one predicate in the array
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
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Edge 'drug--[]->type-2 diabetes' predicate slot value is an empty array!"
            "error.query_graph.edge.predicate.empty_array"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 12: ... but if present, predicates must be valid for the specified Biolink Model version...
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
                        "predicates": ["biolink:not_a_predicate"],
                        "object": "type-2 diabetes"
                    }
                }
            },
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Predicate element 'biolink:not_a_predicate' is unknown!"
            "error.query_graph.edge.predicate.unknown"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 13: ... but if present, predicates must be valid for the specified Biolink Model version...
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
                        "predicates": ["biolink:has_unit"],
                        "object": "type-2 diabetes"
                    }
                }
            },
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Predicate element 'biolink:has_unit' is invalid!"
            "error.query_graph.edge.predicate.invalid"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 14: ... and must also be canonical predicates?
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
                        "predicates": ["biolink:affected_by"],
                        "object": "type-2 diabetes"
                    }
                }
            },
            # f"{QUERY_GRAPH_PREFIX}: WARNING - Edge predicate 'biolink:affected_by' is non-canonical?"
            "warning.query_graph.edge.predicate.non_canonical"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 15: 'Subject' id used in edge is mandatory
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
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Edge 'None--['biolink:treats']->type-2 diabetes' " +
            # "has a missing or empty 'subject' slot value!"
            "error.query_graph.edge.subject.missing"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 16: 'Subject' id used in edge is missing from the nodes catalog?
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
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Edge 'subject' id 'drug' is missing from the nodes catalog!"
            "error.query_graph.edge.subject.missing_from_nodes"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 17: 'Object' id used in edge is mandatory
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
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Edge 'drug--['biolink:treats']->None' " +
            # f"has a missing or empty 'object' slot value!"
            "error.query_graph.edge.object.missing"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 18: 'Object' id used in edge is missing from the nodes catalog?
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
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Edge 'object' id 'type-2 diabetes' is missing from the nodes catalog!"
            "error.query_graph.edge.object.missing_from_nodes"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 19: Node 'is_set' value is not a boolean
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
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Node 'drug.is_set' slot is not a boolean value!"
            "error.query_graph.node.is_set.not_boolean"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 20: Unmapped node ids against any of the specified Biolink Model categories
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
            # f"{QUERY_GRAPH_PREFIX}: WARNING - Node 'type-2 diabetes' has identifiers ['FOO:12345', 'BAR:67890'] " +
            # "unmapped to the target categories: ['biolink:Disease', 'biolink:Gene']?"
            "warning.query_graph.node.ids.unmapped_prefix"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 21: Abstract category in query graph? Simply ignored now during validation...
            {
                "nodes": {
                    "type-2 diabetes": {"ids": ["MONDO:0005148"]},
                    "drug": {
                        "categories": ["biolink:BiologicalEntity"]
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
            ""
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 22: Mixin category in query graph? Simply ignored now during validation...
            {
                "nodes": {
                    "type-2 diabetes": {"ids": ["MONDO:0005148"]},
                    "drug": {
                        "categories": ["biolink:ChemicalOrDrugOrTreatment"]
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
            ""
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 23: Query edge predicate is a mixin
            {
                "nodes": {
                    "IRS1": {"ids": ["HGNC:6125"], "categories": ["biolink:Gene"]},
                    "drug": {
                        "categories": ["biolink:Drug"]
                    }
                },
                "edges": {
                    "treats": {
                        "subject": "drug",
                        "predicates": ["biolink:increases_amount_or_activity_of"],
                        "object": "IRS1"
                    }
                }
            },
            # f"{QUERY_GRAPH_PREFIX}: INFO - Predicate element 'biolink:increases_amount_or_activity_of' is a mixin."
            "info.query_graph.edge.predicate.mixin"
        ),
        (
            SUPPRESS_BIOLINK_MODEL_VALIDATION,
            # Query 24: ... but if present, predicates must be valid
            #           for the specified Biolink Model version, but...
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
                        "predicates": ["biolink:has_unit"],
                        "object": "type-2 diabetes"
                    }
                }
            },
            # ...since Biolink Model validation is tagged as 'suppress',
            # we  don't expect any validation output here?
            ""
        ),
        (
            SUPPRESS_BIOLINK_MODEL_VALIDATION,
            # Query 25: Query edge predicate is a mixin...but...
            {
                "nodes": {
                    "IRS1": {"ids": ["HGNC:6125"], "categories": ["biolink:Gene"]},
                    "drug": {
                        "categories": ["biolink:Drug"]
                    }
                },
                "edges": {
                    "treats": {
                        "subject": "drug",
                        "predicates": ["biolink:increases_amount_or_activity_of"],
                        "object": "IRS1"
                    }
                }
            },
            # ...since Biolink Model validation is tagged as 'suppress',
            # we  don't expect any validation output here?
            ""
        )
    ]
)
def test_check_biolink_model_compliance_of_query_graph(query: Tuple):
    validator: BiolinkValidator = \
        check_biolink_model_compliance_of_query_graph(graph=query[1], biolink_version=query[0])
    check_messages(validator, query[2])


TEST_ARA_CASE_TEMPLATE = {
    "idx": 0,
    "url": "http://test_ara_endpoint",
    "ara_api_name": "Test_ARA",
    "ara_source": "aragorn",
    "kp_api_name": "Test_KP_1",
    "kp_source": "panther",
    "kp_source_type": "primary"
}


def get_ara_test_case(changes: Optional[Dict[str, str]] = None):
    test_case = TEST_ARA_CASE_TEMPLATE.copy()
    if changes:
        test_case.update(changes)
    return test_case


#
# Attribute constraints are not yet implemented
#
# @pytest.mark.parametrize(
#     "query",
#     [
#         ("", "")
#     ]
# )
# def test_validate_attribute_constraints(query: Tuple):
#     validator = BiolinkValidator(
#         graph_type=TRAPIGraphType.Query_Graph,
#         biolink_version=LATEST_BIOLINK_MODEL
#     )
#     validator.validate_attribute_constraints(edge_id="test_validate_attributes unit test", edge=query[0])
#     check_messages(validator, query[1])


@pytest.mark.parametrize(
    "edge_data,validation_code",
    [
        # (
        #         "mock_edge",  # mock data has dumb edges: don't worry about the S-P-O, just the attributes
        #         "mock_context",
        #         "AssertError_message"
        # ),   # set 3rd argument to AssertError message if test edge should 'fail'; otherwise, empty string (for pass)
        (
            # Query 0. 'attributes' key missing in edge record is None
            {},
            # "Edge has no 'attributes' key!"
            "error.knowledge_graph.edge.attribute.missing"
        ),
        (
            # Query 1. Empty attributes
            {
                "attributes": None
            },
            # "Edge has empty attributes!"
            "error.knowledge_graph.edge.attribute.empty"
        ),
        (
            # Query 2. Empty attributes
            {
                "attributes": []
            },
            # "Edge has empty attributes!"
            "error.knowledge_graph.edge.attribute.empty"
        )
    ]
)
def test_pre_trapi_1_4_0_validate_missing_or_empty_attributes(edge_data: Dict, validation_code: str):
    validator = BiolinkValidator(graph_type=TRAPIGraphType.Knowledge_Graph, trapi_version=TRAPI_1_3_0)
    validator.validate_attributes(edge_id="test_validate_attributes unit test", edge=edge_data)
    check_messages(validator, validation_code)


@pytest.mark.parametrize(
    "edge_data",
    [
        # These tests should all pass in TRAPI releases 'default' >= 1.4.0-beta
        (
            # Query 0. 'attributes' key missing in edge record is None
            {}
        ),
        (
            # Query 1. Empty attributes
            {
                "attributes": None
            }
        ),
        (
            # Query 2. Empty attributes
            {
                "attributes": []
            }
        ),
        (
            # Query 3. EDAM-DATA:2526 ought to have an acceptable namespace
            {
                "attributes": [
                    {
                        "attribute_type_id": "EDAM-DATA:2526",
                        "value": "some-value"
                    }
                ]
            }
        ),
        (
            # Query 4. Validating terms in the ATTRIBUTE_TYPE_ID_INCLUSIONS list
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:knowledge_level",
                        "value": "knowledge_assertion"
                    },
                    {
                        "attribute_type_id": "biolink:agent_type",
                        "value": "manual_agent"
                    }
                ]
            }
        )
    ]
)
def test_post_1_4_0_trapi_validate_attributes(edge_data: Dict):
    validator = BiolinkValidator(graph_type=TRAPIGraphType.Knowledge_Graph)
    validator.validate_attributes(edge_id="test_validate_attributes unit test", edge=edge_data)
    check_messages(validator, "")


@pytest.mark.parametrize(
    "query",
    [
        (
            # Query 0. Missing ARA knowledge source provenance?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "infores:sri-reference-kg"
                    },
                ]
            },
            get_ara_test_case(),
            # "missing ARA knowledge source provenance!"
            "warning.knowledge_graph.edge.provenance.ara.missing"
        ),
        (
            # Query 1. KP provenance value is not a well-formed InfoRes CURIE? Should fail?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "infores:aragorn"
                    },
                    {
                        "attribute_type_id": "biolink:primary_knowledge_source",
                        "value": "panther"
                    }
                ]
            },
            get_ara_test_case(),
            # "Edge has provenance value '{infores}' which is not a well-formed InfoRes CURIE!"
            "error.knowledge_graph.edge.provenance.infores.missing"
        ),
        (
            # Query 2. KP provenance value is missing?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "infores:aragorn"
                    }
                ]
            },
            get_ara_test_case(),
            # "is missing as expected knowledge source provenance!"
            "warning.knowledge_graph.edge.provenance.kp.missing"
        ),
        (
            # Query 3. Missing 'primary' nor 'original' knowledge source
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "infores:aragorn"
                    },
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "infores:panther"
                    }
                ]

            },
            get_ara_test_case({"kp_source_type": "aggregator"}),
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Edge has neither a 'primary' nor 'original' knowledge source?"
            "error.knowledge_graph.edge.provenance.missing_primary"
        )
    ]
)
def test_pre_1_4_0_validate_provenance(query: Tuple):
    """TRAPI pre-1.4.0 releases recorded provenance in attributes. This unit test checks for this"""
    validator = BiolinkValidator(
        graph_type=TRAPIGraphType.Knowledge_Graph,
        trapi_version=TRAPI_1_3_0,
        biolink_version=LATEST_BIOLINK_MODEL_VERSION,
        target_provenance=query[1]
    )
    validator.validate_attributes(edge_id="test_validate_attributes unit test", edge=query[0])
    check_messages(validator, query[2])


@pytest.mark.parametrize(
    "query",
    [
        (
            # Query 0. Attributes are not a proper array
            {
                "attributes": {"not_a_list"}
            },
            get_ara_test_case(),
            # "Edge attributes are not an array!"
            "error.knowledge_graph.edge.attribute.not_array"
        ),
        (
            # Query 1. attribute missing its 'attribute_type_id' field
            {
                "attributes": [
                    {"value": ""}
                ]
            },
            get_ara_test_case(),
            # "Edge attribute missing its 'attribute_type_id' property!"
            "error.knowledge_graph.edge.attribute.type_id.missing"
        ),
        (
            # Query 2. attribute missing its 'value' field
            {
                "attributes": [
                    {"attribute_type_id": "biolink:p_value"}
                ]
            },
            get_ara_test_case(),
            # "Edge attribute missing its 'value' property!"
            "error.knowledge_graph.edge.attribute.value.missing"
        ),
        (
            # Query 3. value is an empty list?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": []
                    },
                ]
            },
            get_ara_test_case(),
            "error.knowledge_graph.edge.attribute.value.empty"
        ),
        (
            # Query 4. value is the string "null"?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "null"
                    },
                ]
            },
            get_ara_test_case(),
            "error.knowledge_graph.edge.attribute.value.empty"
        ),
        (
            # Query 5. value is the string "N/A"?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "N/A"
                    },
                ]
            },
            get_ara_test_case(),
            "error.knowledge_graph.edge.attribute.value.empty"
        ),
        (
            # Query 6. value is the string "None"
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "None"
                    },
                ]
            },
            get_ara_test_case(),
            "error.knowledge_graph.edge.attribute.value.empty"
        ),
        (
            # Query 7. KP provenance value is not a well-formed InfoRes CURIE? Should fail?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "infores:aragorn"
                    },
                    {
                        "attribute_type_id": "biolink:primary_knowledge_source",
                        "value": "infores:panther"
                    },
                    {
                        "attribute_type_id": "non_a_curie",
                        "value": "something"
                    }
                ]
            },
            get_ara_test_case(),
            # "is not a well-formed CURIE!"
            "error.knowledge_graph.edge.attribute.type_id.not_curie"
        ),
        (
            # Query 8. kp type is 'primary'. Should pass?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "infores:aragorn"
                    },
                    {
                        "attribute_type_id": "biolink:primary_knowledge_source",
                        "value": "infores:panther"
                    }
                ]
            },
            get_ara_test_case(),
            ""
        ),
        (
            # Query 9. Is complete and should pass?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "infores:aragorn"
                    },
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "infores:panther"
                    },
                    {
                        "attribute_type_id": "biolink:primary_knowledge_source",
                        "value": "infores:my-primary-ks"
                    }
                ]
            },
            get_ara_test_case({"kp_source_type": "aggregator"}),
            ""
        )
    ]
)
def test_latest_validate_attributes(query: Tuple):
    validator = BiolinkValidator(
        graph_type=TRAPIGraphType.Knowledge_Graph,
        # trapi_version="latest",
        biolink_version=LATEST_BIOLINK_MODEL_VERSION,
        target_provenance=query[1]
    )
    validator.validate_attributes(edge_id="test_validate_attributes unit test", edge=query[0])
    check_messages(validator, query[2])


def qualifier_validator(
        tested_method,
        edge_model: str,
        query: Tuple[Dict, str],
        trapi_version: Optional[str] = None,
        biolink_version: Optional[str] = LATEST_BIOLINK_MODEL_VERSION
):
    # TODO: to review: which of the validation tests that may be overridden by earlier TRAPI validation
    # Sanity check: does TRAPI validation catch this first?
    trapi_validator = TRAPISchemaValidator(trapi_version=trapi_version)
    # Wrap Qualifiers inside a small mock QEdge
    mock_edge: Dict = deepcopy(query[0])
    mock_edge["subject"] = "mock_subject"

    if trapi_validator.minimum_required_trapi_version(TRAPI_1_4_0_BETA):
        # not testing Edge semantics here but rather, the qualifiers,
        # but from 1.4.0-beta(2) onwards, we also need
        # a non-null predicate and the new 'sources' field here!
        mock_edge["predicate"] = "biolink:related_to"
        mock_edge["sources"] = [
            {
                "resource_id": "infores:molepro",
                "resource_role": "primary_knowledge_source"
            }
        ]

    mock_edge["object"] = "mock_object"
    trapi_validator.is_valid_trapi_query(mock_edge, edge_model)
    # TODO: not sure if simple errors should be fully displaced
    #       by 'critical' errors or rather, just complement them
    if trapi_validator.has_critical():
        validator = trapi_validator
    else:
        # if you get this far,then attempt additional Biolink Validation
        validator = BiolinkValidator(
            graph_type=TRAPIGraphType.Query_Graph,
            trapi_version=trapi_version,
            biolink_version=biolink_version
        )
        tested_method(
            validator,
            edge_id=f"{tested_method.__name__} unit test",
            edge=query[0]
        )
    check_messages(validator, query[1])


@pytest.mark.parametrize(
    "query",
    [
        (  # Query 0 - no 'qualifier_constraints' key - since nullable: true, this should pass
            {},
            ""
        ),
        (  # Query 1 - 'qualifier_constraints' value is None - invalidated by TRAPI schema
            {
                'qualifier_constraints': None
            },
            "critical.trapi.validation"
        ),
        (  # Query 2 - 'qualifier_constraints' value is not an array - invalidated by TRAPI schema
            {
                'qualifier_constraints': {}
            },
            "critical.trapi.validation"
        ),
        (  # Query 3 - empty 'qualifier_constraints' array value - since nullable: true, this should pass
            {
                'qualifier_constraints': []
            },
            ""
        ),
        (  # Query 4 - empty 'qualifier_set' entry - invalidated by TRAPI schema
            {
                'qualifier_constraints': [
                    {}
                ]
            },
            "critical.trapi.validation"
        ),
        (  # Query 5 - 'qualifier_set' entry is not a dictionary - invalidated by TRAPI schema
            {
                'qualifier_constraints': [
                    []
                ]
            },
            "critical.trapi.validation"
        ),
        (  # Query 6 - 'qualifier_set' entry is missing the 'qualifier_set' key - invalidated by TRAPI schema
            {
                'qualifier_constraints': [
                    {"not_qualifier_set": []}
                ]
            },
            "critical.trapi.validation"
        ),
        (  # Query 7 - 'qualifier_set' entry is empty
            {
                'qualifier_constraints': [
                    {"qualifier_set": []}
                ]
            },
            "error.query_graph.edge.qualifier_constraints.qualifier_set.empty"
        ),
        (  # Query 8 - 'qualifier_set' object value is not an array - invalidated by TRAPI schema
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": {}
                    }
                ]
            },
            "critical.trapi.validation"
        ),
        (  # Query 9 - 'qualifier' entry in the qualifier_set is empty - invalidated by TRAPI schema
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": [
                            None
                        ]
                    }
                ]
            },
            "critical.trapi.validation"
        ),
        (  # Query 10 - 'qualifier' entry is not a JSON object (dictionary) - invalidated by TRAPI schema
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": [
                            []
                        ]
                    }
                ]
            },
            "critical.trapi.validation"
        ),
        (  # Query 11 - 'qualifier' entry is missing its 'qualifier_type_id' property - invalidated by TRAPI schema
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": [
                            {
                                # 'qualifier_type_id': "",
                                'qualifier_value': ""
                            }
                        ]
                    }
                ]
            },
            "critical.trapi.validation"
        ),
        (  # Query 12 - 'qualifier_type_id' property value is unknown
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": [
                            {
                                'qualifier_type_id': "biolink:unknown_qualifier",
                                'qualifier_value': "fake-qualifier-value"
                            }
                        ]
                    }
                ]
            },
            "error.query_graph.edge.qualifier_constraints.qualifier_set.qualifier.type_id.unknown"
        ),
        (  # Query 13 - 'qualifier_type_id' property value is valid but abstract
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": [
                            {
                                'qualifier_type_id': "biolink:aspect_qualifier",
                                'qualifier_value': "stability"
                            }
                        ]
                    }
                ]
            },
            ""  # this will pass here since Query Graphs are allowed to have abstract qualifiers?
        ),
        (  # Query 14 - 'qualifier_type_id' property value is not a Biolink qualifier term
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": [
                            {
                                'qualifier_type_id': "biolink:related_to",
                                'qualifier_value': "fake-qualifier-value"
                            }
                        ]
                    }
                ]
            },
            "error.query_graph.edge.qualifier_constraints.qualifier_set.qualifier.type_id.unknown"
        ),
        (  # Query 15 - 'qualifier' entry is missing its 'qualifier_value' property - invalidated by TRAPI schema
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": [
                            {
                                'qualifier_type_id': "biolink:object_direction_qualifier"
                            }
                        ]
                    }
                ]
            },
            "critical.trapi.validation"
        ),
        (   # Query 16 - qualifier_type_id 'object_direction_qualifier' is a valid Biolink qualifier type and
            #            'upregulated' a valid corresponding 'permissible value' enum 'qualifier_value'
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": [
                            {
                                'qualifier_type_id': "biolink:object_direction_qualifier",
                                'qualifier_value': "upregulated"
                            }
                        ]
                    }
                ]
            },
            ""    # this particular use case should pass
        ),
        # (   #  *** Currently unsupported use case:
        #     # Query xx - 'qualifier_type_id' is a valid Biolink qualifier type and 'RO:0002213'
        #     #            is an 'exact match' to a 'upregulated', the above 'qualifier_value'
        #     {
        #         'qualifier_constraints': [
        #             {
        #                 "qualifier_set": [
        #                     {
        #                         'qualifier_type_id': "biolink:object_direction_qualifier",
        #                         'qualifier_value': "RO:0002213"   # RO 'exact match' term for 'upregulated'
        #                     }
        #                 ]
        #             }
        #         ]
        #     },
        #     ""    # this other use case should also pass
        # ),
        (   # Query 17 - 'qualifier_type_id' is the special qualifier case 'biolink:qualified_predicate'
            #            with a Biolink predicate as its value
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": [
                            {
                                'qualifier_type_id': "biolink:qualified_predicate",
                                'qualifier_value': "biolink:causes"
                            }
                        ]
                    }
                ]
            },
            ""  # this particular use case should also pass
        ),
        (   # Query 18 - 'qualifier_type_id' is the special qualifier case 'biolink:qualified_predicate'
            #            an incorrect value, which is not a Biolink predicate
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": [
                            {
                                'qualifier_type_id': "biolink:qualified_predicate",
                                'qualifier_value': "biolink:Association"
                            }
                        ]
                    }
                ]
            },
            "error.query_graph.edge.qualifier_constraints.qualifier_set.qualifier.value.not_a_predicate"
        )
    ]
)
def test_validate_qualifier_constraints(query: Tuple[Dict, str]):
    # TODO: to review: which of the validation tests that may be overridden by earlier TRAPI validation
    qualifier_validator(
        tested_method=BiolinkValidator.validate_qualifier_constraints,
        edge_model="QEdge",
        query=query
    )


@pytest.mark.parametrize(
    "query",
    [
        (   # Query 0 - 'qualifier_type_id' is the special qualifier case 'biolink:qualified_predicate'
            #            an incorrect value, which is not a Biolink predicate,  but...
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": [
                            {
                                'qualifier_type_id': "biolink:qualified_predicate",
                                'qualifier_value': "biolink:Association"
                            }
                        ]
                    }
                ]
            },
            # ...since Biolink Model validation is tagged as 'suppress',
            #    then we don't expect any validation output here?
            ""
        ),
        (  # Query 14 - 'qualifier_type_id' property value is not a Biolink qualifier term, but...
            {
                'qualifier_constraints': [
                    {
                        "qualifier_set": [
                            {
                                'qualifier_type_id': "biolink:related_to",
                                'qualifier_value': "fake-qualifier-value"
                            }
                        ]
                    }
                ]
            },
            # ...since Biolink Model validation is tagged as 'suppress',
            #    then we don't expect any validation output here?
            ""
        )
    ]
)
def test_biolink_validation_suppressed_validate_qualifier_constraints(query: Tuple[Dict, str]):
    qualifier_validator(
        tested_method=BiolinkValidator.validate_qualifier_constraints,
        edge_model="QEdge",
        query=query,
        biolink_version="suppress"
    )


QC_QS_NOT_A_CURIE = {
    'qualifier_constraints': [
        {
            "qualifier_set": [
                {
                    'qualifier_type_id': "not-a-curie",
                    'qualifier_value': "fake-qualifier-value"
                }
            ]
        }
    ]
}


@pytest.mark.parametrize(
    "query",
    [
        (  # Query 0 - 'qualifier_type_id' value not a Biolink CURIE - seen as 'unknown' in TRAPI < 1.4.0-beta
            TRAPI_1_3_0,
            QC_QS_NOT_A_CURIE,
            "error.query_graph.edge.qualifier_constraints.qualifier_set.qualifier.type_id.unknown"
        ),
        (  # Query 1 - 'qualifier_type_id' value not a Biolink CURIE - schema validation error in TRAPI < 1.4.0-beta
            TRAPI_1_4_0_BETA,
            QC_QS_NOT_A_CURIE,
            "critical.trapi.validation"
        )
    ]
)
def test_validate_biolink_curie_in_qualifier_constraints(query: Tuple[str, Dict, str]):
    qualifier_validator(
        tested_method=BiolinkValidator.validate_qualifier_constraints,
        edge_model="QEdge",
        query=query[1:],
        trapi_version=query[0]
    )


@pytest.mark.parametrize(
    "query",
    [
        (  # Query 0 - no 'qualifiers' key - since nullable: true, this should pass
            {},
            ""
        ),
        (  # Query 1 - 'qualifiers' value is nullable: true, this should pass
            {
                'qualifiers': None
            },
            ""
        ),
        (  # Query 2 - 'qualifiers' value is not an array - invalidated by TRAPI schema
            {
                'qualifiers': {}
            },
            "critical.trapi.validation"
        ),
        (  # Query 3 - empty 'qualifiers' array value - since nullable: true, this should pass
            {
                'qualifiers': []
            },
            ""
        ),
        (  # Query 4 - empty 'qualifier_set' entry - invalidated by TRAPI schema
            {
                'qualifiers': [{}]
            },
            "critical.trapi.validation"
        ),
        (  # Query 5 - 'qualifier_set' entry is not a dictionary - invalidated by TRAPI schema
            {
                'qualifiers': [[]]
            },
            "critical.trapi.validation"
        ),
        (  # Query 6 - 'qualifier' entry is missing its 'qualifier_type_id' property - invalidated by TRAPI schema
            {
                'qualifiers': [
                    {
                        # 'qualifier_type_id': "",
                        'qualifier_value': ""
                    }
                ]
            },
            "critical.trapi.validation"
        ),
        (  # Query 7 - 'qualifier_type_id' property value is unknown
            {
                'qualifiers': [
                    {
                        'qualifier_type_id': "biolink:unknown_qualifier",
                        'qualifier_value': "fake-qualifier-value"
                    }
                ]
            },
            "error.knowledge_graph.edge.qualifiers.qualifier.type_id.unknown"
        ),
        (  # Query 8 - 'qualifier_type_id' property value is valid but abstract
            {
                'qualifiers': [
                    {
                        'qualifier_type_id': "biolink:aspect_qualifier",
                        'qualifier_value': "stability"
                    }
                ]
            },
            # "info.query_graph.edge.qualifier.abstract"
            "error.knowledge_graph.edge.qualifiers.qualifier.value.unresolved"
        ),
        (  # Query 9 - 'qualifier_type_id' property value is not a Biolink qualifier term
            {
                'qualifiers': [
                    {
                        'qualifier_type_id': "biolink:related_to",
                        'qualifier_value': "fake-qualifier-value"
                    }
                ]
            },
            "error.knowledge_graph.edge.qualifiers.qualifier.type_id.unknown"
        ),
        (  # Query 10 - 'qualifier' entry is missing its 'qualifier_value' property - invalidated by TRAPI schema
            {
                'qualifiers': [
                    {
                        'qualifier_type_id': "biolink:object_direction_qualifier"
                    }
                ]
            },
            "critical.trapi.validation"
        ),
        (   # Query 11 - qualifier_type_id 'object_direction_qualifier' is a valid Biolink qualifier type and
            #            'upregulated' a valid corresponding 'permissible value' enum 'qualifier_value'
            {
                'qualifiers': [
                    {
                        'qualifier_type_id': "biolink:object_direction_qualifier",
                        'qualifier_value': "upregulated"
                    }
                ]
            },
            ""    # this particular use case should pass
        ),
        # (   # This use case was discussed with Sierra on 11 April 2023 and
        #     # decided to be out-of-scope of enum values for is_permissible_value_of_enum()
        #
        #     # Query ## - 'qualifier_type_id' is a valid Biolink qualifier type and 'RO:0002213'
        #     #            is an 'exact match' to a 'upregulated', the above 'qualifier_value'.
        #     #            This unit test won't pass without a modification of the Biolink Model Toolkit
        #     #            method for validating qualifier values to accept mapped values.
        #     {
        #         'qualifiers': [
        #             {
        #                 'qualifier_type_id': "biolink:object_direction_qualifier",
        #                 'qualifier_value': "RO:0002213"   # RO 'exact match' term for 'upregulated'
        #             }
        #         ]
        #     },
        #     ""
        # )
    ]
)
def test_validate_qualifiers(query: Tuple):
    qualifier_validator(
        tested_method=BiolinkValidator.validate_qualifiers,
        edge_model="Edge",
        query=query
    )


Q_NOT_A_CURIE = {
    'qualifiers': [
        {
            'qualifier_type_id': "not-a-curie",
            'qualifier_value': "fake-qualifier-value"
        }
    ]
}


@pytest.mark.parametrize(
    "query",
    [
        (  # Query 0 - 'qualifier_type_id' value not a Biolink CURIE - seen as 'unknown' in TRAPI < 1.4.0-beta
                TRAPI_1_3_0,
                Q_NOT_A_CURIE,
                "error.knowledge_graph.edge.qualifiers.qualifier.type_id.unknown"
        ),
        (  # Query 1 - 'qualifier_type_id' value not a Biolink CURIE - schema validation error in TRAPI < 1.4.0-beta
                TRAPI_1_4_0_BETA,
                Q_NOT_A_CURIE,
                "critical.trapi.validation"
        )
    ]
)
def test_validate_biolink_curie_in_qualifiers(query: Tuple[str, Dict, str]):
    qualifier_validator(
        tested_method=BiolinkValidator.validate_qualifiers,
        edge_model="Edge",
        query=query[1:],
        trapi_version=query[0]
    )


##################################
# Validate TRAPI Knowledge Graph #
##################################
@pytest.mark.parametrize(
    "query",
    [
        (
            LATEST_BIOLINK_MODEL_VERSION,  # Biolink Model Version

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
                               "attribute_source": "infores:hmdb",
                               "attribute_type_id": "biolink:aggregator_knowledge_source",
                               "attributes": [],
                               "description": "Molecular Data Provider",
                               "original_attribute_name": "biolink:aggregator_knowledge_source",
                               "value": "infores:molepro",
                               "value_type_id": "biolink:InformationResource"
                           }
                        ],
                       "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                       ]
                    }
                }
            },
            ""
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 1: Empty graph - caught by missing 'nodes' key
            {},
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Response returned an empty Message Knowledge Graph?"
            "warning.graph.empty"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 2: Empty nodes dictionary
            {
                "nodes": {}
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - No nodes found!"
            "error.knowledge_graph.nodes.empty"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
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
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - No edges found!"
            "error.knowledge_graph.edges.empty"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
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
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - No edges found!"
            "error.knowledge_graph.edges.empty"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 5: missing node 'categories' slot
            {
                "nodes": {
                    "NCBIGene:29974": {}
                },
                "edges": {
                   "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:physically_interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Node 'NCBIGene:29974' is missing its categories!"
            "error.knowledge_graph.node.category.missing"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Node 'NCBIGene:29974.categories' slot value is not an array!"
            "error.knowledge_graph.node.categories.not_array"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 7: Knowledge Graph 'categories' list values should include
            #          at least one (non-abstract, non-mixin) category term
            {
                "nodes": {
                    "UniProtKB:Q14191": {
                       "categories": ["biolink:GeneProductMixin"]
                    },
                    "CHEBI:18420": {
                        "name": "Magnesium",
                        "categories": ["biolink:SmallMolecule"]
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "UniProtKB:Q14191",
                        "predicate": "biolink:physically_interacts_with",
                        "object": "CHEBI:18420",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Node 'NCBIGene:29974.categories' slot value is not an array!"
            "error.knowledge_graph.node.categories.not_concrete"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 8: unknown category specified
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:NonsenseCategory"
                       ]
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:physically_interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Knowledge Graph Node element 'biolink:NonsenseCategory' is unknown!"
            "error.knowledge_graph.node.category.unknown"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 9: unknown category specified
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:BiologicalEntity"
                       ]
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:physically_interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Node has deprecated category!"
            "warning.knowledge_graph.node.category.abstract_or_mixin"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 10: abstract category in Knowledge Graphs? Itself ignored now during validation,
            #          although if at least one 'concrete' class is not given, other related
            #          validation errors (e.g. 'unmapped_prefix'?) may be reported?
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:Entity",
                           "biolink:Gene"
                       ]
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:physically_interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [
                            {
                                "attribute_type_id": "biolink:primary_knowledge_source",
                                "value": "infores:my-kp"
                            }
                        ],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            ""
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 11: mixin category in Knowledge Graphs? Itself ignored now during validation,
            #          although if at least one 'concrete' class is not given with id_prefix mappings,
            #          other related validation errors (e.g. 'unmapped_prefix'?) may be reported?
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:GeneOrGeneProduct",
                           "biolink:Gene"
                       ]
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:physically_interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [
                            {
                                "attribute_type_id": "biolink:primary_knowledge_source",
                                "value": "infores:my-kp"
                            }
                        ],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            ""
        ),
        # (   # no longer testable in Biolink 3.1.1 since Nutrient is
        #     # gone and no other deprecated categories in this release
        #     LATEST_BIOLINK_MODEL,
        #     # Query xx: deprecated category triggers a warning in Knowledge Graphs
        #     {
        #         "nodes": {
        #             "CHEBI:27300": {  # Vitamin D
        #                "categories": [
        #                    "biolink:Nutrient"
        #                ]
        #             },
        #             "Orphanet:120464": {  # Vitamin D Receptor
        #                "categories": [
        #                    "biolink:Protein"
        #                ]
        #             }
        #         },
        #         "edges": {
        #             "edge_1": {
        #                 "subject": "CHEBI:27300",
        #                 "predicate": "biolink:physically_interacts_with",
        #                 "object": "Orphanet:120464",
        #                 "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
        #             }
        #         }
        #     },
        #  f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Knowledge Graph Node element 'biolink:OntologyClass' is deprecated!"
        #     "warning.knowledge_graph.node.category.deprecated"
        # ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 12: invalid node CURIE prefix namespace, for specified category
            {
                "nodes": {
                    "FOO:1234": {
                       "categories": [
                           "biolink:Gene"
                       ],
                    },
                    "NCBIGene:29974": {
                        "categories": [
                            "biolink:Gene"
                        ]
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "FOO:1234",
                        "predicate": "biolink:physically_interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [
                            {
                                "attribute_type_id": "biolink:primary_knowledge_source",
                                "value": "infores:my-kp"
                            }
                        ],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Node 'FOO:1234' " +
            # "is unmapped to the target categories: ['biolink:Gene']?"
            "warning.knowledge_graph.node.id.unmapped_prefix"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 13: missing or empty subject, predicate, object values
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # ditto for predicate and object... but identical code pattern thus we only test missing subject id here
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge 'None--biolink:interacts_with->NCBIGene:29974' " +
            # "has a missing or empty 'subject' slot value!"
            "error.knowledge_graph.edge.subject.missing"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 14: 'subject' id is missing from the nodes catalog
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge 'subject' id 'NCBIGene:12345' is missing from the nodes catalog!"
            "error.knowledge_graph.edge.subject.missing_from_nodes"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 15: predicate is unknown
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Predicate element 'biolink:unknown_predicate' is unknown!"
            "error.knowledge_graph.edge.predicate.unknown"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 16: predicate is invalid - may be a valid Biolink element but is not a predicate
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
                        "predicate": "biolink:has_unit",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Predicate element 'biolink:has_unit' is invalid!"
            "error.knowledge_graph.edge.predicate.invalid"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 17: predicate is a mixin - not allowed in Knowledge Graphs
            {
                "nodes": {
                    "HGNC:3059": {
                       "categories": [
                           "biolink:Gene"
                       ]
                    },
                    "HGNC:391": {
                        "name": "AKT serine/threonine kinase 1",
                        "categories": [
                            "biolink:Gene"
                        ],
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "HGNC:3059",
                        "predicate": "biolink:increases_amount_or_activity_of",
                        "object": "HGNC:391",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # "{KNOWLEDGE_GRAPH_PREFIX}: ERROR -Predicate element 'biolink:increases_amount_or_activity of' is a mixin!"
            "error.knowledge_graph.edge.predicate.mixin"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 18: predicate is abstract - not allowed in Knowledge Graphs
            {
                "nodes": {
                    "PMID:1234": {
                       "categories": [
                           "biolink:InformationContentEntity"
                       ]
                    },
                    "ORCID:56789": {
                        "name": "cytosine",
                        "categories": [
                            "biolink:Agent"
                        ],
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "PMID:1234",
                        "predicate": "biolink:contributor",
                        "object": "ORCID:56789",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Predicate element 'biolink:contributor' is abstract!"
            "error.knowledge_graph.edge.predicate.abstract"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 19: predicate is non-canonical
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
                        "predicate": "biolink:affected_by",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Edge predicate 'biolink:affected_by' is non-canonical?"
            "warning.knowledge_graph.edge.predicate.non_canonical"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 20: 'object' id is missing from the nodes catalog
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "PUBCHEM.COMPOUND:678",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge 'object' id " +
            # f"'PUBCHEM.COMPOUND:678' is missing from the nodes catalog!"
            "error.knowledge_graph.edge.object.missing_from_nodes"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 21: attribute 'attribute_type_id' is missing
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"value": "some value"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge attribute is missing its 'attribute_type_id' key!"
            "error.knowledge_graph.edge.attribute.type_id.missing"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 22: attribute 'value' is missing?
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge attribute is missing its 'value' key!"
            "error.knowledge_graph.edge.attribute.value.missing"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 23: 'attribute_type_id' is not a CURIE
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"attribute_type_id": "not_a_curie", "value": "some value"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge attribute_type_id 'not_a_curie' is not a CURIE!"
            "error.knowledge_graph.edge.attribute.type_id.not_curie"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 24: 'attribute_type_id' is not a 'biolink:association_slot' (biolink:synonym is a node property)
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"attribute_type_id": "biolink:synonym", "value": "some synonym"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Edge attribute_type_id "
            # "'biolink:synonym' is not a biolink:association_slot?"
            "warning.knowledge_graph.edge.attribute.type_id.not_association_slot"
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 25: 'attribute_type_id' has a 'biolink' CURIE prefix and is an association_slot, so it should pass
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [
                            {"attribute_type_id": "biolink:negated", "value": "some value"},
                            {"attribute_type_id": "biolink:primary_knowledge_source", "value": "infores:hmdb"}
                        ],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            ""  # this should recognize the 'attribute_type_id' as a Biolink CURIE
        ),
        (
            LATEST_BIOLINK_MODEL_VERSION,
            # Query 26: 'attribute_type_id' has a CURIE prefix namespace unknown to Biolink?
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"attribute_type_id": "foo:bar", "value": "some value"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Edge attribute_type_id 'foo:bar' " +
            # f"has a CURIE prefix namespace unknown to Biolink!"
            "warning.knowledge_graph.edge.attribute.type_id.non_biolink_prefix"
        ),
        (   # Query 27:  # An earlier Biolink Model won't recognize a category not found in its specified release
            "1.8.2",
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
                            "biolink:SmallMolecule"  # Not valid in the latest model?
                        ],
                    }
                },
                # Sample edge
                'edges': {
                   "edge_1": {
                       "subject": "NCBIGene:29974",
                       "predicate": "biolink:physically_interacts_with",
                       "object": "PUBCHEM.COMPOUND:597",
                    }
                }
            },
            "error.knowledge_graph.node.category.unknown"
        ),
        (   # Query 28:  #'attribute_type_id' has a CURIE prefix namespace unknown to Biolink but...
            SUPPRESS_BIOLINK_MODEL_VALIDATION,
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"attribute_type_id": "foo:bar", "value": "some value"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # ...since Biolink Model validation is tagged as 'suppress',
            # we  don't expect any validation output here?
            ""
        ),
        (
            SUPPRESS_BIOLINK_MODEL_VALIDATION,
            # Query 29: 'attribute_type_id' is not a 'biolink:association_slot'
            #           (biolink:synonym is a node property) but...
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"attribute_type_id": "biolink:synonym", "value": "some synonym"}],
                        "sources": [
                            {
                                "resource_id": "infores:molepro",
                                "resource_role": "primary_knowledge_source"
                            }
                        ]
                    }
                }
            },
            # ...since Biolink Model validation is tagged as 'suppress',
            # we  don't expect any validation output here?
            ""
        )
    ]
)
def test_check_biolink_model_compliance_of_knowledge_graph(query: Tuple):
    validator: BiolinkValidator = check_biolink_model_compliance_of_knowledge_graph(
        graph=query[1], biolink_version=query[0]
    )
    check_messages(validator, query[2])


MESSAGE_EDGE_WITHOUT_ATTRIBUTES = {
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
            "predicate": "biolink:physically_interacts_with",
            "object": "PUBCHEM.COMPOUND:597",
            # "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
        }
    }
}


def test_pre_trapi_1_4_0_validate_attributes():
    # message edges must have at least some 'provenance' attributes
    edge_without_attributes = deepcopy(MESSAGE_EDGE_WITHOUT_ATTRIBUTES)
    validator: BiolinkValidator = check_biolink_model_compliance_of_knowledge_graph(
        graph=edge_without_attributes,
        trapi_version=TRAPI_1_3_0,
        biolink_version=LATEST_BIOLINK_MODEL_VERSION
    )
    check_messages(validator, "error.knowledge_graph.edge.attribute.missing")


def test_suppress_biolink_validation_pre_trapi_1_4_0_validate_attributes():
    # message edges must have at least some 'provenance' attributes
    edge_without_attributes = deepcopy(MESSAGE_EDGE_WITHOUT_ATTRIBUTES)
    validator: BiolinkValidator = check_biolink_model_compliance_of_knowledge_graph(
        graph=edge_without_attributes,
        trapi_version=TRAPI_1_3_0,
        biolink_version=SUPPRESS_BIOLINK_MODEL_VALIDATION
    )
    check_messages(validator, "")


SAMPLE_PRIMARY_RETRIEVAL_SOURCE = {
    # required, infores CURIE to an Information Resource
    "resource_id": "infores:chebi",

    # required, string drawn from the TRAPI ResourceRoleEnum
    # values that were formerly recorded as TRAPI attributes
    # are now presented as first class edge annotation
    "resource_role": "primary_knowledge_source",

    # nothing upstream... it' primary!
    "upstream_resource_ids": []
}

SAMPLE_KP_RETRIEVAL_SOURCE = {
    # required, infores CURIE to an Information Resource
    "resource_id": "infores:molepro",

    # required, string drawn from the TRAPI ResourceRoleEnum
    # values that were formerly recorded as TRAPI attributes
    # are now presented as first class edge annotation
    "resource_role": "aggregator_knowledge_source",

    # primary knowledge source is 'upstream'
    "upstream_resource_ids": ["infores:chebi"]
}

SAMPLE_ARA_RETRIEVAL_SOURCE = {
    # required, infores CURIE to an Information Resource
    "resource_id": "infores:arax",

    # required, string drawn from the TRAPI ResourceRoleEnum
    # values that were formerly recorded as TRAPI attributes
    # are now presented as first class edge annotation
    "resource_role": "aggregator_knowledge_source",

    # KP is 'upstream'
    "upstream_resource_ids": ["infores:molepro"]
}

SAMPLE_SOURCES_ARRAY = [
    SAMPLE_PRIMARY_RETRIEVAL_SOURCE,
    SAMPLE_KP_RETRIEVAL_SOURCE,
    SAMPLE_ARA_RETRIEVAL_SOURCE
]

SAMPLE_RETRIEVAL_SOURCE_EMPTY_RESOURCE_ID = {
    # required, string drawn from the TRAPI ResourceRoleEnum
    # values that were formerly recorded as TRAPI attributes
    # are now presented as first class edge annotation
    "resource_role": "primary_knowledge_source"
}

SAMPLE_RETRIEVAL_SOURCE_EMPTY_RESOURCE_ROLE = {
    # required, infores CURIE to an Information Resource
    "resource_id": "infores:molepro",
}

SAMPLE_RETRIEVAL_SOURCE_RESOURCE_ID_NOT_CURIE = {
    # required, infores CURIE to an Information Resource
    "resource_id": "molepro",

    # required, string drawn from the TRAPI ResourceRoleEnum
    # values that were formerly recorded as TRAPI attributes
    # are now presented as first class edge annotation
    "resource_role": "primary_knowledge_source"
}

SAMPLE_RETRIEVAL_SOURCE_RESOURCE_ID_INFORES_INVALID = {
    # required, infores CURIE to an Information Resource
    "resource_id": "not-an-infores:molepro",

    # required, string drawn from the TRAPI ResourceRoleEnum
    # values that were formerly recorded as TRAPI attributes
    # are now presented as first class edge annotation
    "resource_role": "primary_knowledge_source"
}

SAMPLE_RETRIEVAL_SOURCE_RESOURCE_ID_INFORES_UNKNOWN = {
    # required, infores CURIE to an Information Resource
    "resource_id": "infores:my-favorite-kp",

    # required, string drawn from the TRAPI ResourceRoleEnum
    # values that were formerly recorded as TRAPI attributes
    # are now presented as first class edge annotation
    "resource_role": "primary_knowledge_source"
}


def test_build_source_trail():
    sources: Dict[str, List[str]] = {
        "infores:chebi": [],
        "infores:biothings-explorer": ["infores:chebi"],
        "infores:molepro": ["infores:biothings-explorer"],
        "infores:arax": ["infores:molepro"]
    }
    assert BiolinkValidator.build_source_trail(sources) == \
           "infores:chebi -> infores:biothings-explorer -> infores:molepro -> infores:arax"

    # even though a primary_knowledge_source appears to be missing
    # we are able to infer a path on a putative primary source
    sources: Optional[Dict[str, List[str]]] = {
        "infores:biothings-explorer": ["infores:chebi"],
        "infores:molepro": ["infores:biothings-explorer"],
        "infores:arax": ["infores:molepro"]
    }
    assert BiolinkValidator.build_source_trail(sources) == \
           "infores:chebi -> infores:biothings-explorer -> infores:molepro -> infores:arax"


@pytest.mark.parametrize(
    "sources,validation_code",
    [
        ([SAMPLE_PRIMARY_RETRIEVAL_SOURCE], ""),  # No validation code generated?
        ([SAMPLE_KP_RETRIEVAL_SOURCE], "error.knowledge_graph.edge.provenance.missing_primary"),
        ([SAMPLE_ARA_RETRIEVAL_SOURCE], "error.knowledge_graph.edge.provenance.missing_primary"),
        (SAMPLE_SOURCES_ARRAY, ""),             # No validation code generated?
        (None, "error.knowledge_graph.edge.sources.missing"),
        ([], "error.knowledge_graph.edge.sources.empty"),
        ("not-an-array", "error.knowledge_graph.edge.sources.not_array"),
        (
            [SAMPLE_RETRIEVAL_SOURCE_EMPTY_RESOURCE_ID],
            "error.knowledge_graph.edge.sources.retrieval_source.resource_id.empty"
        ),
        (
            [SAMPLE_RETRIEVAL_SOURCE_EMPTY_RESOURCE_ROLE],
            "error.knowledge_graph.edge.sources.retrieval_source.resource_role.empty"
        ),
        (
            [SAMPLE_RETRIEVAL_SOURCE_RESOURCE_ID_NOT_CURIE],
            "error.knowledge_graph.edge.sources.retrieval_source.resource_id.infores.not_curie"
        ),
        (
            [SAMPLE_RETRIEVAL_SOURCE_RESOURCE_ID_INFORES_INVALID],
            "error.knowledge_graph.edge.sources.retrieval_source.resource_id.infores.invalid"
        ),
        # TODO: need method to determine if an infores is known with recent changes to BMT
        # (
        #     [SAMPLE_RETRIEVAL_SOURCE_RESOURCE_ID_INFORES_UNKNOWN],
        #     "error.knowledge_graph.edge.sources.retrieval_source.resource_id.infores.unknown"
        # )
    ]
)
def test_latest_trapi_validate_sources(sources: bool, validation_code: str):
    # no attributes are strictly needed in 1.4.0-beta now that (mandatory)
    # Edge provenance is recorded in the Edge.sources list of RetrievalSource
    # message edges must have at least some 'provenance' attributes
    sample_message = deepcopy(MESSAGE_EDGE_WITHOUT_ATTRIBUTES)
    if sources is not None:
        edge = sample_message["edges"]["edge_1"]
        edge["sources"] = sources
    validator: BiolinkValidator = check_biolink_model_compliance_of_knowledge_graph(
        graph=sample_message,
        # trapi_version="latest",  # 1.4.0++
        biolink_version=LATEST_BIOLINK_MODEL_VERSION
    )
    check_messages(validator, validation_code)


@pytest.mark.parametrize(
    "predicate,result",
    [
        (None, False),
        ("biolink:related_to", True),
        ("related_to", True),
        ("related to", True),
        ("biolink:active_in", False),
        ("active_in", False),
        ("active in", False),
        ("biolink:has_active_component", False)
    ]
)
def test_is_symmetric(predicate, result):
    # we assume the default is a late version which has proper inverse
    validator: BiolinkValidator = BiolinkValidator(TRAPIGraphType.Knowledge_Graph, biolink_version=None)
    assert validator.is_symmetric(predicate) == result


@pytest.mark.parametrize(
    "predicate,inverse",
    [
        (None, None),
        ("", None),
        ("biolink:related_to", "biolink:related_to"),
        ("related_to", "biolink:related_to"),
        ("related to", "biolink:related_to"),
        ("biolink:active_in", "biolink:has_active_component"),
        ("active_in", "biolink:has_active_component"),
        ("active in", "biolink:has_active_component"),
        ("biolink:has_active_component", "biolink:active_in")
    ]
)
def test_get_inverse_predicate(predicate, inverse):
    # we assume the default is a late version which has proper inverse
    validator: BiolinkValidator = BiolinkValidator(TRAPIGraphType.Knowledge_Graph, biolink_version=None)
    assert validator.get_inverse_predicate(predicate) == inverse
