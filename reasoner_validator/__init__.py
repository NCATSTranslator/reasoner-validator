"""TRAPI Validation Functions."""
from typing import Optional, Dict, Set

import jsonschema

from .report import ValidationReporter
from .util import load_schema


class TRAPIValidator(ValidationReporter):
    """
    TRAPI Validator is a wrapper class for validating
    conformance of JSON messages to the Translator Reasoner API.
    """
    # Default major version resolves to latest TRAPI OpenAPI release,
    # specifically 1.3.0, as of September 1st, 2022
    DEFAULT_TRAPI_VERSION = "1"

    def __init__(self, trapi_version: Optional[str] = None):
        """
        TRAPI Validator constructor.

        Parameters
        ----------
        trapi_version : str
            version of component to validate against
        """
        self.version = trapi_version if trapi_version else self.DEFAULT_TRAPI_VERSION
        ValidationReporter.__init__(self, prefix=F"Validating against TRAPI {self.version}")

    def get_trapi_version(self) -> str:
        """
        :return: str, TRAPI (SemVer) version
        """
        return self.version

    def validate(self, instance, component):
        """Validate instance against schema.

        Parameters
        ----------
        instance
            instance to validate
        component : str
            component to validate against

        Raises
        ------
        `ValidationError <https://python-jsonschema.readthedocs.io/en/latest/errors/#jsonschema.exceptions.ValidationError>`_
            If the instance is invalid.

        Examples
        --------
        >>> TRAPIValidator(trapi_version="1.3.0").validate({"message": {}}, "Query")

        """
        schema = load_schema(self.version)[component]
        jsonschema.validate(instance, schema)

    def is_valid_trapi_query(self, instance):
        """Make sure that the Message is a syntactically valid TRAPI Query JSON object.

        Parameters
        ----------
        instance
            instance to validate

        Returns
        -------
        Outcome of validation is recorded in TRAPIValidator instance ("information", "warning" and "error") messages.

        Examples
        --------
        >>> TRAPIValidator(trapi_version="1.3.0").is_valid_trapi_query({"message": {}})
        """
        try:
            self.validate(
                instance=instance,
                component="Query"
            )
        except jsonschema.ValidationError as e:
            self.error(f"TRAPI {self.version} Query: '{e.message}'")


def check_trapi_validity(instance, trapi_version: str) -> Dict[str, Set[str]]:
    """
    Checks schema compliance of a Query component against a given TRAPI version.

    Parameters
    ----------
    instance: Dict, of format {"message": {}}
    trapi_version : str
        version of component to validate against

    Returns
    -------
    Dict[str, Set[str]], of "information", "warnings" or "errors" indexed sets of string messages (may be empty)
    """
    trapi_validator = TRAPIValidator(trapi_version=trapi_version)
    trapi_validator.is_valid_trapi_query(instance)
    return trapi_validator.get_messages()
