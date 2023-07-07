"""Utilities."""
from typing import NamedTuple, Optional, List
from os import environ
from re import sub, compile
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
versions = [release["tag_name"] for release in release_data]

response = requests.get(f"https://api.github.com/repos/{GIT_ORG}/{GIT_REPO}/branches")
branch_data = response.json()
branches = [
    branch["name"] for branch in branch_data
]

# This is modified version of a standard SemVer regex which
# takes into account the possibility of capturing a non-numeric prefix
semver_pattern = compile(
    r"^(?P<prefix>[a-zA-Z]*)(?P<major>0|[1-9]\d*)(\.(?P<minor>0|[1-9]\d*)(\.(?P<patch>0|[1-9]\d*))?)?" +
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][\da-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][\da-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[\da-zA-Z-]+(?:\.[\da-zA-Z-]+)*))?$"
)


class SemVerError(Exception):
    """Invalid semantic version."""


class SemVerUnderspecified(SemVerError):
    """Semantic version underspecified."""


class SemVer(NamedTuple):

    prefix: str = ""
    major: int = 0
    minor: int = 0
    patch: int = 0
    prerelease: Optional[str] = None
    buildmetadata: Optional[str] = None

    @classmethod
    def from_string(
        cls,
        string: str,
        ignore_prefix: bool = False,
        core_fields: List[str] = ('major', 'minor', 'patch'),
        ext_fields: List[str] = ('prerelease', 'buildmetadata')

    ):
        """
        Initializes a SemVer from a string.  This is an 'augmented' SemVer which may also have an alphabetic prefix
        (for example, a 'v' for 'version' designation of a GitHub release). Note that the string may be a
        YAML file (path) name. In such a case, the SemVer is assumed to be encoded as a suffix in the root file name
        just before the .yaml file extension - e.g. my_schema_3.2.1-beta5.yaml - where the version suffix string
        is assumed to be delimited by a leading underscore character (i.e. "3.2.1-beta5" in the above example).

        :param string: str, string encoding the SemVer.
        :param ignore_prefix: bool, if set, any alphabetic prefix of the SemVer string is ignored (not recorded)
                              the SemVer string value, e.g. a Git Release 'v' character (i.e. v1.2.3); Default: False.
        :param core_fields: List[str], list of names of core SemVer field to explicitly set (may NOT be empty?)
                                       (default: ['major', 'minor', 'patch']).
        :param ext_fields: List[str], list of names of extended SemVer fields to explicitly set (maybe empty?)
                                      (default: ['prerelease', 'buildmetadata']).
        :return:
        """
        # sanity check on required and allowed parameters
        assert string
        # print(core_fields, file=stderr)
        assert len(core_fields) > 0 and all([field in ['major', 'minor', 'patch'] for field in core_fields])
        assert len(core_fields) >= 1 and 'major' in core_fields
        assert len(core_fields) >= 2 and 'major' in core_fields and 'minor' in core_fields
        assert all([field in ['prerelease', 'buildmetadata'] for field in ext_fields])

        # If the string is a file path, generically detected using the .yaml file extension,
        # then assume that the file path string encodes the SemVer string, as a part of the
        # root file name just before the .yaml file extension, e.g. my_schema_3.2.1-beta5.yaml
        #
        # Note that the TRAPI version suffix to the root file name
        # is assumed to be delimited by a leading underscore character.
        if string.endswith(".yaml"):
            root_path: str = string.replace(".yaml", "")
            semver_string = root_path.split("_")[-1]
        else:
            semver_string = string

        match = semver_pattern.fullmatch(semver_string)

        if match is None:
            if string.endswith(".yaml"):
                raise SemVerError(
                    "the mandatory TRAPI 'Semantic Version' suffix string of the root file (path) name:\n"
                    f"\t'{string}'\nof your local YAML schema file, must delimited from the prefix of "
                    f"the root file (path) name by a leading underscore character!"
                )
            else:
                raise SemVerError(f"'{string}' is not a valid release version!")

        captured = match.groupdict()
        missing_fields_errmsg = f"SemVer '{string}' is missing expected fields: {', '.join(core_fields)}"

        observed_prefix = captured["prefix"] if not ignore_prefix else ""
        core_field_values: List[int] = list()
        for field in ['major', 'minor', 'patch']:
            if field in core_fields:
                if field in captured and captured[field] is not None:
                    core_field_values.append(int(captured[field]))
                else:
                    raise SemVerUnderspecified(missing_fields_errmsg)
            else:
                core_field_values.append(0)

        ext_field_values: List[Optional[str]] = list()
        for field in ['prerelease', 'buildmetadata']:
            if field in ext_fields and field in captured:
                ext_field_values.append(captured[field])
            else:
                ext_field_values.append(None)
        try:
            return cls(
                observed_prefix,
                *core_field_values,
                *ext_field_values
            )
        except TypeError:
            raise SemVerUnderspecified(missing_fields_errmsg)

    def __str__(self):
        """Generate string."""
        value = f"{self.prefix}{self.major}"
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
def _semver_eq_(obj: SemVer, other: SemVer) -> bool:
    """
    Equal operator ('==') override.
    :param obj: SemVer
    :param other: SemVer
    :return: bool, True if obj and other are equal
    """
    # Clearcut cases of 'major' release ordering
    if obj.major != other.major:
        return False
    # obj.major == other.major

    # Check 'minor' level
    elif obj.minor != other.minor:
        return False
    # obj.minor == other.minor

    # Check 'patch' level
    elif obj.patch != other.patch:
        return False
    # obj.patch == other.patch

    # Check 'prerelease' tagging
    elif (obj.prerelease is None and other.prerelease is None) or obj.prerelease == other.prerelease:
        return True

    return False


