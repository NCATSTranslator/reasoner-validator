"""TRAPI Validation Functions."""
import jsonschema

from .util import load_schema

# Default resolves to latest, specifically 1.2.0 as of April 2022,
# but the Reasoner validator should discern this
DEFAULT_TRAPI_VERSION = "1"


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
    >>> validate({"message": {}}, "Query", "1.3.0")

    """
    schema = load_schema(trapi_version)[component]
    jsonschema.validate(instance, schema)


def is_valid_trapi_query(instance, trapi_version) -> str:
    """Make sure that the Message is a syntactically valid TRAPI Query JSON object.

    Parameters
    ----------
    instance
        instance to validate
    trapi_version : str
        version of component to validate against

    Returns
    -------
    String outcome of validation, either "Valid TRAPI Message" or "Invalid TRAPI Message: <details of error>"

    Examples
    --------
    >>> is_valid_trapi_query({"message": {}}, "1.3.0")
    """
    try:
        validate(
            instance=instance,
            component="Query",
            trapi_version=trapi_version
        )
        return ""
    except jsonschema.ValidationError as e:
        return f"TRAPI {trapi_version} Query: '{e.message}'"
