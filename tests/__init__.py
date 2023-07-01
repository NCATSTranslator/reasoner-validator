from sys import stderr
from os.path import abspath, dirname, sep

TESTS_DIRECTORY = abspath(dirname(__file__))
print(f"Test Directory: {TESTS_DIRECTORY}", file=stderr)

PATCHED_SCHEMA_VERSION = "v1.4.0-beta5"
PATCHED_140_SCHEMA_FILEPATH = f"{TESTS_DIRECTORY}{sep}test_data{sep}patched_trapi_schema_{PATCHED_SCHEMA_VERSION}.yaml"

LATEST_TRAPI_VERSION: str = "v1.4.0"
LATEST_TEST_VERSIONS = "1", "1.4", "1.4.0"
