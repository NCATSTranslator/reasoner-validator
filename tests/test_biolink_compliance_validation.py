"""
Unit tests for the generic (shared) components of the SRI Testing Framework
"""
from typing import Tuple, Optional, Dict
from pprint import PrettyPrinter
import logging
import pytest
from sys import stderr
from bmt import Toolkit
from linkml_runtime.linkml_model import SlotDefinition

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

# October 19, 2022 - as of reasoner-validator 3.1.0, we don't pretend to totally support Biolink Models
# any earlier than 3.0.3.  If earlier biolink model compliance testing is desired,
# then perhaps reasoner-validator version 3.0.5 or earlier can be used.
LATEST_BIOLINK_MODEL = "3.0.3"


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
        (   # Query 1 - Missing subject category
            LATEST_BIOLINK_MODEL,
            {
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Subject has a missing Biolink category!"
            "error.input_edge.node.category.missing"
        ),
        (   # Query 2 - Invalid subject category
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:NotACategory',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Subject element 'biolink:NotACategory' is unknown!"
            "error.input_edge.node.category.unknown"
        ),
        (   # Query 3 - Missing object category
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Object has a missing Biolink category!"
            "error.input_edge.node.category.missing"
        ),
        (   # Query 4 - Invalid object category
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:NotACategory',
                'predicate': 'biolink:subclass_of',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Object element 'biolink:NotACategory' is unknown!"
            "error.input_edge.node.category.unknown"
        ),
        (   # Query 5 - Missing predicate
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Predicate is missing or empty!"
            "error.input_edge.predicate.missing"
        ),
        (   # Query 6 - Empty predicate
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': '',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Predicate is missing or empty!"
            "error.input_edge.predicate.missing"
        ),
        (   # Query 7 - Predicate is deprecated
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:Drug',
                'object_category': 'biolink:Protein',
                'predicate': 'biolink:has_real_world_evidence_of_association_with',
                'subject': 'NDC:0002-8215-01',  # a form of insulin
                'object': 'MONDO:0005148'  # type 2 diabetes?
            },
            # f"{INPUT_EDGE_PREFIX}: WARNING - Predicate element " +
            # "'has_real_world_evidence_of_association_with' is deprecated?"
            "warning.input_edge.edge.predicate.deprecated"
        ),
        (   # Query 8 - Predicate is abstract
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:InformationContentEntity',
                'object_category': 'biolink:Agent',
                'predicate': 'biolink:contributor',
                'subject': 'PMID:1234',
                'object': 'ORCID:56789'
            },
            # f"{INPUT_EDGE_PREFIX}: INFO - Predicate element 'biolink:contributor' is abstract."
            "info.input_edge.edge.predicate.abstract"
        ),
        (   # Query 9 - Predicate is a mixin
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:regulates',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: INFO - Predicate element 'biolink:regulates' is a mixin."
            "info.input_edge.edge.predicate.mixin"
        ),
        (   # Query 10 - Unknown predicate element
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:not_a_predicate',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Predicate element 'biolink:not_a_predicate' is unknown!"
            "error.input_edge.edge.predicate.unknown"
        ),
        (   # Query 11 - Invalid or unknown predicate
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:has_unit',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Predicate element 'biolink:has_unit' is inavlid!"
            "error.input_edge.edge.predicate.invalid"
        ),
        (   # Query 12 - Non-canonical directed predicate
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:SmallMolecule',
                'object_category': 'biolink:Disease',
                'predicate': 'biolink:affected_by',
                'subject': 'DRUGBANK:DB00331',
                'object': 'MONDO:0005148'
            },
            # f"{INPUT_EDGE_PREFIX}: WARNING - Edge predicate 'biolink:affected_by' is non-canonical?"
            "warning.input_edge.edge.predicate.non_canonical"
        ),
        (   # Query 13 - Missing subject
            LATEST_BIOLINK_MODEL,  # Biolink Model Version
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'object': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Subject node identifier is missing!"
            "error.input_edge.node.id.missing"
        ),
        (   # Query 14 - Unmappable subject namespace
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'FOO:0005453',
                'object': 'UBERON:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: WARNING - Subject node identifier 'FOO:0005453' " +
            # "is unmapped to 'biolink:AnatomicalEntity'?"
            "warning.input_edge.node.id.unmapped_to_category"
        ),
        (   # Query 15 - missing object
            LATEST_BIOLINK_MODEL,  # Biolink Model Version
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': "UBERON:0005453"
            },
            # f"{INPUT_EDGE_PREFIX}: ERROR - Object node identifier is missing!"
            "error.input_edge.node.id.missing"
        ),
        (   # Query 16 - Unmappable object namespace
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'UBERON:0005453',
                'object': 'BAR:0035769'
            },
            # f"{INPUT_EDGE_PREFIX}: WARNING - Object node identifier 'BAR:0035769' " +
            # "is unmapped to 'biolink:AnatomicalEntity'?"
            "warning.input_edge.node.id.unmapped_to_category"
        ),
        (   # Query 17 - Valid other model
            "1.8.2",
            {
                'subject_category': 'biolink:ChemicalSubstance',
                'object_category': 'biolink:Protein',
                'predicate': 'biolink:entity_negatively_regulates_entity',
                'subject': 'DRUGBANK:DB00945',
                'object': 'UniProtKB:P23219'
            },
            ""
        ),
        (   # Query 18 - Deprecated
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:Nutrient',
                'object_category': 'biolink:Protein',
                'predicate': 'biolink:physically_interacts_with',
                'subject': 'CHEBI:27300',
                'object': 'Orphanet:120464'
            },
            # f"{INPUT_EDGE_PREFIX}: WARNING - Subject 'biolink:Nutrient' is deprecated?"
            "warning.input_edge.node.category.deprecated"
        ),
        (   # Query 19 - inform that the input category is a mixin?
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:GeneOrGeneProduct',
                'object_category': 'biolink:Protein',
                'predicate': 'biolink:related_to',
                'subject': 'HGNC:9604',
                'object': 'UniProtKB:P23219'
            },
            # f"{INPUT_EDGE_PREFIX}: INFO - Subject element 'biolink:GeneOrGeneProduct' is a mixin."
            "info.input_edge.node.category.mixin"
        ),
        (   # Query 20 - inform that the input category is abstract?
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AdministrativeEntity',
                'object_category': 'biolink:Agent',
                'predicate': 'biolink:related_to',
                'subject': 'isbn:1234',
                'object': 'ORCID:1234'
            },
            # f"{INPUT_EDGE_PREFIX}: INFO - Subject element 'biolink:AdministrativeEntity' is abstract."
            "info.input_edge.node.category.abstract"
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
            # Query Graphs can have empty 'nodes', so we should just issue a warning
            # f"{QUERY_GRAPH_PREFIX}: WARNING - Empty graph!"
            "warning.graph.empty"
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
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Node 'type-2 diabetes.ids' slot value is not an array!"
            "error.query_graph.node.ids.not_array"
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
            ""
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
            # f"{QUERY_GRAPH_PREFIX}: ERROR - Node 'NCBIGene:29974.categories' slot value is not an array!"
            "error.query_graph.node.categories.not_array"
        ),
        (
            LATEST_BIOLINK_MODEL,
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
            LATEST_BIOLINK_MODEL,
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
            LATEST_BIOLINK_MODEL,
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
            LATEST_BIOLINK_MODEL,
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
            LATEST_BIOLINK_MODEL,
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
            LATEST_BIOLINK_MODEL,
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
            LATEST_BIOLINK_MODEL,
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
            LATEST_BIOLINK_MODEL,
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
            LATEST_BIOLINK_MODEL,
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
            LATEST_BIOLINK_MODEL,
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
            LATEST_BIOLINK_MODEL,
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
            LATEST_BIOLINK_MODEL,
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
            LATEST_BIOLINK_MODEL,
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
            "warning.query_graph.node.ids.unmapped_to_categories"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 21: Abstract category in query graph
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
            # f"{QUERY_GRAPH_PREFIX}: INFO - Query Graph Node element 'biolink:BiologicalEntity' is abstract."
            "info.query_graph.node.category.abstract"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 22: Mixin category in query graph
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
            # f"{QUERY_GRAPH_PREFIX}: INFO - Query Graph Node element 'biolink:ChemicalOrDrugOrTreatment' is a mixin."
            "info.query_graph.node.category.mixin"
        ),
        (
            LATEST_BIOLINK_MODEL,
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


@pytest.mark.parametrize(
    "query",
    [
        # (
        #         "mock_edge",  # mock data has dumb edges: don't worry about the S-P-O, just the attributes
        #         "mock_context",
        #         "AssertError_message"
        # ),   # set 3rd argument to AssertError message if test edge should 'fail'; otherwise, empty string (for pass)
        (
            # Query 0. 'attributes' key missing in edge record is None
            {},
            get_ara_test_case(),
            # "Edge has no 'attributes' key!"
            "error.knowledge_graph.edge.attribute.missing"
        ),
        (
            # Query 1. Empty attributes
            {
                "attributes": None
            },
            get_ara_test_case(),
            # "Edge has empty attributes!"
            "error.knowledge_graph.edge.attribute.empty"
        ),
        (
            # Query 2. Empty attributes
            {
                "attributes": []
            },
            get_ara_test_case(),
            # "Edge has empty attributes!"
            "error.knowledge_graph.edge.attribute.empty"
        ),
        (
            # Query 3. Empty attributes
            {
                "attributes": {"not_a_list"}
            },
            get_ara_test_case(),
            # "Edge attributes are not an array!"
            "error.knowledge_graph.edge.attribute.not_array"
        ),
        (
            # Query 4. attribute missing its 'attribute_type_id' field
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
            # Query 5. attribute missing its 'value' field
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
            # Query 6. Missing ARA knowledge source provenance?
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
            # Query 7. value is an empty list?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": []
                    },
                ]
            },
            get_ara_test_case(),
            # "value is an empty list!"
            "error.knowledge_graph.edge.attribute.value.empty"
        ),
        (
            # Query 8. KP provenance value is not a well-formed InfoRes CURIE? Should fail?
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
            # Query 9. KP provenance value is not a well-formed InfoRes CURIE? Should fail?
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
            # Query 10. KP provenance value is missing?
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
            # Query 11. kp type is 'original'. Should draw a WARNING about deprecation
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "infores:aragorn"
                    },
                    {
                        "attribute_type_id": "biolink:original_knowledge_source",
                        "value": "infores:panther"
                    }
                ]
            },
            get_ara_test_case(),
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Attribute Type ID element " +
            # "'biolink:original_knowledge_source' is deprecated?"
            "warning.knowledge_graph.attribute.type_id.deprecated"
        ),
        (
            # Query 12. kp type is 'primary'. Should pass?
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
            # Query 13. Missing 'primary' nor 'original' knowledge source
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
            "warning.knowledge_graph.edge.provenance.missing_primary"
        ),
        (
            # Query 14. Is complete and should pass?
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
def test_validate_attributes(query: Tuple):
    validator = BiolinkValidator(
        graph_type=TRAPIGraphType.Knowledge_Graph,
        biolink_version=LATEST_BIOLINK_MODEL,
        sources=query[1]
    )
    validator.validate_attributes(edge=query[0])
    check_messages(validator, query[2])


##################################
# Validate TRAPI Knowledge Graph #
##################################
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
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Response returned an empty Message Knowledge Graph?"
            "warning.graph.empty"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 2: Empty nodes dictionary
            {
                "nodes": {}
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - No nodes found!"
            "error.knowledge_graph.nodes.empty"
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
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - No edges found!"
            "error.knowledge_graph.edges.empty"
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
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - No edges found!"
            "error.knowledge_graph.edges.empty"
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Node 'NCBIGene:29974' is missing its categories!"
            "error.knowledge_graph.node.category.missing"
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
                        "predicate": "biolink:physically_interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Node 'NCBIGene:29974.categories' slot value is not an array!"
            "error.knowledge_graph.node.categories.not_array"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 7: unknown category specified
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Knowledge Graph Node element 'biolink:NonsenseCategory' is unknown!"
            "error.knowledge_graph.node.category.unknown"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 8: abstract category not allowed in Knowledge Graphs
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:AdministrativeEntity"
                       ]
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:physically_interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Knowledge Graph Node element " +
            # "'biolink:AdministrativeEntity' is abstract!"
            "error.knowledge_graph.node.category.abstract"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 9: mixin category not allowed in Knowledge Graphs
            {
                "nodes": {
                    "NCBIGene:29974": {
                       "categories": [
                           "biolink:GeneOrGeneProduct"
                       ]
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "NCBIGene:29974",
                        "predicate": "biolink:physically_interacts_with",
                        "object": "NCBIGene:29974",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Knowledge Graph Node element 'biolink:GeneOrGeneProduct' is a mixin!"
            "error.knowledge_graph.node.category.mixin"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 10: deprecated category triggers a warning in Knowledge Graphs
            {
                "nodes": {
                    "CHEBI:27300": {  # Vitamin D
                       "categories": [
                           "biolink:Nutrient"
                       ]
                    },
                    "Orphanet:120464": {  # Vitamin D Receptor
                       "categories": [
                           "biolink:Protein"
                       ]
                    }
                },
                "edges": {
                    "edge_1": {
                        "subject": "CHEBI:27300",
                        "predicate": "biolink:physically_interacts_with",
                        "object": "Orphanet:120464",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Knowledge Graph Node element 'biolink:OntologyClass' is deprecated!"
            "warning.knowledge_graph.node.category.deprecated"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 11: invalid node CURIE prefix namespace, for specified category
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
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Node 'FOO:1234' " +
            # "is unmapped to the target categories: ['biolink:Gene']?"
            "warning.knowledge_graph.node.unmapped_prefix"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 12: missing or empty subject, predicate, object values
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # ditto for predicate and object... but identical code pattern thus we only test missing subject id here
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge 'None--biolink:interacts_with->NCBIGene:29974' " +
            # "has a missing or empty 'subject' slot value!"
            "error.knowledge_graph.edge.subject.missing"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 13: 'subject' id is missing from the nodes catalog
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge 'subject' id 'NCBIGene:12345' is missing from the nodes catalog!"
            "error.knowledge_graph.edge.subject.missing_from_nodes"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 14: predicate is unknown
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Predicate element 'biolink:unknown_predicate' is unknown!"
            "error.knowledge_graph.edge.predicate.unknown"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 15: predicate is invalid - may be a valid Biolink element but is not a predicate
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Predicate element 'biolink:has_unit' is invalid!"
            "error.knowledge_graph.edge.predicate.invalid"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 16: predicate is a mixin - not allowed in Knowledge Graphs
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
                        "predicate": "biolink:regulated_by",
                        "object": "PUBCHEM.COMPOUND:597",
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Predicate element 'biolink:regulated_by' is a mixin!"
            "error.knowledge_graph.edge.predicate.mixin"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 17: predicate is abstract - not allowed in Knowledge Graphs
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Predicate element 'biolink:contributor' is abstract!"
            "error.knowledge_graph.edge.predicate.abstract"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 18: predicate is non-canonical
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Edge predicate 'biolink:affected_by' is non-canonical?"
            "warning.knowledge_graph.edge.predicate.non_canonical"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 19: 'object' id is missing from the nodes catalog
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge 'object' id " +
            # f"'PUBCHEM.COMPOUND:678' is missing from the nodes catalog!"
            "error.knowledge_graph.edge.object.missing_from_nodes"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 20: attribute 'attribute_type_id' is missing
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
                        "attributes": [{"value": "some value"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge attribute is missing its 'attribute_type_id' key!"
            "error.knowledge_graph.edge.attribute.type_id.missing"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 21: attribute 'value' is missing?
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge attribute is missing its 'value' key!"
            "error.knowledge_graph.edge.attribute.value.missing"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 22: 'attribute_type_id' is not a CURIE
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
                        "attributes": [{"attribute_type_id": "not_a_curie", "value": "some value"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge attribute_type_id 'not_a_curie' is not a CURIE!"
            "error.knowledge_graph.edge.attribute.type_id.not_curie"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 23: 'attribute_type_id' is not a 'biolink:association_slot' (biolink:synonym is a node property)
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
                        "attributes": [{"attribute_type_id": "biolink:synonym", "value": "some synonym"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Edge attribute_type_id "
            # "'biolink:synonym' is not a biolink:association_slot?"
            "warning.knowledge_graph.edge.attribute.type_id.not_association_slot"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 24: 'attribute_type_id' has a 'biolink' CURIE prefix and is an association_slot so it should pass
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
                        ]
                    }
                }
            },
            ""  # this should recognize the 'attribute_type_id' as a Biolink CURIE
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 25: 'attribute_type_id' has a CURIE prefix namespace unknown to Biolink?
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
                        "attributes": [{"attribute_type_id": "foo:bar", "value": "some value"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Edge attribute_type_id 'foo:bar' " +
            # f"has a CURIE prefix namespace unknown to Biolink!"
            "warning.knowledge_graph.edge.attribute.type_id.unknown_prefix"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 26: has missing or empty attributes?
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
                        # "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge has no 'attributes' key!"
            "error.knowledge_graph.edge.attribute.missing"
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
                        ]
                    }
                }
            },
            # f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Knowledge Graph Node element 'biolink:SmallMolecule' is unknown!"
            "error.knowledge_graph.node.category.unknown"
        )
    ]
)
def test_check_biolink_model_compliance_of_knowledge_graph(query: Tuple):
    validator: BiolinkValidator = check_biolink_model_compliance_of_knowledge_graph(
        graph=query[1], biolink_version=query[0]
    )
    check_messages(validator, query[2])
