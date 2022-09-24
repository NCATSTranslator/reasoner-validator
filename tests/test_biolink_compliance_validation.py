"""
Unit tests for the generic (shared) components of the SRI Testing Framework
"""
from typing import Tuple, Optional, Dict, Union
from pprint import PrettyPrinter
import logging
import pytest
from sys import stderr
from bmt import Toolkit

from reasoner_validator.report import ValidationReporter
from reasoner_validator.biolink import (
    TRAPIGraphType,
    BiolinkValidator,
    get_biolink_model_toolkit,
    check_biolink_model_compliance_of_input_edge,
    check_biolink_model_compliance_of_query_graph,
    check_biolink_model_compliance_of_knowledge_graph,
    check_biolink_model_compliance_of_trapi_response
)

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

pp = PrettyPrinter(indent=4)

# "Latest" Biolink Model Version (in the BM 2 series)
# Note: different BMT versions may have different defaults, e.g. 2.2.16 in BMT 0.8.4
# TODO: updating this to 3.0.1 will break a few things in the test, e.g. the test for non-canonical
LATEST_BIOLINK_MODEL = "2.4.8"


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
    assert not tk.get_inverse(predicate.name)
    tk: Toolkit = get_biolink_model_toolkit("v2.4.8")
    predicate = tk.get_element("biolink:active_in")
    assert not predicate['symmetric']
    assert tk.get_inverse(predicate.name) == "has active component"


