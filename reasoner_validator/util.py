"""Utilities."""


def fix_nullable(schema) -> None:
    """Fix nullable schema."""
    if "$ref" in schema or "type" in schema:
        schema = {
            "oneOf": [
                schema,
                {"type": "null"},
            ]
        }
        return
    if "oneOf" in schema:
        schema["oneOf"].append({"type": "null"})
        return
    if "anyOf" in schema:
        schema["anyOf"].append({"type": "null"})
        return


def openapi_to_jsonschema(schema) -> None:
    """Convert OpenAPI schema to JSON schema."""
    if schema.get("type", None) == "object":
        for prop in schema.get("properties", dict()).values():
            openapi_to_jsonschema(prop)
    if schema.get("type", None) == "array":
        openapi_to_jsonschema(schema.get("items", dict()))
    if schema.pop("nullable", False):
        fix_nullable(schema)
