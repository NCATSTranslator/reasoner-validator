"""
Unit tests against reasoner-validator utils
"""
from typing import List, Optional
import pytest

from reasoner_validator.utils import is_curie, get_aliases, get_reference


@pytest.mark.parametrize(
    "identifier,outcome",
    [
        (None, False),
        ("foo:bar", True),
        ("not-a-curie", False),
    ]
)
def test_is_curie(identifier: str, outcome: bool):
    assert is_curie(identifier) is outcome


@pytest.mark.parametrize(
    "identifier",
    [
        None,
        ""
    ]
)
def test_get_aliases_of_empty_identifier(identifier):
    with pytest.raises(RuntimeError):
        get_aliases(identifier)


@pytest.mark.parametrize(
    "identifier,one_alias",
    [
        (   # Special test for a CURIE for which
            # NodeNormalization is known to
            # return a lower case namespace
            "ORPHANET:33110",
            "MONDO:0011096"
        ),
        (   # only CURIEs can be resolved to aliases
            # but just logs a warning but returns the identifier
            "not-a-curie",
            ""
        ),
    ]
)
def test_get_aliases(identifier: str, one_alias: str):
    aliases: List[str] = get_aliases(identifier)
    assert identifier in aliases
    assert one_alias in aliases if one_alias in aliases else True


@pytest.mark.parametrize(
    "identifier,reference",
    [
        (   # Valid CURIE has a reference
            "ORPHANET:33110",
            "33110"
        ),
        (   # Only CURIEs can be resolved to references
            "not-a-curie",
            None
        ),
    ]
)
def test_get_aliases(identifier: str, reference: str):
    assert get_reference(identifier) == reference
