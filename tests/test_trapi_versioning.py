"""Test TRAPI version handling."""
from typing import Dict

import pytest

from reasoner_validator.versioning import get_latest_version
from reasoner_validator.trapi import load_schema, TRAPIAccessError
from tests import SAMPLE_SCHEMA_FILE, LATEST_TRAPI_VERSION


def test_semver_spec_trapi_version():
    trapi_version: str = get_latest_version(release_tag="1")
    assert trapi_version == LATEST_TRAPI_VERSION


def test_unknown_semver_spec_trapi_version():
    trapi_version: str = get_latest_version(release_tag="2")
    assert trapi_version is None


def test_schema_spec_trapi_version():
    trapi_version = get_latest_version(release_tag=SAMPLE_SCHEMA_FILE)
    assert trapi_version is not None
    assert trapi_version.endswith(".yaml")


def test_load_schema_with_semver_trapi_version():
    trapi_version: str = get_latest_version(release_tag="1")
    schema: Dict = load_schema(trapi_version)
    assert schema


def test_load_schema_with_branch_name_as_trapi_version():
    trapi_version: str = get_latest_version(release_tag="master")
    schema: Dict = load_schema(trapi_version)
    assert schema
    with pytest.raises(ValueError):
        load_schema(target="not-a-branch-name")


def test_load_schema_with_schema_trapi_version():
    trapi_version: str = get_latest_version(release_tag=SAMPLE_SCHEMA_FILE)
    assert trapi_version is not None
    schema: Dict = load_schema(trapi_version)
    assert schema
    with pytest.raises(TRAPIAccessError):
        load_schema(target="not-a-trapi-schema.yaml")
