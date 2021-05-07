"""Build validation functions."""
import jsonschema
import requests

from .util import load_schema


response = requests.get("https://api.github.com/repos/NCATSTranslator/ReasonerAPI/releases")
releases = response.json()
versions = [
    release["tag_name"][1:]
    for release in releases
    if release["tag_name"].startswith("v")
]


def validate(instance, component, trapi_version=None):
    """Validate instance against schema.

    Parameters
    ----------
    instance
        instance to validate
    component : str
        component to validate against
    trapi_version : str
        version of component to validate against

    Raises
    ------
    `ValidationError <https://python-jsonschema.readthedocs.io/en/latest/errors/#jsonschema.exceptions.ValidationError>`_
        If the instance is invalid.

    Examples
    --------
    >>> validate({"message": {}}, "Query", "1.0.3")

    """
    if trapi_version not in versions:
        raise ValueError(f"No TRAPI version {trapi_version}")
    schema = load_schema(trapi_version)[component]
    jsonschema.validate(instance, schema)
