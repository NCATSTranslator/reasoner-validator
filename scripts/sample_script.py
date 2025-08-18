#!/usr/bin/env python
from api import SAMPLE_TRAPI_RESPONSE
from reasoner_validator.message import MESSAGES_BY_TARGET
from reasoner_validator.validator import TRAPIResponseValidator


validator = TRAPIResponseValidator(
    # If the TRAPI version value is omitted or set to None,
    # then the latest TRAPI version applies.
    trapi_version="1.5.0",

    # If the Biolink Model version value is omitted or set to None,
    # then the current Biolink Model Toolkit default release applies.
    biolink_version="4.2.0",

    # 'target_provenance' is set to trigger checking of
    # expected edge knowledge source provenance
    target_provenance={
        "target_ara_source": "infores:molepro",
        "target_kp_source": "infores:hmdb",
        "target_kp_source_type": "primary"
    },

    # Optional flag: if omitted or set to 'False', we let the system decide the
    # default validation strictness by validation context unless we override it here
    strict_validation=False
)

# Unlike earlier release of the package, validation methods do NOT throw an exception,
# but rather, return validation outcomes as a dictionary of validation messages
# Here, the 'message' parameter here is just the Python equivalent dictionary of the
# TRAPI Response of the TRAPI.Message JSON schema model (not the full TRAPI Response...yet)

# this method validates a complete TRAPI Response JSON result
validator.check_compliance_of_trapi_response(response=SAMPLE_TRAPI_RESPONSE)

# Messages are retrieved from the validator object as follows:
messages: MESSAGES_BY_TARGET = validator.get_all_messages()

# where MESSAGES_BY_TARGET is:
#
# Dict[
#     str,  # target identifier: endpoint URL, URI or CURIE
#     Dict[
#         str,  # unique identifiers for each test
#         Dict[
#             str,  # message type (info|skipped|warning|error|critical)
#             Dict[
#                 str,  # message 'code' as indexing key
#                 # Dictionary of 'identifier' indexed messages with parameters
#                 # (Maybe None, if code doesn't have any additional parameters)
#                 Optional[
#                     Dict[
#                         str,  # key is the message-unique template 'identifier' value of parameterized messages
#                         Optional[
#                             List[
#                                 # Each reported message adds a dictionary of such parameters
#                                 # to the list here; these are not guaranteed to be unique
#                                 Dict[str, str]
#                             ]
#                         ]
#                     ]
#                 ]
#             ]
#         ]
#     ]
# ]
#
# this method dumps a human-readable text report of
# the validation messages to (by default) stdout
validator.dump()
