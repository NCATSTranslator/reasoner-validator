"""Build validation functions."""
import copy
from inspect import signature
import sys

import jsonschema
from jsonschema import ValidationError
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources
from . import data  # relative-import the *package* containing the templates

from .util import openapi_to_jsonschema

TRAPI_VERSIONS = ['1.0', '1.1']
to_loads = {}
specs = {}
components = {}
for _version in TRAPI_VERSIONS:
    to_loads[_version] = pkg_resources.read_text(data, 'TranslatorReasonerAPI-{}.yml'.format(_version))
    specs[_version] = yaml.load(to_loads[_version], Loader=Loader)
    components[_version] = specs[_version]['components']['schemas']

    for component_name, schema in components[_version].items():
        openapi_to_jsonschema(schema)
    for component_name in components[_version]:
        # build json schema against which we validate
        other_components = copy.deepcopy(components[_version])
        schema = other_components.pop(component_name)
        schema['components'] = {'schemas': other_components}

        def validate(obj, schema=schema):
            """Validate object against schema."""
            jsonschema.validate(obj, schema)

        # Override signature
        sig = signature(validate)
        sig = sig.replace(parameters=tuple(sig.parameters.values())[:1])
        validate.__signature__ = sig

        # Make version useable
        _version2 = _version.split('.')

        validate.__name__ = f'validate_{component_name}_{_version2[0]}_{_version2[1]}'
        validate.__doc__ = (
            """Validate object against {component:s} schema.

            Parameters
            ----------
            obj : object
                Object to validate

            Raises
            ------
            `ValidationError <https://python-jsonschema.readthedocs.io/en/latest/errors/#jsonschema.exceptions.ValidationError>`_
              If the object is not a valid {component:s}.

            Examples
            --------
            >>> validate_{component:s}({{'message': {{}}}})

            """.format(
                component=component_name
            )
        )

        setattr(
            sys.modules[__name__],
            validate.__name__,
            validate,
        )

    del validate
