from jsonschema import ValidationError

from reasoner_validator import validate


def is_valid_trapi(instance, trapi_version):
    """Make sure that the Message is valid using reasoner_validator"""
    try:
        validate(
            instance=instance,
            component="Query",
            trapi_version=trapi_version
        )
        return True
    except ValidationError as e:
        print(e)
        return False
