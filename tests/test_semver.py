"""Test semantic version handling."""
import pytest

from reasoner_validator.versioning import semver_pattern, SemVer, SemVerError, SemVerUnderspecified


def test_regex_pattern():
    # test the semver pattern directly
    assert semver_pattern.fullmatch("1.2.3")
    assert semver_pattern.fullmatch("1.2")
    assert semver_pattern.fullmatch("1")
    assert semver_pattern.fullmatch("1.3-beta")
    assert semver_pattern.fullmatch("1.3-rc.1")
    assert semver_pattern.fullmatch("1.3-rc.1+build.123")
    assert semver_pattern.fullmatch("a.2.3") is None
    assert semver_pattern.fullmatch("1.2.3.4") is None


def test_from_string():
    # test simple semver patterns without prefixes
    assert str(SemVer.from_string("1.2.4")) == "1.2.4"
    assert str(SemVer.from_string("1.2.4-beta")) == "1.2.4-beta"
    assert str(SemVer.from_string("1.2.4-alpha+build.123")) == "1.2.4-alpha+build.123"
    assert str(SemVer.from_string("1.2.4+build.123")) == "1.2.4+build.123"


def test_underspecified_string():
    # test underspecified semver
    with pytest.raises(SemVerUnderspecified):
        assert str(SemVer.from_string("1.2"))


def test_string_with_prefix():
    # test semver with (ignorable Pypi-style release) semver
    assert str(SemVer.from_string("v1.2.4", ignore_prefix='v')) == "1.2.4"
    with pytest.raises(SemVerError):
        assert str(SemVer.from_string("v1.2.4"))


def test_semver_greater_or_equal_to():
    zero_zero_one = SemVer.from_string("0.0.1")
    one_zero_zero = SemVer.from_string("1.0.0")
    one_one_zero = SemVer.from_string("1.1.0")
    one_one_one = SemVer.from_string("1.1.1")
    one_one_zero_r = SemVer.from_string("1.1.0-R1")
    one_one_one_r = SemVer.from_string("1.1.1-R1")
    one_one_zero_r_b = SemVer.from_string("1.1.0-R1+build123")
    one_one_one_r_b = SemVer.from_string("1.1.1-R2+build456")

    # Major release diff
    assert one_zero_zero >= zero_zero_one
    assert not zero_zero_one >= one_zero_zero

    # Minor release diff
    assert one_one_zero >= one_zero_zero
    assert not one_zero_zero >= one_one_zero

    # Patch release diff
    assert one_one_one >= one_one_zero
    assert not one_one_zero >= one_one_one

    # Patch release diff ignores the prerelease ...
    assert one_one_one_r >= one_one_zero_r
    assert not one_one_zero_r >= one_one_one_r
    assert one_one_one_r >= one_one_zero
    assert not one_one_zero >= one_one_one_r

    # ... and build subvariants
    assert one_one_one_r_b >= one_one_zero_r_b
    assert not one_one_zero_r_b >= one_one_one_r_b
    assert one_one_one_r_b >= one_one_zero_r
    assert not one_one_zero_r >= one_one_one_r_b
    assert one_one_one_r_b >= one_one_zero
    assert not one_one_zero >= one_one_one_r_b
