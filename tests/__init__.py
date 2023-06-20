from sys import stderr
from os.path import abspath, dirname, sep

TESTS_DIRECTORY = abspath(dirname(__file__))
print(f"Test Directory: {TESTS_DIRECTORY}", file=stderr)

SAMPLE_SCHEMA_VERSION = "v3.2.1-beta5"
SAMPLE_SCHEMA_FILE = f"{TESTS_DIRECTORY}{sep}test_data{sep}sample_trapi_schema_{SAMPLE_SCHEMA_VERSION}.yaml"

LATEST_TRAPI_VERSION: str = "v1.4.0-beta4"
