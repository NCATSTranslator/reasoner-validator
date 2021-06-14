"""Test semantic version handling."""
import pytest

from reasoner_validator.util import SemVerUnderspecified, semver_pattern, SemVer


def test_pattern():
    assert semver_pattern.fullmatch("1.2.3")
    assert semver_pattern.fullmatch("1.2")
    assert semver_pattern.fullmatch("1")
    assert semver_pattern.fullmatch("a.2.3") is None
    assert semver_pattern.fullmatch("1.2.3.4") is None
    assert str(SemVer.from_string("1.2.4")) == "1.2.4"
    with pytest.raises(SemVerUnderspecified):
        assert str(SemVer.from_string("1.2"))
