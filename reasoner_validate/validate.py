"""OpenAPI validation."""
import copy
import sys

import jsonschema
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
to_load = pkg_resources.read_text(data, 'TranslatorReasonersAPI.yml')

spec = yaml.load(to_load, Loader=Loader)
components = spec['components']['schemas']
for component_name in components:
    # build json schema against which we validate
    other_components = copy.deepcopy(components)
    schema = other_components.pop(component_name)
    schema['components'] = {'schemas': other_components}

    def validate(obj, schema=schema):
        """Validate object against JSON schema."""
        jsonschema.validate(obj, schema)
    validate.__name__ = f'validate_{component_name}'

    setattr(
        sys.modules[__name__],
        validate.__name__,
        validate,
    )
