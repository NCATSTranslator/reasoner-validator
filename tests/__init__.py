from typing import Tuple, List
from sys import stderr
from os.path import abspath, dirname, sep
from reasoner_validator.trapi import (
    TRAPI_1_3_0,
    LATEST_TRAPI_MAJOR_RELEASE,
    LATEST_TRAPI_RELEASE
)

TESTS_DIRECTORY = abspath(dirname(__file__))
print(f"Test Directory: {TESTS_DIRECTORY}", file=stderr)

PATCHED_SCHEMA_VERSION = "v1.4.0-beta5"
PATCHED_140_SCHEMA_FILEPATH = f"{TESTS_DIRECTORY}{sep}test_data{sep}patched_trapi_schema_{PATCHED_SCHEMA_VERSION}.yaml"
BROKEN_SCHEMA_FILEPATH = f"broken-{PATCHED_SCHEMA_VERSION}.yaml"

PRE_1_4_0_TEST_VERSIONS: List = ["1.2", "1.2.0", "1.3", TRAPI_1_3_0]
LATEST_TEST_RELEASES: List = ["1", LATEST_TRAPI_MAJOR_RELEASE, LATEST_TRAPI_RELEASE]

ALL_TEST_VERSIONS: List[str] = PRE_1_4_0_TEST_VERSIONS + LATEST_TEST_RELEASES
