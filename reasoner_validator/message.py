"""
This module provides standalone global reasoner-validator validation Message types
to avoid load order conflicts for other modules using these data types.
"""
from enum import Enum
from typing import Optional, List, Dict

#
# The MESSAGE_CATALOG data structure is something like the following:
#
#  {
#    # message 'type'
#     "information": {
#
#        # message 'code'
#         "info.input_edge.predicate.mixin": {
#
#             # message 'scope' may be a source_trail (as shown) or "global"
#             "infores:molepro -> infores:arax": {
#
#                 # characteristic "identifier" to which the validation message specifically applies
#                 "biolink:interacts_with"[
#                     {  # parameters of a distinct message
#                       "edge_id": "a--biolink:interacts_with->b"
#                     },
#                     { <parameters of second reported message...> },
#                     etc...
#                 ]
#             }
#         } ,
#         # codes without parameters can just be set to an empty list?
#         "info.compliant.message": {"global": []}
#
#     },
#     "warnings":  {
#       ...<similar to information data structure above>
#     },
#     "errors": {
#       ...<similar to information data structure above>
#     },
#     "critical": {
#       ...<similar to information data structure above>
#     }
# }
#

# One instance of 'MESSAGE_PARAMETERS' is a dictionary of string
# parameters associated with a  given message code, as documented
# within the global 'codes.yaml' validation message catalog
MESSAGE_PARAMETERS = Dict[str, str]

# An 'IDENTIFIED_MESSAGES' data structure is a dictionary of Lists
# parameterized messages, indexed by a unique 'identifier' discriminator
# (i.e. the Biolink Model or TRAPI token target of the validation)
IDENTIFIED_MESSAGES = Dict[
    str,  # key is the message-unique template 'identifier' value of parameterized messages

    # Note: some message codes may not have any associated
    # parameters beyond their discriminating identifier
    Optional[List[MESSAGE_PARAMETERS]]
]

# A 'SCOPED_MESSAGES' data structure is a dictionary of message parameters associated to a
# particular coded message and resolved as to knowledge source. The scope may be 'global' or
# defined by a 'source trail' of knowledge source specified by infores,
# from a biolink:primary_knowledge_source up to a topmost biolink:aggregator_knowledge_source
# retrieving the given knowledge assertion (Subject-Predicate-Object statement with evidence).
SCOPED_MESSAGES = Dict[
    str,  # 'source trail' origin of affected edge or 'global' validation error

    # (A given message code may have
    # no IDENTIFIED_MESSAGES with discriminating identifier
    #  and parameters hence, it may have a scoped value of 'None')
    Optional[IDENTIFIED_MESSAGES]
]

# A 'MESSAGE_PARTITION' is a dictionary of coded messages,
# indexed by validation code and corresponding to one of the
# four major categories of validation messages:
# critical/errors/warnings/information
MESSAGE_PARTITION = Dict[
    str,  # message 'code' as indexing key
    SCOPED_MESSAGES
]


class MessageType(Enum):
    info = "information"
    skipped = "skipped tests"
    warning = "warnings"
    error = "errors"
    critical = "critical errors"


# A individual MESSAGE_CATALOG contains
# the validation messages from
# all five major categories of validation:
# critical errors/errors/warnings/skipped tests/information
MESSAGE_CATALOG = Dict[
    str,  # message type (critical/error/warning/skipped/info)
    MESSAGE_PARTITION
]

# MESSAGES_BY_TEST contains MESSAGE_CATALOG
# entries indexed by individual tests
MESSAGES_BY_TEST = Dict[
    str,  # unique identifiers for each test
    MESSAGE_CATALOG
]

# MESSAGES_BY_TARGET contains MESSAGES_BY_TEST entries
# indexed by target: endpoint URL, URI or CURIE
MESSAGES_BY_TARGET = Dict[
    str,  # target identifier: endpoint URL, URI or CURIE
    MESSAGES_BY_TEST
]
