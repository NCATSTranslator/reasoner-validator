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


def test_nullable_1_3():
    """Test nullable property."""
    qnode = {
        "category": None
    }
    validate(qnode, "QNode", "1.3")

    message = {
        "knowledge_graph": None,
        "query_graph": None,
        "results": None,
    }
    validate(message, "Message", "1.3")


def test_1_3_0_beta_empty_message():
    """Test 1.3.0-beta empty message in validate()."""
    validate({
        "message": {},
    }, "Query", "1.3.0-beta")
    with pytest.raises(ValidationError):
        validate({
            "foo": {},
            "bar": {},
        }, "Query", "1.3.0-beta")


def test_1_3_0_empty_message():
    """Test 1.3.0 empty message in validate()."""
    validate({
        "message": {},
    }, "Query", "1.3.0-beta")
    with pytest.raises(ValidationError):
        validate({
            "foo": {},
            "bar": {},
        }, "Query", "1.3.0")


sample_message_result = {
    "knowledge_graph": None,
    "query_graph": None,
    "results": [{"edge_bindings": {"ab": [{"attributes": None,
                                           "id": "uuid:7884e454-d09c-11ec-b00f-0242ac110002"}]},
                 "node_bindings": {"a": [{"attributes": None,
                                          "id": "SGD:S000000065",
                                          "qnode_id": "SGD:S000000065",
                                          "query_id": "None"}],
                                   "b": [{"attributes": None,
                                          "id": "GO:1905776",
                                          "query_id": "None"}]},
                 "score": None},
                {"edge_bindings": {"ab": [{"attributes": None,
                                           "id": "uuid:7884c8a2-d09c-11ec-b00f-0242ac110002"}]},
                 "node_bindings": {"a": [{"attributes": None,
                                          "id": "SGD:S000000065",
                                          "qnode_id": "SGD:S000000065",
                                          "query_id": "None"}],
                                   "b": [{"attributes": None,
                                          "id": "GO:0032079",
                                          "query_id": "None"}]},
                 "score": None}]
}


def test_120_results_component_validation():
    """Test Test 1.2.0 Message.Results component in validate()."""
    validate(sample_message_result, "Message", "1.2.0")
    with pytest.raises(ValidationError):
        validate({
            "foo": {},
            "bar": {},
        }, "Query", "1.2.0")


def test_1_3_0_results_component_validation():
    """Test Test 1.3.0 Message.Results component in validate()."""
    validate(sample_message_result, "Message", "1.3.0")
    with pytest.raises(ValidationError):
        validate({
            "foo": {},
            "bar": {},
        }, "Query", "1.3.0")
