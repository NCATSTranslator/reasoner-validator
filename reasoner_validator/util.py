"""Utilities."""
import copy
from functools import lru_cache

import requests
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


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
    if schema.get("type", None) == "object":
        for prop in schema.get("properties", dict()).values():
            openapi_to_jsonschema(prop)
    if schema.get("type", None) == "array":
        openapi_to_jsonschema(schema.get("items", dict()))
    if schema.pop("nullable", False):
        fix_nullable(schema)


@lru_cache()
def load_schema(trapi_version: str):
    """Load schema from GitHub."""
    response = requests.get(f"https://raw.githubusercontent.com/NCATSTranslator/ReasonerAPI/v{trapi_version}/TranslatorReasonerAPI.yaml")
    spec = yaml.load(response.text, Loader=Loader)
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
