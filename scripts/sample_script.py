#!/usr/bin/env python
from typing import Optional, List, Dict
from reasoner_validator.trapi.biolink.validator import TRAPIResponseValidator

SAMPLE_RESPONSE = {
    "schema_version": "1.4.1",
    "biolink_version": "3.2.6",
    "message": {
        "query_graph": {
            "nodes": {
                "type-2 diabetes": {"ids": ["MONDO:0005148"]},
                "drug": {"categories": ["biolink:Drug"]}
            },
            "edges": {
                "treats": {"subject": "drug", "predicates": ["biolink:treats"], "object": "type-2 diabetes"}
            }
        },
        "knowledge_graph": {
            "nodes": {
                "MONDO:0005148": {"name": "type-2 diabetes"},
                "CHEBI:6801": {"name": "metformin", "categories": ["biolink:Drug"]}
            },
            "edges": {
                "df87ff82": {"subject": "CHEBI:6801", "predicate": "biolink:treats", "object": "MONDO:0005148"}
            }
        },
        "results": [
            {
                "node_bindings": {
                    "type-2 diabetes": [{"id": "MONDO:0005148"}],
                    "drug": [{"id": "CHEBI:6801"}]
                },
                "edge_bindings": {
                    "treats": [{"id": "df87ff82"}]
                }
            }
        ]
    },
    "workflow": [
        {
            "id": "lookup"
        }
    ]
}

validator = TRAPIResponseValidator(
    # If the TRAPI version value is omitted or set to None,
    # then the latest TRAPI version applies.
    trapi_version="1.3.0",

    # If the Biolink Model version value is omitted or set to None,
    # then the current Biolink Model Toolkit default release applies.
    biolink_version="3.2.6",

    # Optional flag: if omitted or set to 'False', we let the system decide the
    # default validation strictness by validation context unless we override it here
    strict_validation=False
)

# Unlike earlier release of the package, validation methods do NOT throw an exception,
# but rather, return validation outcomes as a dictionary of validation messsages
# Here, the 'message' parameter here is just the Python equivalent dictionary of the
# TRAPI.Message JSON schema model component of the TRAPI Response (not the full TRAPI Response...yet)

# this method validates a complete TRAPI Response JSON result
validator.check_compliance_of_trapi_response(

    response=SAMPLE_RESPONSE,

    # 'target_provenance' is set to trigger checking of
    # expected edge knowledge source provenance
    target_provenance={
        "ara_source": "infores:molepro",
        "kp_source": "infores:hmdb",
        "kp_source_type": "primary"
    }
)

# Messages are retrieved from the validator object as follows:
messages: Dict[
            str,  # message type (errors|warnings|information)
            Dict[
                str,  # message 'code' as indexing key
                # Dictionary of 'identifier' indexed messages with parameters
                # (Maybe None, if code doesn't have any additional parameters)
                Optional[
                    Dict[
                        str,  # key is the message-unique template 'identifier' value of parameterized messages
                        Optional[
                            List[
                                # Each reported message adds a dictionary of such parameters
                                # to the list here; these are not guaranteed to be unique
                                Dict[str, str]
                            ]
                        ]
                    ]
                ]
            ]
        ] = validator.get_messages()

# this method dumps a human-readable text report of
# the validation messages to (by default) stdout
validator.dump()
