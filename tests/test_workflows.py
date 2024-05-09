"""
This test file overlaps a bit with test_validate.py but intentionally isolates
basic TRAPI Query 'workflow' testing to help troubleshoot the validation.
"""
import pytest
from typing import Dict
from itertools import product
from json import dumps

from reasoner_validator.trapi import TRAPISchemaValidator
from reasoner_validator.validator import TRAPIResponseValidator

from tests import LATEST_TEST_RELEASES, TRAPI_1_4_TEST_VERSIONS

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
                "allowlist": {
                    "allowlist": [
                        "infores:aragorn"
                    ]
                }
            }
        },
        {
            "id": "lookup",
            "runner_parameters": {
                "allowlist": {
                    "allowlist": [
                        "infores:aragorn"
                    ]
                }
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

TRAPI_1_4_QUERY_VERSION = [qv for qv in product(TRAPI_1_4_TEST_VERSIONS, (SAMPLE_QUERY_1, SAMPLE_QUERY_2))]


@pytest.mark.parametrize("trapi_version,query", TRAPI_1_4_QUERY_VERSION)
def test_trapi_1_4_query_trapi_workflow_properties(trapi_version: str, query: Dict):
    """Test flawed TRAPI Query workflow properties."""

    print(f"\nTRAPI release: '{trapi_version}'")
    print(f"Test Workflow: '{dumps(query['workflow'], indent=2)}'")

    validator = TRAPISchemaValidator(trapi_version=trapi_version)
    validator.validate(query, "Query")


TRAPI_LATEST_TRAPI_QUERY_VERSION = [qv for qv in product(LATEST_TEST_RELEASES, (SAMPLE_QUERY_1, SAMPLE_QUERY_2))]


@pytest.mark.skip(reason="Not updated to work correctly with TRAPI 1.5.0")
@pytest.mark.parametrize("trapi_version,query", TRAPI_LATEST_TRAPI_QUERY_VERSION)
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
