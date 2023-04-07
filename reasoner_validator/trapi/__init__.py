"""TRAPI Validation Functions."""
from typing import Optional
import copy
from functools import lru_cache

import jsonschema
import requests

from yaml import load, CLoader as Loader

from reasoner_validator.report import ValidationReporter
from reasoner_validator.trapi.mapping import check_node_edge_mappings
from reasoner_validator.versioning import (
    SemVer,
    SemVerError,
    get_latest_version,
    GIT_ORG,
    GIT_REPO,
    branches
)

import logging
logger = logging.getLogger(__name__)


@lru_cache()
def _load_schema(schema_version: str):
    """Load schema from GitHub."""
    result = requests.get(
        f"https://raw.githubusercontent.com/{GIT_ORG}/{GIT_REPO}/{schema_version}/TranslatorReasonerAPI.yaml"
    )
    spec = load(result.text, Loader=Loader)
    components = spec["components"]["schemas"]
    for component, schema in components.items():
        openapi_to_jsonschema(schema, version=schema_version)
    schemas = dict()
    for component in components:
        # build json schema against which we validate
        subcomponents = copy.deepcopy(components)
        schema = subcomponents.pop(component)
        schema["components"] = {"schemas": subcomponents}
        schemas[component] = schema
    return schemas


def load_schema(target: str):
    """
    Load schema from GitHub.
    :param target: release semver or git branch name containing the target TRAPI schema.
    :return: loaded TRAPI schema
    """
    mapped_release = get_latest_version(target)
    if mapped_release:
        schema_version = mapped_release
    elif target in branches:
        # cases in which a branch name is
        # given instead of a release number
        schema_version = target
    else:
        err_msg: str = f"No TRAPI version {target}"
        logger.error(err_msg)
        raise ValueError(err_msg)

    return _load_schema(schema_version)


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


def openapi_to_jsonschema(schema, version: str) -> None:
    """
    Convert OpenAPI schema to JSON schema.
    :param schema: Dict, in-memory representation of the OpenAPI schema to be validated.
    :param version: str, TRAPI version against which the schema is currently being validated.
    :return:
    """

    mapped_semver: Optional[SemVer]
    try:
        mapped_semver = SemVer.from_string(version)
    except SemVerError as sve:
        # if we cannot map the version, then it may simply
        # be a non-versioned branch of the schemata
        logger.error(str(sve))
        mapped_semver = None

    # we'll only tweak mapped schemata and
    # such releases that are prior to TRAPI 1.4.0-beta
    if (mapped_semver and not (mapped_semver >= SemVer.from_string("1.4.0-beta"))) \
            and "allOf" in schema:
        # September 1, 2022 hacky patch to rewrite 'allOf'
        # tagged schemata, in TRAPI 1.3.0 or earlier, to 'oneOf'
        schema["oneOf"] = schema.pop("allOf")

    if schema.get("type", None) == "object":
        for tag, prop in schema.get("properties", dict()).items():
            openapi_to_jsonschema(prop, version=version)

    if schema.get("type", None) == "array":
        openapi_to_jsonschema(schema.get("items", dict()), version=version)

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
        ValidationReporter.__init__(
            self,
            prefix="TRAPI Validation",
            trapi_version=trapi_version
        )

    def validate(self, instance, component):
        """Validate instance against schema.

        Parameters
        ----------
        instance
            dict, instance to validate
        component : str
            TRAPI subschema to validate (e.g. 'Query', 'QueryGraph', 'KnowledgeGraph', 'Result'; Default: 'Query')

        Raises
        ------
        `ValidationError
            <https://python-jsonschema.readthedocs.io/en/latest/errors/#jsonschema.exceptions.ValidationError>`_
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
            self.report(code="error.trapi.validation", identifier=self.trapi_version, reason=e.message)


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
    ValidationReporter catalog of "information", "warnings" or "errors" indexed messages (maybe empty)
    """
    trapi_validator = TRAPISchemaValidator(trapi_version=trapi_version)
    trapi_validator.is_valid_trapi_query(instance, component=component)
    return trapi_validator
