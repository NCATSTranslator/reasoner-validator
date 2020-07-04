"""Test validation."""
import pytest

from jsonschema.exceptions import ValidationError

from reasoner_validate import validate_Query, validate_Credentials


def test_validate():
    """Test validate()."""
    validate_Query({
        'message': {}
    })
    with pytest.raises(ValidationError):
        validate_Query({
            'foo': {},
            'bar': {},
        })
    validate_Credentials({
        'username': 'foo',
        'password': 'bar',
    })
    with pytest.raises(ValidationError):
        validate_Credentials({
            'username': 1,
            'password': 'bar',
        })
