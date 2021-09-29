"""Utilities."""
import copy
from functools import lru_cache
import re
from typing import NamedTuple

import requests
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


response = requests.get("https://api.github.com/repos/NCATSTranslator/ReasonerAPI/releases")
releases = response.json()
print(release for release in releases)
versions = [
    release["tag_name"][1:]
    for release in releases
    if release["tag_name"].startswith("v")
]

semver_pattern = re.compile(r"(\d+)(?:\.(\d+)(?:\.(\d+))?)?")


class SemVerError(Exception):
    """Invalid semantic version."""


class SemVerUnderspecified(SemVerError):
    """Semantic version underspecified."""


class SemVer(NamedTuple):
    major: int
    minor: int
    patch: int

    @classmethod
    def from_string(cls, string):
        match = semver_pattern.fullmatch(string)
        if match is None:
            raise SemVerError(f"'{string}' is not a valid release version")
        captured = match.groups()
        if any(group is None for group in captured):
            raise SemVerUnderspecified(f"'{string}' is missing minor and/or patch versions")
        return cls(*[int(group) for group in captured])
    
    def __str__(self):
        """Generate string."""
        value = f"{self.major}"
        if self.minor is not None:
            value += f".{self.minor}"
        if self.patch is not None:
            value += f".{self.patch}"
        return value


latest_patch = dict()
latest_minor = dict()
latest = dict()
for version in versions:
    try:
        major, minor, patch = SemVer.from_string(version)
    except SemVerError as err:
        print("\nWARNING:", err)
        continue
    latest_minor[major] = max(minor, latest_minor.get(major, -1))
    latest_patch[(major, minor)] = max(patch, latest_patch.get((major, minor), -1))
    latest[f"{major}"] = str(SemVer(
        major,
        latest_minor[major],
        latest_patch[(major, latest_minor[major])],
    ))
    latest[f"{major}.{minor}"] = str(SemVer(
        major,
        minor,
        latest_patch[(major, minor)],
    ))
    latest[f"{major}.{minor}.{patch}"] = str(SemVer(
        major,
        minor,
        patch,
    ))


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


def load_schema(trapi_version: str):
    """Load schema from GitHub."""
    full_version = latest.get(trapi_version)
    if full_version not in versions:
        raise ValueError(f"No TRAPI version {trapi_version}")
    return _load_schema(full_version)


@lru_cache()
def _load_schema(trapi_version: str):
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