def check_messages(validator: ValidationReporter, query):
    messages: Dict = validator.get_messages()
    if query:
        if 'ERROR' in query:
            assert any([error == query for error in messages['errors']])
        elif 'WARNING' in query:
            assert any([warning == query for warning in messages['warnings']])
        elif 'INFO' in query:
            assert any([info == query for info in messages['information']])
    else:  # no errors or warnings expected? Assert absence of such messages?
        assert not (messages['errors'] or messages['warnings'] or messages['information']), \
            f"Unexpected messages seen {messages}"


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
            f"{INPUT_EDGE_PREFIX}: ERROR - Subject has a missing Biolink category!"
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
            f"{INPUT_EDGE_PREFIX}: ERROR - Subject element 'biolink:NotACategory' is unknown!"
        ),
        (   # Query 3 - Missing object category
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            f"{INPUT_EDGE_PREFIX}: ERROR - Object has a missing Biolink category!"
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
            f"{INPUT_EDGE_PREFIX}: ERROR - Object element 'biolink:NotACategory' is unknown!"
        ),
        (   # Query 5 - Missing predicate
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            f"{INPUT_EDGE_PREFIX}: ERROR - Predicate is missing or empty!"
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
            f"{INPUT_EDGE_PREFIX}: ERROR - Predicate is missing or empty!"
        ),
        (   # Query 7 - Predicate is deprecated
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:Drug',
                'object_category': 'biolink:Disease',
                'predicate': 'biolink:approved_to_treat',
                'subject': 'NDC:0002-8215-01',  # a form of insulin
                'object': 'MONDO:0005148'  # type 2 diabetes?
            },
            f"{INPUT_EDGE_PREFIX}: WARNING - Predicate element 'biolink:approved_to_treat' is deprecated?"
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
            f"{INPUT_EDGE_PREFIX}: INFO - Predicate element 'biolink:contributor' is abstract."
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
            f"{INPUT_EDGE_PREFIX}: INFO - Predicate element 'biolink:regulates' is a mixin."
        ),
        (   # Query 10 - Invalid or unknown predicate
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:not_a_predicate',
                'subject': 'UBERON:0005453',
                'object': 'UBERON:0035769'
            },
            f"{INPUT_EDGE_PREFIX}: ERROR - Predicate element 'biolink:not_a_predicate' is unknown!"
        ),
        (   # Query 11 - Non-canonical directed predicate
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:SmallMolecule',
                'object_category': 'biolink:Disease',
                'predicate': 'biolink:affected_by',
                'subject': 'DRUGBANK:DB00331',
                'object': 'MONDO:0005148'
            },
            f"{INPUT_EDGE_PREFIX}: WARNING - Predicate 'biolink:affected_by' is non-canonical?"
        ),
        (   # Query 12 - Missing subject
            LATEST_BIOLINK_MODEL,  # Biolink Model Version
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'object': 'UBERON:0035769'
            },
            f"{INPUT_EDGE_PREFIX}: ERROR - Subject node identifier is missing!"
        ),
        (   # Query 13 - Unmappable subject namespace
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'FOO:0005453',
                'object': 'UBERON:0035769'
            },
            f"{INPUT_EDGE_PREFIX}: WARNING - Subject node identifier 'FOO:0005453' " +
            "is unmapped to 'biolink:AnatomicalEntity'?"
        ),
        (   # Query 14 - missing object
            LATEST_BIOLINK_MODEL,  # Biolink Model Version
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': "UBERON:0005453"
            },
            f"{INPUT_EDGE_PREFIX}: ERROR - Object node identifier is missing!"
        ),
        (   # Query 15 - Unmappable object namespace
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AnatomicalEntity',
                'object_category': 'biolink:AnatomicalEntity',
                'predicate': 'biolink:subclass_of',
                'subject': 'UBERON:0005453',
                'object': 'BAR:0035769'
            },
            f"{INPUT_EDGE_PREFIX}: WARNING - Object node identifier 'BAR:0035769' " +
            "is unmapped to 'biolink:AnatomicalEntity'?"
        ),
        (   # Query 16 - Valid other model
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
        (   # Query 17 - Deprecated
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:ChemicalSubstance',
                'object_category': 'biolink:Protein',
                'predicate': 'biolink:entity_negatively_regulates_entity',
                'subject': 'DRUGBANK:DB00945',
                'object': 'UniProtKB:P23219'
            },
            f"{INPUT_EDGE_PREFIX}: WARNING - Subject element 'biolink:ChemicalSubstance' is deprecated?"
        ),
        (   # Query 18 - inform that the input category is a mixin?
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:GeneOrGeneProduct',
                'object_category': 'biolink:Protein',
                'predicate': 'biolink:related_to',
                'subject': 'HGNC:9604',
                'object': 'UniProtKB:P23219'
            },
            f"{INPUT_EDGE_PREFIX}: INFO - Subject element 'biolink:GeneOrGeneProduct' is a mixin."
        ),
        (   # Query 19 - inform that the input category is abstract?
            LATEST_BIOLINK_MODEL,
            {
                'subject_category': 'biolink:AdministrativeEntity',
                'object_category': 'biolink:Agent',
                'predicate': 'biolink:related_to',
                'subject': 'isbn:1234',
                'object': 'ORCID:1234'
            },
            f"{INPUT_EDGE_PREFIX}: INFO - Subject element 'biolink:AdministrativeEntity' is abstract."
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
            f"{QUERY_GRAPH_PREFIX}: ERROR - Empty graph!"
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
            f"{QUERY_GRAPH_PREFIX}: ERROR - Node 'type-2 diabetes.ids' slot value is not an array!"
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
            f"{QUERY_GRAPH_PREFIX}: ERROR - Node 'NCBIGene:29974.categories' slot value is not an array!"
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
            f"{QUERY_GRAPH_PREFIX}: ERROR - Node 'NCBIGene:29974.categories' slot array is empty!"
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
            f"{QUERY_GRAPH_PREFIX}: ERROR - Query Graph Node element 'biolink:InvalidCategory' is unknown!"
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
            f"{QUERY_GRAPH_PREFIX}: ERROR - Edge 'drug--biolink:treats->type-2 diabetes' " +
            f"predicate slot value is not an array!"
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
            f"{QUERY_GRAPH_PREFIX}: ERROR - Edge 'drug--[]->type-2 diabetes' predicate slot value is an empty array!"
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
                        "predicates": ["biolink:invalid_predicate"],
                        "object": "type-2 diabetes"
                    }
                }
            },
            f"{QUERY_GRAPH_PREFIX}: ERROR - Predicate element 'biolink:invalid_predicate' is unknown!"
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
            f"{QUERY_GRAPH_PREFIX}: WARNING - Predicate 'biolink:affected_by' is non-canonical?"
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
            f"{QUERY_GRAPH_PREFIX}: ERROR - Edge 'None--['biolink:treats']->type-2 diabetes' " +
            "has a missing or empty 'subject' slot value!"
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
            f"{QUERY_GRAPH_PREFIX}: ERROR - Edge 'subject' id 'drug' is missing from the nodes catalog!"
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
            f"{QUERY_GRAPH_PREFIX}: ERROR - Edge 'drug--['biolink:treats']->None' " +
            f"has a missing or empty 'object' slot value!"
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
            f"{QUERY_GRAPH_PREFIX}: ERROR - Edge 'object' id 'type-2 diabetes' is missing from the nodes catalog!"
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
            f"{QUERY_GRAPH_PREFIX}: ERROR - Node 'drug.is_set' slot is not a boolean value!"
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
            f"{QUERY_GRAPH_PREFIX}: WARNING - Node 'type-2 diabetes' has identifiers ['FOO:12345', 'BAR:67890'] " +
            "unmapped to the target categories: ['biolink:Disease', 'biolink:Gene']?"
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
            f"{QUERY_GRAPH_PREFIX}: INFO - Query Graph Node element 'biolink:BiologicalEntity' is abstract."
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
            f"{QUERY_GRAPH_PREFIX}: INFO - Query Graph Node element 'biolink:ChemicalOrDrugOrTreatment' is a mixin."
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
            f"{QUERY_GRAPH_PREFIX}: INFO - Predicate element 'biolink:increases_amount_or_activity_of' is a mixin."
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
            "Edge has no 'attributes' key!"
        ),
        (
            # Query 1. Empty attributes
            {
                "attributes": None
            },
            get_ara_test_case(),
            "Edge has empty attributes!"
        ),
        (
            # Query 2. Empty attributes
            {
                "attributes": []
            },
            get_ara_test_case(),
            "Edge has empty attributes!"
        ),
        (
            # Query 3. Empty attributes
            {
                "attributes": {}
            },
            get_ara_test_case(),
            "Edge attributes are not a list!"
        ),
        (
            # Query 4. attribute missing its 'attribute_type_id' field
            {
                "attributes": [
                    {"value": ""}
                ]
            },
            get_ara_test_case(),
            "Edge attribute missing its 'attribute_type_id' field!"
        ),
        (
            # Query 5. attribute missing its 'value' field
            {
                "attributes": [
                    {"attribute_type_id": ""}
                ]
            },
            get_ara_test_case(),
            "Edge attribute missing its 'value' field!"
        ),
        (
            # Query 6.
            {
                "attributes": [
                    {
                        "attribute_type_id": "",
                        "value": ""
                    },
                ]
            },
            get_ara_test_case(),
            "missing ARA knowledge source provenance!"
        ),
        (
            # Query 7. missing ARA knowledge source provenance
            {
                "attributes": [
                    {
                        "attribute_type_id": "",
                        "value": ""
                    },
                ]
            },
            get_ara_test_case(),
            "missing ARA knowledge source provenance!"
        ),
        (
            # Query 8. value is an empty list?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": []
                    },
                ]
            },
            get_ara_test_case(),
            "value is an empty list!"
        ),
        (
            # Query 9. value has an unrecognized data type for a provenance attribute?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": 1234
                    },
                ]
            },
            get_ara_test_case(),
            "value has an unrecognized data type for a provenance attribute!"
        ),
        (
            # Query 10. KP provenance value is not a well-formed InfoRes CURIE? Should fail?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "infores:aragorn"
                    },
                    {
                        "attribute_type_id": "biolink:original_knowledge_source",
                        "value": "not_an_infores"
                    }
                ]
            },
            get_ara_test_case(),
            "is not a well-formed InfoRes CURIE!"
        ),
        (
            # Query 11. KP provenance value is missing?
            {
                "attributes": [
                    {
                        "attribute_type_id": "biolink:aggregator_knowledge_source",
                        "value": "infores:aragorn"
                    }
                ]
            },
            get_ara_test_case(),
            "is missing as expected knowledge source provenance!"
        ),
        (
            # Query 12. kp type is 'original'. Should draw a WARNING about deprecation
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
            f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Attribute Type ID element " +
            "'biolink:original_knowledge_source' is deprecated?"
        ),
        (
            # Query 13. kp type is 'primary'. Should pass?
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
            # Query 14. Missing 'primary' nor 'original' knowledge source
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
            f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Edge has neither a 'primary' nor 'original' knowledge source?"
        ),
        (
            # Query 15. Is complete and should pass?
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
        biolink_version=LATEST_BIOLINK_MODEL
    )
    validator.validate_attributes(edge=query[0], context=query[1])
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
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - No nodes found!"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 2: Empty nodes dictionary
            {
                "nodes": {}
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - No nodes found!"
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
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - No edges found!"
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
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - No edges found!"
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Node 'NCBIGene:29974' is missing its categories!"
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - The value of node 'NCBIGene:29974.categories' should be an array!"
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Knowledge Graph Node element 'biolink:Nonsense_Category' is unknown!"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 8: invalid node CURIE prefix namespace, for specified category
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
                        "predicate": "biolink:interacts_with",
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
            f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Node 'FOO:1234' " +
            f"is unmapped to the target categories: ['biolink:Gene']?"
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            # ditto for predicate and object... but identical code pattern thus we only test missing subject id here
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge 'None--biolink:interacts_with->NCBIGene:29974' " +
            "has a missing or empty 'subject' slot value!"
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge 'subject' id 'NCBIGene:12345' is missing from the nodes catalog!"
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Predicate element 'biolink:unknown_predicate' is unknown!"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 12: predicate is non-canonical
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
            f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - Predicate 'biolink:affected_by' is non-canonical?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 13: 'object' id is missing from the nodes catalog
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge 'object' id " +
            f"'PUBCHEM.COMPOUND:678' is missing from the nodes catalog!"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 14: attribute 'attribute_type_id' is missing
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
                        "attributes": [{"value": "some value"}]
                    }
                }
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge attribute is missing its 'attribute_type_id' key!"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 15: attribute 'value' is missing?
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
                        "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge attribute is missing its 'value' key!"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 16: 'attribute_type_id' is not a CURIE
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
                        "attributes": [{"attribute_type_id": "not_a_curie", "value": "some value"}]
                    }
                }
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge attribute_type_id 'not_a_curie' is not a CURIE!"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 17: 'attribute_type_id' is not a 'biolink:association_slot' (biolink:synonym is a node property)
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
                        "attributes": [{"attribute_type_id": "biolink:synonym", "value": "some synonym"}]
                    }
                }
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: WARNING - " +
            f"Edge attribute_type_id 'biolink:synonym' is not a biolink:association_slot?"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 18: 'attribute_type_id' has a 'biolink' CURIE prefix and is an association_slot so it should pass
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
            # Query 19: 'attribute_type_id' has a CURIE prefix namespace unknown to Biolink?
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
                        "attributes": [{"attribute_type_id": "foo:bar", "value": "some value"}]
                    }
                }
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge attribute_type_id 'foo:bar' " +
            f"has a CURIE prefix namespace unknown to Biolink!"
        ),
        (
            LATEST_BIOLINK_MODEL,
            # Query 20: has missing or empty attributes?
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
                        # "attributes": [{"attribute_type_id": "biolink:knowledge_source"}]
                    }
                }
            },
            f"{KNOWLEDGE_GRAPH_PREFIX}: ERROR - Edge has no 'attributes' key!"
        ),
        (   # Query 21:  # An earlier Biolink Model Version won't recognize a category not found in its version
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
            f"{KNOWLEDGE_GRAPH_PREFIX}: Knowledge Graph Node element 'biolink:SmallMolecule' is unknown!"
        )
    ]
)
def test_check_biolink_model_compliance_of_knowledge_graph(query: Tuple):
    validator: BiolinkValidator = check_biolink_model_compliance_of_knowledge_graph(
        graph=query[1], biolink_version=query[0]
    )
    check_messages(validator, query[2])


