"""Test TRAPI version handling."""
from typing import Dict

import pytest

from reasoner_validator.versioning import get_latest_version
from reasoner_validator.trapi import load_schema, TRAPIAccessError

LATEST_TRAPI_VERSION: str = "v1.4.0-beta4"


def test_semver_spec_trapi_version():
    trapi_version: str = get_latest_version("1")
    assert trapi_version == LATEST_TRAPI_VERSION


def test_unknown_semver_spec_trapi_version():
    trapi_version: str = get_latest_version("2")
    assert trapi_version is None


def test_schema_spec_trapi_version():
    trapi_version = get_latest_version("./test_trapi_schema.yaml")
    assert trapi_version is not None
    assert trapi_version.endswith(".yaml")


def test_load_schema_with_semver_trapi_version():
    trapi_version: str = get_latest_version("1")
    schema: Dict = load_schema(trapi_version)
    assert schema


def test_load_schema_with_branch_name_as_trapi_version():
    trapi_version: str = get_latest_version("master")
    schema: Dict = load_schema(trapi_version)
    assert schema
    with pytest.raises(ValueError):
        load_schema(target="not-a-branch-name")


def test_load_schema_with_schema_trapi_version():
    trapi_version: str = get_latest_version("./test_trapi_schema.yaml")
    assert trapi_version is not None
    schema: Dict = load_schema(trapi_version)
    assert schema
    with pytest.raises(TRAPIAccessError):
        load_schema(target="not-a-trapi-schema.yaml")