SemVer.__eq__ = _semver_eq_


def _semver_ne_(obj: SemVer, other: SemVer) -> bool:
    """
    Equal operator ('!=') override.
    :param obj: SemVer
    :param other: SemVer
    :return: bool, True if obj and other are NOT equal
    """
    return not _semver_eq_(obj, other)


SemVer.__ne__ = _semver_ne_


def _semver_ge_(obj: SemVer, other: SemVer) -> bool:
    """
    Greater than or equal operator ('>=') override.
    :param obj: SemVer
    :param other: SemVer
    :return: bool, True if obj >= other
    """
    # Clearcut cases of 'major' release ordering
    if obj.major > other.major:
        return True
    elif obj.major < other.major:
        return False

    # obj.major == other.major

    # Now check 'minor' level
    elif obj.minor > other.minor:
        return True
    elif obj.minor < other.minor:
        return False

    # obj.minor == other.minor

    # Now check 'patch' level
    elif obj.patch > other.patch:
        return True
    elif obj.patch < other.patch:
        return False

    # obj.patch == other.patch

    # Now check 'prerelease' tagging
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

_latest = dict()


# Provide an accessor function for retrieving the latest version in string format
def get_latest_version(release_tag: Optional[str]) -> Optional[str]:
    """
    Return the latest TRAPI version corresponding to the release tag given.
    Note that if the release tag looks like a YAML file, then it is assumed
    to be a direct schema specification. If a Git branch name in the schema
    repository, the branch name is also passed on.

    :param release_tag: (possibly partial) SemVer string, Git branch name,
                        or YAML schema file name identifying a release.
    :return: 'best' latest release of SemVer specification or the YAML file directly returned.
    """
    global _latest

    if not release_tag:
        return None
    elif release_tag.lower().endswith(".yaml"):
        return release_tag
    elif release_tag in branches:
        # cases in which a branch name is
        # given instead of a release number
        return release_tag
    else:
        # strip any prefix from the release tag to ensure that
        # only the SemVer part is used for the latest version lookup
        release = sub(r'^[^0-9]+', '', release_tag)
        latest: SemVer = _latest.get(release, None)
        return str(latest) if latest else None


def _set_preferred_version(release_tag: str, target_release: SemVer):
    global _latest
    latest_4_release_tag: Optional[SemVer] = _latest.get(release_tag, None)
    if not latest_4_release_tag or (target_release >= latest_4_release_tag):
        _latest[release_tag] = target_release


for version in versions:

    prefix: str = ""
    major: Optional[int] = None
    minor: Optional[int] = None
    patch: Optional[int] = None
    prerelease: Optional[str] = None
    # buildmetadata: Optional[str] = None

    try:
        prefix, major, minor, patch, prerelease, buildmetadata = SemVer.from_string(version)
    except SemVerError as err:
        print("\nWARNING:", err)
        continue

    candidate_release: SemVer = SemVer(
        prefix=prefix,
        major=major,
        minor=minor,
        patch=patch,
        prerelease=prerelease
    )

    if str(candidate_release) in versions:
        _set_preferred_version(f"{major}", candidate_release)
        _set_preferred_version(f"{major}.{minor}", candidate_release)
        _set_preferred_version(f"{major}.{minor}.{patch}", candidate_release)
        if prerelease:
            _set_preferred_version(f"{major}.{minor}.{patch}-{prerelease}", candidate_release)
        # TODO: we won't bother with buildmetadata for now
