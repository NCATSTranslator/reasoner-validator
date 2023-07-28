from reasoner_validator.versioning import SemVer

TRAPI_1_3_0_SEMVER = SemVer.from_string("v1.3.0")
TRAPI_1_3_0: str = str(TRAPI_1_3_0_SEMVER)
TRAPI_1_4_0_BETA_SEMVER = SemVer.from_string("v1.4.0-beta")
TRAPI_1_4_0_BETA = str(TRAPI_1_4_0_BETA_SEMVER)
TRAPI_1_4_0_BETA2_SEMVER = SemVer.from_string("v1.4.0-beta2")
TRAPI_1_4_0_BETA3_SEMVER = SemVer.from_string("v1.4.0-beta3")
TRAPI_1_4_0_BETA4_SEMVER = SemVer.from_string("v1.4.0-beta4")
TRAPI_1_4_0_SEMVER = SemVer.from_string("v1.4.0")
TRAPI_1_4_0: str = str(TRAPI_1_4_0_SEMVER)
TRAPI_1_4_1_SEMVER = SemVer.from_string("v1.4.1")
TRAPI_1_4_1: str = str(TRAPI_1_4_1_SEMVER)
TRAPI_1_4_2_SEMVER = SemVer.from_string("v1.4.2")
TRAPI_1_4_2: str = str(TRAPI_1_4_2_SEMVER)

LATEST_TRAPI_RELEASE_SEMVER: SemVer = TRAPI_1_4_2_SEMVER
LATEST_TRAPI_RELEASE: str = TRAPI_1_4_2
LATEST_TRAPI_MAJOR_RELEASE_SEMVER: SemVer = SemVer.from_string("v1.4", core_fields=['major', 'minor'])
LATEST_TRAPI_MAJOR_RELEASE: str = str(LATEST_TRAPI_MAJOR_RELEASE_SEMVER)
