"""
This test file overlaps a bit with test_validate.py but intentionally isolates
basic TRAPI Query 'workflow' testing to help troubleshoot the validation.
"""
import pytest
from typing import Tuple, Dict
from itertools import product
from json import dumps

from reasoner_validator.trapi import TRAPISchemaValidator

LATEST_TEST_VERSIONS = "1", "1.4", "1.4.0", "1.4.0-beta", "1.4.0-beta2"

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

QUERY_VERSION = [qv for qv in product(LATEST_TEST_VERSIONS, (SAMPLE_QUERY_1, SAMPLE_QUERY_2))]


@pytest.mark.parametrize("query", QUERY_VERSION)
def test_query_latest_trapi_workflow_properties(query: Tuple[str, Dict]):
    """Test flawed TRAPI Query workflow properties."""

    print(f"\nTRAPI release: '{query[0]}'")
    print(f"Test Workflow: '{dumps(query[1]['workflow'], indent=2)}'")

    validator = TRAPISchemaValidator(trapi_version=query[0])
    validator.validate(query[1], "Query")
