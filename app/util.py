from typing import Optional, Dict
from jsonschema import ValidationError
from pydantic import BaseModel
from reasoner_validator import validate

# Default is actually specifically 1.2.0 as of April 2022,
# but the Reasoner validator should discern this
DEFAULT_TRAPI_VERSION = "1"


#
# We don't instantiate the full TRAPI models here but
# just use an open-ended dictionary which should have
# query_graph, knowledge_graph and results JSON tag-values
#
class Query(BaseModel):
    version: Optional[str] = DEFAULT_TRAPI_VERSION
    message: Dict


def is_valid_trapi(instance, trapi_version) -> str:
    """Make sure that the Message is valid using reasoner_validator"""
    try:
        validate(
            instance=instance,
            component="Query",
            trapi_version=trapi_version
        )
        return "Valid TRAPI Message"
    except ValidationError as e:
        return f"Invalid TRAPI Message: '{e.message}'"