@pytest.mark.parametrize(
    "query",
    [
        (   # Query 0 - Completely empty Response.Message, QGraph trapped first....
            {
                "query_graph": None,
                "knowledge_graph": None,
                "results": None
            },
            None,
            None,
            "Validate TRAPI Response: ERROR - Response returned an empty Message Query Graph?"
        ),
        (
            {
                # Query 1 - Partly empty Response.Message with a modest but workable query graph? KG trapped next?
                "query_graph": {
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
                "knowledge_graph": None,
                "results": None
            },
            None,
            None,
            "Validate TRAPI Response: WARNING - Response returned an empty Message Knowledge Graph?"
        ),
        (
            {
                # Query 2 - Partly empty Response.Message with a modest but
                # workable query and knowledge graphs? Empty Results detected next?

                # modest but workable query and knowledge graphs?
                "query_graph": {
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
                "knowledge_graph": {
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
                "results": None
            },
            None,
            None,
            "Validate TRAPI Response: WARNING - Response returned empty Message Results?"
        )
    ]
)
def test_check_biolink_model_compliance_of_trapi_response(query: Tuple[Union[Dict, str]]):
    validator: ValidationReporter = check_biolink_model_compliance_of_trapi_response(
        message=query[0],
        trapi_version=query[1],
        biolink_version=query[2]
    )
    check_messages(validator, query[3])
