"""
FastAPI web service wrapper for TRAPI validator and Biolink Model compliance testing
"""
from typing import Optional, Dict
from sys import stderr
from pydantic import BaseModel

import uvicorn
from fastapi import FastAPI, HTTPException

from reasoner_validator.trapi import TRAPISchemaValidator
from reasoner_validator.versioning import get_latest_version
from reasoner_validator import TRAPIResponseValidator

app = FastAPI()


#
# We don't instantiate the full TRAPI models here but
# just use an open-ended dictionary which should have
# query_graph, knowledge_graph and results JSON tag-values
#

# Dictionary of validation context identifying the  ARA and KP
# sources subject to edge provenance attribute validation
# (key-value examples as given here)
class Sources(BaseModel):
    ara_source: Optional[str] = None,
    kp_source: Optional[str] = None,
    kp_source_type: Optional[str] = None


class Query(BaseModel):
    trapi_version: Optional[str] = get_latest_version(TRAPISchemaValidator.DEFAULT_TRAPI_VERSION)

    # default: latest Biolink Model Toolkit supported version
    biolink_version: Optional[str] = None

    # See Sources above
    sources: Optional[Sources] = Sources(ara_source="aragorn", kp_source="panther", kp_source_type="primary")

    # Apply strict validation of element abstract or mixin status of category, attribute_type_id and predicate elements
    # and detection of absent Knowledge Graph Edge predicate and attributes (despite 'nullable: true' model permission)
    strict_validation: Optional[bool] = None

    # validation normally reports empty Message query graph, knowledge graph and results as warnings.
    # This flag suppresses the reporting of such warnings (default: False)
    suppress_empty_data_warnings: Optional[bool] = None

    # A full Query.Response is (now) expected here, as described in:
    # https://github.com/NCATSTranslator/ReasonerAPI/blob/master/docs/reference.md#response-.
    response: Dict


@app.post("/validate")
async def validate(query: Query):

    if not query.response:
        raise HTTPException(status_code=400, detail="Empty input message?")

    trapi_version: Optional[str] = query.trapi_version
    print(f"Specified trapi_version == {trapi_version}", file=stderr)

    biolink_version: Optional[str] = query.biolink_version
    print(f"Specified biolink_version == {biolink_version}", file=stderr)

    sources: Optional[Sources] = query.sources
    print(f"Validation Context == {sources}", file=stderr)

    strict_validation: bool = query.strict_validation if query.strict_validation else False
    print(f"Validation Context == {str(strict_validation)}", file=stderr)

    suppress_empty_data_warnings: bool = \
        query.suppress_empty_data_warnings if query.suppress_empty_data_warnings else False
    print(f"suppress Empty Data Warnings == {str(suppress_empty_data_warnings)}", file=stderr)

    validator: TRAPIResponseValidator = TRAPIResponseValidator(
        trapi_version=trapi_version,
        biolink_version=biolink_version,
        sources=sources.dict(),
        strict_validation=strict_validation,
        suppress_empty_data_warnings=suppress_empty_data_warnings
    )
    validator.check_compliance_of_trapi_response(response=query.response)

    if not validator.has_messages():
        validator.report(code="info.compliant")

    return validator.to_dict()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
