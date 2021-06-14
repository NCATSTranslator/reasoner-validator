"""Build validation functions."""
import jsonschema

from .util import load_schema


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
    schema = load_schema(trapi_version)[component]
    jsonschema.validate(instance, schema)
