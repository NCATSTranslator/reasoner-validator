"""
Unit tests for validation of Infores identifiers against the InfoRes catalog
"""
import pytest

from reasoner_validator.biolink.infores import is_infores


@pytest.mark.parametrize(
    "identifier,outcome",
    [
        ("infores:molepro", True),
        (" infores:molepro ", True),  # surrounding whitespace is ignored
        ("infores:not-a-registered-infores", False),
        ("molepro", False),  # 'infores:' prefix is required
        ("", False),
        (None, False)
    ]
)
def test_is_infores(identifier: str, outcome: bool):
    assert is_infores(identifier) is outcome
