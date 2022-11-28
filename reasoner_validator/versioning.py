"""Utilities."""
import re
from os import environ
from typing import NamedTuple, Optional

import requests

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


# Undocumented possible local environmental variable
# override of the ReasonerAPI schema access endpoint
GIT_ORG = environ.setdefault('GIT_ORGANIZATION', "NCATSTranslator")
GIT_REPO = environ.setdefault('GIT_REPOSITORY', "ReasonerAPI")

response = requests.get(f"https://api.github.com/repos/{GIT_ORG}/{GIT_REPO}/releases")
releases = response.json()
versions = [
    release["tag_name"][1:]
    for release in releases
    if release["tag_name"].startswith("v")
]


semver_pattern = re.compile(
    r"^(?P<major>0|[1-9]\d*)(\.(?P<minor>0|[1-9]\d*)(\.(?P<patch>0|[1-9]\d*))?)?" +
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][\da-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][\da-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[\da-zA-Z-]+(?:\.[\da-zA-Z-]+)*))?$"
)


class SemVerError(Exception):
    """Invalid semantic version."""


class SemVerUnderspecified(SemVerError):
    """Semantic version underspecified."""


class SemVer(NamedTuple):
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    buildmetadata: Optional[str] = None

    @classmethod
    def from_string(cls, string: str, ignore_prefix: Optional[str] = None):
        """
        Initializes a SemVer from a string.

        :param string: str, string encoding the SemVer.
        :param ignore_prefix: Optional[str], if set, gives a prefix of the SemVer string to be ignored before validating
                              the SemVer string value, e.g. a Git Release 'v' character (i.e. v1.2.3); Default: None.
        :return:
        """
        if ignore_prefix:
            string = string.replace(ignore_prefix, "")

        match = semver_pattern.fullmatch(string)

        if match is None:
            raise SemVerError(f"'{string}' is not a valid release version")

        captured = match.groupdict()
        if not all([group in captured for group in ['major', 'minor', 'patch']]):
            raise SemVerUnderspecified(f"'{string}' is missing minor and/or patch versions")
        try:
            return cls(
                *[int(captured[group]) for group in ['major', 'minor', 'patch']],
                *[captured[group] for group in ['prerelease', 'buildmetadata']],
            )
        except TypeError:
            raise SemVerUnderspecified(f"'{string}' is missing minor and/or patch versions")

    def __str__(self):
        """Generate string."""
        value = f"{self.major}"
        if self.minor is not None:
            value += f".{self.minor}"
        if self.patch is not None:
            value += f".{self.patch}"
        if self.prerelease is not None:
            value += f"-{self.prerelease}"
        if self.buildmetadata is not None:
            value += f"+{self.buildmetadata}"
        return value


###########################################
# Deferred SemVer method creation to work #
# around SemVer forward definitions issue #
###########################################
def _semver_ge_(obj: SemVer, other: SemVer) -> bool:
    # Clearcut cases of 'major' release ordering
    if obj.major > other.major:
        return True
    elif obj.major < other.major:
        return False

    # obj.major == other.major
    # Check 'minor' level
    elif obj.minor > other.minor:
        return True
    elif obj.minor < other.minor:
        return False

    # obj.minor == other.minor
    # Check 'patch' level
    elif obj.patch >= other.patch:
        return True
    else:
        # obj.patch < other.patch
        return False


SemVer.__ge__ = _semver_ge_


latest_patch = dict()
latest_minor = dict()
latest_prerelease = dict()
latest = dict()
for version in versions:
    try:
        major, minor, patch, prerelease, buildmetadata = SemVer.from_string(version)
    except SemVerError as err:
        print("\nWARNING:", err)
        continue

    latest_minor[major] = max(minor, latest_minor.get(major, -1))
    latest_patch[(major, minor)] = max(patch, latest_patch.get((major, minor), -1))
    latest_prerelease[(major, minor, patch)] = prerelease \
        if prerelease and not latest_prerelease.get((major, minor, patch), None) else None

    latest[f"{major}"] = str(SemVer(
        major,
        latest_minor[major],
        latest_patch[(major, latest_minor[major])],
    ))
    latest[f"{major}.{minor}"] = str(SemVer(
        major,
        minor,
        latest_patch[(major, minor)],
    ))
    latest[f"{major}.{minor}.{patch}"] = str(SemVer(
        major,
        minor,
        patch,
    ))
    if prerelease:
        latest[f"{major}.{minor}.{patch}-{prerelease}"] = str(SemVer(
            major,
            minor,
            patch,
            prerelease,
            buildmetadata
        ))
    # TODO: we won't bother with buildmetadata for now
