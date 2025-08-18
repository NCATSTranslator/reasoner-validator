"""
This test file overlaps a bit with test_validate.py but intentionally isolates
basic TRAPI Query 'workflow' testing to help troubleshoot the validation.
"""
import pytest
from typing import List, Tuple, Dict
from itertools import product
from json import dumps

from reasoner_validator.trapi import TRAPISchemaValidator
from reasoner_validator.validator import TRAPIResponseValidator

from tests import LATEST_TEST_RELEASES


SAMPLE_QUERY_1 = {
    "message": {
        "knowledge_graph": None,
        "query_graph": None,
        "results": None,
    },
    "log_level": None,
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


SAMPLE_QUERY_2 = {
    "message": {
        "knowledge_graph": None,
        "query_graph": None,
        "results": None,
    },
    "log_level": None,
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


@pytest.mark.parametrize(
    "trapi_version,query",
    _generate_workflow_sample_data(
        versions=LATEST_TEST_RELEASES,
        queries=(SAMPLE_QUERY_1, SAMPLE_QUERY_2)
    )
)
def test_query_latest_trapi_workflow_properties(trapi_version: str, query: Dict):
    """Test flawed TRAPI Query workflow properties."""

    print(f"\nTRAPI release: '{trapi_version}'")
    print(f"Test Workflow: '{dumps(query['workflow'], indent=2)}'")

    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    validator.validate(query, "Query")


SAMPLE_QUERY_3 = {
    "message": {
        "knowledge_graph": None,
        "query_graph": None,
        "results": None,
    },
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


def test_query_sanitize_response_workflow_properties():
    """Test sanitization of flawed TRAPI Query workflow properties."""

    validator = TRAPIResponseValidator()
    response = validator.sanitize_workflow(SAMPLE_QUERY_3)
    validator.validate(response, "Query")
