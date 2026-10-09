"""
This test file overlaps a bit with test_validate.py but intentionally isolates
basic TRAPI Query 'workflow' testing to help troubleshoot the validation.
"""
import pytest
from typing import List, Tuple, Dict
from copy import deepcopy
from itertools import product
from json import dumps

from reasoner_validator.trapi import TRAPISchemaValidator
from reasoner_validator.validator import TRAPIResponseValidator

from tests import LATEST_TEST_RELEASES


SAMPLE_WORKFLOW_1 = {
    "workflow":  [
        {
            "id": "sort_results_score",
            "parameters": {
                "ascending_or_descending": "ascending"
            },
            "runner_parameters": {
                "allowlist": [
                        "infores:aragorn"
                    ]
            }
        },
        {
            "id": "lookup",
            "runner_parameters": {
                "allowlist": [
                        "infores:aragorn"
                    ]
            }
        }
    ]
}

SAMPLE_WORKFLOW_2 = {
    "workflow":  [
        {
            "id": "sort_results_score",
            "parameters": {
                "ascending_or_descending": "ascending"
            }
        },
        {
            "id": "lookup"
        }
    ]
}


def _generate_workflow_sample_data(versions: List[str], queries: Tuple[Dict, Dict]) -> List:
    return [qv for qv in product(versions, queries)]

# From TRAPI 2.0, message components cannot be nullable and
# for nodes, must include some minimum content, which is faked here
TRAPI_2_0_COMPLIANT_QUERY_TEMPLATE = {
    "message": {
        "knowledge_graph": {
            "nodes": {
                "OMIM:603903": {
                    "categories": ["biolink:Disease"],
                    "name": "Sickle Cell Disease"
                }
            }
        },
        "query_graph": {
            "nodes": {
                "n0": {
                    "ids": ["OMIM:603903"],
                    "categories": ["biolink:Disease"]
                }
            }
        },
        "results": [
            {
                "node_bindings": {
                    "n0": {
                        "ids": ["OMIM:603903"]
                    }
                }
            }
        ],
    },
    "log_level": None,
}

SAMPLE_POST_2_0_QUERY_1 = deepcopy(TRAPI_2_0_COMPLIANT_QUERY_TEMPLATE) | deepcopy(SAMPLE_WORKFLOW_1)
SAMPLE_POST_2_0_QUERY_2 = deepcopy(TRAPI_2_0_COMPLIANT_QUERY_TEMPLATE) | deepcopy(SAMPLE_WORKFLOW_2)

@pytest.mark.parametrize(
    "trapi_version,query",
    _generate_workflow_sample_data(
        versions=LATEST_TEST_RELEASES,
        queries=(SAMPLE_POST_2_0_QUERY_1, SAMPLE_POST_2_0_QUERY_2)
    )
)
def test_query_post_2_0_trapi_workflow_properties(trapi_version: str, query: Dict):
    """Test flawed TRAPI Query workflow properties."""

    print(f"\nTRAPI release: '{trapi_version}'")
    print(f"Test Workflow: '{dumps(query['workflow'], indent=2)}'")

    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    validator.validate(query, "Query")


SAMPLE_INCOMPLETE_WORKFLOW = {
    "log_level": None,
    "workflow":  [
        {
            "id": "annotate_nodes",
            "parameters": None,
            "runner_parameters": None
        },
        {
            "id": "lookup"
        }
    ]
}
QUERY_WITH_FLAWED_WORKFLOW = deepcopy(TRAPI_2_0_COMPLIANT_QUERY_TEMPLATE) | deepcopy(SAMPLE_INCOMPLETE_WORKFLOW)

def test_query_sanitize_response_workflow_properties():
    """Test sanitization of flawed TRAPI Query workflow properties."""

    validator = TRAPIResponseValidator(trapi_version="2")
    response = validator.sanitize_workflow(QUERY_WITH_FLAWED_WORKFLOW)
    validator.validate(response, "Query")
