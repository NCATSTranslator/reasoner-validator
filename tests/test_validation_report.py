"""Testing Validation Report methods"""
from typing import Dict, Set, Tuple
import pytest

from reasoner_validator.report import ValidationReporter

TEST_TRAPI_VERSION = "1.3.0"
TEST_BIOLINK_VERSION = "2.4.8"


def test_messages():

    # Loading and checking a first reporter
    reporter1 = ValidationReporter(prefix="First Validation Report", trapi_version=TEST_TRAPI_VERSION)
    assert reporter1.get_trapi_version() == TEST_TRAPI_VERSION
    assert reporter1.get_biolink_version() is None
    assert not reporter1.has_messages()
    reporter1.info("this is information.")
    assert reporter1.has_messages()
    assert reporter1.has_information()
    assert not reporter1.has_warnings()
    assert not reporter1.has_errors()
    reporter1.warning("this is a warning?")
    assert reporter1.has_warnings()
    reporter1.error("this is an error!")
    assert reporter1.has_messages()

    # Testing merging of messages from a second reporter
    reporter2 = ValidationReporter(prefix="Second Validation Report", biolink_version=TEST_BIOLINK_VERSION)
    assert reporter2.get_trapi_version() is "1"
    assert reporter2.get_biolink_version() == TEST_BIOLINK_VERSION
    reporter2.info("this is more information.")
    reporter2.warning("this is another warning?")
    reporter2.error("this is a second error!")
    reporter1.merge(reporter2)
    assert reporter1.get_trapi_version() == TEST_TRAPI_VERSION
    assert reporter1.get_biolink_version() == TEST_BIOLINK_VERSION
    
    # No prefix...
    reporter3 = ValidationReporter()
    reporter3.error("Ka Boom!")
    reporter1.merge(reporter3)
    assert reporter1.get_trapi_version() == TEST_TRAPI_VERSION
    assert reporter1.get_biolink_version() == TEST_BIOLINK_VERSION

    # testing addition a few raw batch messages
    new_messages: Dict[str, Set[str]] = {
            "information": {"Hello Dolly...", "Well,... hello Dolly"},
            "warnings": {"Warning, Will Robinson, warning!"},
            "errors": {"Dave, this can only be due to human error!"}
    }
    reporter1.add_messages(new_messages)

    # Verify what we have
    messages: Dict[str, Set[str]] = reporter1.get_messages()
    assert "First Validation Report: INFO - this is information." in messages["information"]
    assert "Second Validation Report: INFO - this is more information." in messages["information"]
    assert "Hello Dolly..." in messages["information"]
    assert "Well,... hello Dolly" in messages["information"]
    assert "First Validation Report: WARNING - this is a warning?" in messages["warnings"]
    assert "Second Validation Report: WARNING - this is another warning?" in messages["warnings"]
    assert "Warning, Will Robinson, warning!" in messages["warnings"]
    assert "First Validation Report: ERROR - this is an error!" in messages["errors"]
    assert "Second Validation Report: ERROR - this is a second error!" in messages["errors"]
    assert "Dave, this can only be due to human error!" in messages["errors"]
    assert "ERROR - Ka Boom!" in messages["errors"]
    
    obj = reporter1.to_dict()
    assert obj["trapi_version"] == TEST_TRAPI_VERSION
    assert obj["biolink_version"] == TEST_BIOLINK_VERSION
    assert "messages" in obj
    assert "errors" in obj["messages"]
    assert "ERROR - Ka Boom!" in obj["messages"]["errors"]


def test_validator_method():
    reporter = ValidationReporter(
        prefix="Test Validator Method",
        trapi_version=TEST_TRAPI_VERSION,
        biolink_version=TEST_BIOLINK_VERSION
    )

    test_data: Dict = {
        "some key": "some value"
    }
    test_parameters: Dict = {
        "some parameter": "some parameter value",
        "another parameter": "some other parameter value"
    }

    def validator_method(validator: ValidationReporter, arg, **case):
        assert isinstance(arg, Dict)
        assert arg['some key'] == "some value"
        validator.warning("This is a Warning?")
        assert len(case) == 2
        assert case['some parameter'] == "some parameter value"
        validator.error("This is an Error!")

    reporter.validate(validator_method, test_data, **test_parameters)

    messages: Dict[str, Set[str]] = reporter.get_messages()

    assert "Test Validator Method: WARNING - This is a Warning?" in messages["warnings"]
    assert "Test Validator Method: ERROR - This is an Error!" in messages["errors"]


# has_validation_errors(root_key: str = 'validation', case: Optional[Dict] = None)
@pytest.mark.parametrize(
    "query",
    [
        (
                'validation',
                {
                    "validation": {
                        "trapi_version": "1.3",
                        "biolink_version": "2.4.7",
                        "messages": {
                            "information": [],
                            "warnings": [],
                            "errors": [
                                "Validation: ERROR - this is an error"
                            ]
                        }
                    }
                },
                True
        ),
        (
                "validation",
                {
                    "validation": {
                        "trapi_version": "1.3",
                        "biolink_version": "2.4.7",
                        "messages": {
                            "information": [],
                            "warnings": [
                                "Validation: WARNING - Input Biolink class 'biolink:ChemicalSubstance' is deprecated?",
                                "Validation: WARNING - Input predicate 'biolink:participates_in' is non-canonical!"
                            ],
                            "errors": []
                        }
                    }
                },
                False
        ),
    ]
)
def test_has_validation_errors(query: Tuple):
    reporter = ValidationReporter()
    assert reporter.has_validation_errors(tag=query[0], case=query[1]) == query[2]

