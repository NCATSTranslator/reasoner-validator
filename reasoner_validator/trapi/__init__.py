"""TRAPI Validation Functions."""
from typing import Optional
import copy
from functools import lru_cache

import jsonschema
import requests

from yaml import load, CLoader as Loader

from reasoner_validator.report import ValidationReporter
from reasoner_validator.trapi.mapping import check_node_edge_mappings
from reasoner_validator.versioning import latest, versions, GIT_ORG, GIT_REPO


@lru_cache()
def _load_schema(trapi_version: str):
    """Load schema from GitHub."""
    result = requests.get(
        f"https://raw.githubusercontent.com/{GIT_ORG}/{GIT_REPO}/v{trapi_version}/TranslatorReasonerAPI.yaml"
    )
    spec = load(result.text, Loader=Loader)
    components = spec["components"]["schemas"]
    for component, schema in components.items():
        openapi_to_jsonschema(schema)
    schemas = dict()
    for component in components:
        # build json schema against which we validate
        subcomponents = copy.deepcopy(components)
        schema = subcomponents.pop(component)
        schema["components"] = {"schemas": subcomponents}
        schemas[component] = schema
    return schemas


def load_schema(trapi_version: str):
    """Load schema from GitHub."""
    full_version = latest.get(trapi_version)
    if full_version not in versions:
        raise ValueError(f"No TRAPI version {trapi_version}")
    return _load_schema(full_version)


def fix_nullable(schema) -> None:
    """Fix nullable schema."""
    if "oneOf" in schema:
        schema["oneOf"].append({"type": "null"})
        return
    if "anyOf" in schema:
        schema["anyOf"].append({"type": "null"})
        return
    schema["oneOf"] = [
        {
            key: schema.pop(key)
            for key in list(schema.keys())
        },
        {"type": "null"},
    ]


def openapi_to_jsonschema(schema) -> None:
    """Convert OpenAPI schema to JSON schema."""
    if "allOf" in schema:
        # September 1, 2022 hacky patch to rewrite 'allOf' tagged subschemata to 'oneOf'
        # TODO: TRAPI needs to change this in release 1.4
        schema["oneOf"] = schema.pop("allOf")
    if schema.get("type", None) == "object":
        for tag, prop in schema.get("properties", dict()).items():
            openapi_to_jsonschema(prop)
    if schema.get("type", None) == "array":
        openapi_to_jsonschema(schema.get("items", dict()))
    if schema.pop("nullable", False):
        fix_nullable(schema)


class TRAPISchemaValidator(ValidationReporter):
    """
    TRAPI Validator is a wrapper class for validating
    conformance of JSON messages to the Translator Reasoner API.
    """
    def __init__(
            self,
            trapi_version: Optional[str] = None
    ):
        """
        TRAPI Validator constructor.

        Parameters
        ----------
        trapi_version : str
            version of component to validate against
        """
        resolved_biolink_version = latest.get(trapi_version)
        ValidationReporter.__init__(
            self,
            prefix="TRAPI Validation",
            trapi_version=resolved_biolink_version
        )

    def validate(self, instance, component):
        """Validate instance against schema.

        Parameters
        ----------
        instance
            dict, instance to validate
        component : str
            str, TRAPI subschema to validate (e.g. 'Query', 'QueryGraph', 'KnowledgeGraph', 'Result'; Default: 'Query')

        Raises
        ------
        `ValidationError <https://python-jsonschema.readthedocs.io/en/latest/errors/#jsonschema.exceptions.ValidationError>`_
            If the instance is invalid.

        Examples
        --------
        >>> TRAPISchemaValidator(trapi_version="1.3.0").validate({"message": {}}, "QGraph")

        """
        schema = load_schema(self.trapi_version)[component]
        jsonschema.validate(instance, schema)

    def is_valid_trapi_query(self, instance, component: str = "Query"):
        """Make sure that the Message is a syntactically valid TRAPI Query JSON object.

        Parameters
        ----------
        instance:
            Dict, instance to validate
        component:
            str, TRAPI subschema to validate (e.g. 'Query', 'QueryGraph', 'KnowledgeGraph', 'Result'; Default: 'Query')

        Returns
        -------
        Validation ("information", "warning" and "error") messages are returned within the host TRAPIValidator instance.

        Examples
        --------
        >>> TRAPISchemaValidator(trapi_version="1.3.0").is_valid_trapi_query({"message": {}}, component="Query")
        """
        try:
            self.validate(
                instance=instance,
                component=component
            )
        except jsonschema.ValidationError as e:
            self.report(code="error.trapi.validation", trapi_version=self.trapi_version, exception=e.message)


def check_trapi_validity(instance, trapi_version: str, component: str = "Query") -> TRAPISchemaValidator:
    """
    Checks schema compliance of a Query component against a given TRAPI version.

    Parameters
    ----------
    instance:
        Dict, of format {"message": {}}
    component:
        str, TRAPI subschema to validate (e.g. 'Query', 'QueryGraph', 'KnowledgeGraph', 'Result'; Default: 'Query')
    trapi_version:
        str, version of component to validate against

    Returns
    -------
    ValidationReporter catalog of "information", "warnings" or "errors" indexed messages (may be empty)
    """
    trapi_validator = TRAPISchemaValidator(trapi_version=trapi_version)
    trapi_validator.is_valid_trapi_query(instance, component=component)
    return trapi_validator
