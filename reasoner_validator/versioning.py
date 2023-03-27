"""Utilities."""
import re
from typing import NamedTuple, Optional, List
from os import environ
from functools import lru_cache
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
release_data = response.json()
versions = [
    release["tag_name"][1:]
    for release in release_data
    if release["tag_name"].startswith("v")
]

response = requests.get(f"https://api.github.com/repos/{GIT_ORG}/{GIT_REPO}/branches")
branch_data = response.json()
branches = [
    branch["name"] for branch in branch_data
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
    @lru_cache(maxsize=32)
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
    elif obj.patch > other.patch:
        return True
    elif obj.patch < other.patch:
        return False

    # obj.patch == other.patch

    # Check 'prerelease' tagging
    elif obj.prerelease and not other.prerelease:
        return False
    elif not obj.prerelease:
        return True

    # or compare two non-empty prerelease spec strings
    elif obj.prerelease >= other.prerelease:
        # cheating heuristic for now:
        # simple prerelease string comparison
        return True
    else:
        return False

    # TODO: more comprehensive comparison needed (below)
    # See: https://semver.org/ for the following precedence rules:
    #
    # Precedence for two pre-release versions with the same major, minor, and patch version MUST be determined by
    # comparing each dot separated identifier from left to right until a difference is found as follows:
    #
    # 1. Identifiers consisting of only digits are compared numerically.
    # 2. Identifiers with letters or hyphens are compared lexically in ASCII sort order.
    # 3. Numeric identifiers always have lower precedence than non-numeric identifiers.
    # 4. A larger set of pre-release fields has a higher precedence than a smaller set,
    #    if all of the preceding identifiers are equal.
    #
    # Example:
    # 1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-alpha.beta < 1.0.0-beta < 1.0.0-beta.2 < 1.0.0-beta.11 < 1.0.0-rc.1 < 1.0.0
    # obj_path: List = obj.prerelease.split(".")
    # other_path: List = other.prerelease.split(".")
    # path_length: int = min(len(obj_path),len(other_path))
    # for i in range(0, path_length):
    #     fobj = obj_path[i]
    #     oobj = other_path[i]


SemVer.__ge__ = _semver_ge_

latest_patch = dict()
latest_minor = dict()
latest_prerelease = dict()

_latest = dict()


# Provide an accessor function for retrieving the latest version in string format
def get_latest_version(release_tag: str) -> Optional[str]:
    global _latest
    return str(_latest.get(release_tag, None))


def _set_preferred_version(release_tag: str, candidate_release: SemVer):
    global _latest
    latest_4_release_tag: Optional[SemVer] = _latest.get(release_tag, None)
    if not latest_4_release_tag or (candidate_release >= latest_4_release_tag):
        _latest[release_tag] = candidate_release


for version in versions:

    major: Optional[int] = None
    minor: Optional[int] = None
    patch: Optional[int] = None
    prerelease: Optional[str] = None
    buildmetadata: Optional[str] = None

    try:
        major, minor, patch, prerelease, buildmetadata = SemVer.from_string(version)
    except SemVerError as err:
        print("\nWARNING:", err)
        continue

    candidate_release: SemVer = SemVer(
        major,
        minor,
        patch,
        prerelease
    )

    if str(candidate_release) in versions:
        _set_preferred_version(f"{major}", candidate_release)
        _set_preferred_version(f"{major}.{minor}", candidate_release)
        _set_preferred_version(f"{major}.{minor}.{patch}", candidate_release)
        if prerelease:
            _set_preferred_version(f"{major}.{minor}.{patch}-{prerelease}", candidate_release)
        # TODO: we won't bother with buildmetadata for now
