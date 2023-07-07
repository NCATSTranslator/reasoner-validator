"""Test semantic version handling."""
import pytest

from tests import (
    PATCHED_SCHEMA_VERSION,
    PATCHED_140_SCHEMA_FILEPATH,
    BROKEN_SCHEMA_FILEPATH
)
from reasoner_validator.versioning import (
    semver_pattern,
    SemVer,
    SemVerError,
    SemVerUnderspecified
)


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


def test_fewer_core_fields():
    # test underspecified semver
    assert SemVer.from_string("1.2", core_fields=["major", "minor"])


def test_string_with_prefix():
    # test semver with (ignorable Pypi-style release) semver
    assert str(SemVer.from_string("v1.2.4", ignore_prefix=True)) == "1.2.4"
    assert str(SemVer.from_string("v1.2.4", ignore_prefix=False)) == "v1.2.4"


zero_zero_one = SemVer.from_string("0.0.1")
one_zero_zero = SemVer.from_string("1.0.0")
one_one_zero = SemVer.from_string("1.1.0")
one_one_one = SemVer.from_string("1.1.1")
one_one_zero_r = SemVer.from_string("1.1.0-R1")
one_one_one_r = SemVer.from_string("1.1.1-R1")
one_one_zero_r_b = SemVer.from_string("1.1.0-R1+build123")
one_one_one_r_b = SemVer.from_string("1.1.1-R2+build456")
one_three_zero = SemVer.from_string("1.3.0")
one_three_zero_beta = SemVer.from_string("1.3.0-beta")
one_four_zero = SemVer.from_string("1.4.0")
one_four_one = SemVer.from_string("1.4.1")
one_four_zero_beta = SemVer.from_string("1.4.0-beta")

one_three_only = SemVer.from_string("1.3", core_fields=['major', 'minor'])
one_four_only = SemVer.from_string("1.4", core_fields=['major', 'minor'])

# special pruned
one_four_one_beta_pruned = SemVer.from_string("1.4.1-beta", ext_fields=[])

one_four_zero_beta_one = SemVer.from_string("1.4.0-beta1")
one_four_zero_beta_four = SemVer.from_string("1.4.0-beta4")


def test_semver_greater_or_equal_to():
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

    # pruned SemVer comparisons
    assert one_four_one >= one_four_one_beta_pruned
    assert one_four_one_beta_pruned >= one_four_zero
    assert one_four_zero >= one_four_only
    assert one_four_zero >= one_three_only

    # ... real world comparisons
    assert one_three_zero >= one_three_zero_beta
    assert one_three_zero >= one_three_zero
    assert not one_three_zero_beta >= one_three_zero
    assert one_four_zero >= one_four_zero_beta
    assert not one_four_zero_beta >= one_four_zero
    assert one_four_zero >= one_three_zero
    assert one_four_zero >= one_four_zero_beta
    assert not one_four_zero_beta >= one_four_zero
    assert one_four_zero_beta_one >= one_four_zero_beta
    assert one_four_zero_beta_one >= one_four_zero_beta_one
    assert one_four_zero_beta_four >= one_four_zero_beta
    assert one_four_zero_beta_four >= one_four_zero_beta_one


def test_semver_equal_to():
    assert one_four_zero == one_four_zero
    assert one_four_zero_beta_one == one_four_zero_beta_one

    # Major release diff
    assert not zero_zero_one == one_three_zero

    # Minor release diff
    assert not one_zero_zero == one_one_zero

    # Patch release diff
    assert not one_one_zero == one_one_one

    # Prerelease release diff
    assert not one_four_zero == one_four_zero_beta_one
    assert not one_four_zero_beta_one == one_four_zero
    assert not one_four_zero_beta_one == one_four_zero_beta_four

    # pruned SemVer comparisons
    assert one_four_one == one_four_one_beta_pruned
    assert one_four_zero == one_four_only


def test_semver_not_equal_to():
    assert not one_four_zero != one_four_zero
    assert not one_four_zero_beta_one != one_four_zero_beta_one

    # Major release diff
    assert zero_zero_one != one_three_zero

    # Minor release diff
    assert one_zero_zero != one_one_zero

    # Patch release diff
    assert one_one_zero != one_one_one

    # Prerelease release diff
    assert one_four_zero != one_four_zero_beta_one
    assert one_four_zero_beta_one != one_four_zero
    assert one_four_zero_beta_one != one_four_zero_beta_four

    # pruned SemVer comparisons
    assert one_four_zero != one_four_one_beta_pruned
    assert one_four_zero != one_three_only


sample_schema_version = SemVer.from_string(PATCHED_SCHEMA_VERSION)
sample_schema_file_semver = SemVer.from_string(PATCHED_140_SCHEMA_FILEPATH)


def test_schema_file_versioning():
    # Sample schema file has internal version type
    assert sample_schema_file_semver == sample_schema_version
    with pytest.raises(SemVerError):
        SemVer.from_string(BROKEN_SCHEMA_FILEPATH)
