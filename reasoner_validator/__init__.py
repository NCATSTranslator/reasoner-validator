"""TRAPI Validation Functions."""
from typing import Optional

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
        String outcome of validation, either "Valid TRAPI Message" or "Invalid TRAPI Message: <details of error>"

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
