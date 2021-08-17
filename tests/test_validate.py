"""Test validation."""
import pytest

from jsonschema.exceptions import ValidationError

from reasoner_validator import validate


def test_query():
    """Test validate()."""
    validate({
        "message": {},
    }, "Query", "1.0.3")
    with pytest.raises(ValidationError):
        validate({
            "foo": {},
            "bar": {},
        }, "Query", "1.0.3")


def test_version_completion():
    """Test validate() with version completion."""
    validate({
        "message": {},
    }, "Query", "1.0")
    with pytest.raises(ValidationError):
        validate({
            "foo": {},
            "bar": {},
        }, "Query", "1")


def test_edgebinding():
    """Test validate_EdgeBinding()."""
    validate({
        "id": "hello",
    }, "EdgeBinding", "1.0.3")
    with pytest.raises(ValidationError):
        validate({
            "foo": {},
        }, "EdgeBinding", "1.0.3")


def test_nullable():
    """Test nullable property."""
    qnode = {
        "category": None
    }
    validate(qnode, "QNode", "1.0.3")

    message = {
        "knowledge_graph": None,
        "query_graph": None,
        "results": None,
    }
    validate(message, "Message", "1.0.3")
