"""Test validation."""
import pytest

from jsonschema.exceptions import ValidationError

from reasoner_validator import (
    validate_EdgeBinding, validate_Query,
    validate_QNode, validate_Message,
)


def test_query():
    """Test validate_Query()."""
    validate_Query({
        'message': {},
    })
    with pytest.raises(ValidationError):
        validate_Query({
            'foo': {},
            'bar': {},
        })


def test_edgebinding():
    """Test validate_EdgeBinding()."""
    validate_EdgeBinding({
        'id': 'hello',
    })
    with pytest.raises(ValidationError):
        validate_EdgeBinding({
            'foo': {},
        })


def test_nullable():
    """Test nullable property."""
    qnode = {
        "category": None
    }
    validate_QNode(qnode)

    message = {
        "knowledge_graph": None,
        "query_graph": None,
        "results": None,
    }
    validate_Message(message)
