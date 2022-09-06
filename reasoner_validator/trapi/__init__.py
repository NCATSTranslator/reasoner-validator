"""TRAPI Validation Functions."""
from typing import Optional

import jsonschema

from reasoner_validator.report import ValidationReporter
from reasoner_validator.util import load_schema


class TRAPIValidator(ValidationReporter):
    """
    TRAPI Validator is a wrapper class for validating
    conformance of JSON messages to the Translator Reasoner API.
    """
    def __init__(self, trapi_version: Optional[str] = None):
        """
        TRAPI Validator constructor.

        Parameters
        ----------
        trapi_version : str
            version of component to validate against
        """
        ValidationReporter.__init__(
            self,
            prefix=F"Validating against TRAPI {trapi_version}",
            trapi_version=trapi_version
        )

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
        schema = load_schema(self.trapi_version)[component]
        jsonschema.validate(instance, schema)

    def is_valid_trapi_query(self, instance):
        """Make sure that the Message is a syntactically valid TRAPI Query JSON object.

        Parameters
        ----------
        instance
            instance to validate

        Returns
        -------
        Validation ("information", "warning" and "error") messages are returned within the TRAPIValidator instance.

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
            self.error(f"TRAPI {self.trapi_version} Query: '{e.message}'")


def check_trapi_validity(instance, trapi_version: str) -> ValidationReporter:
    """
    Checks schema compliance of a Query component against a given TRAPI version.

    Parameters
    ----------
    instance: Dict, of format {"message": {}}
    trapi_version : str
        version of component to validate against

    Returns
    -------
    ValidationReporter catalog of "information", "warnings" or "errors" indexed messages (may be empty)
    """
    trapi_validator = TRAPIValidator(trapi_version=trapi_version)
    trapi_validator.is_valid_trapi_query(instance)
    return trapi_validator
