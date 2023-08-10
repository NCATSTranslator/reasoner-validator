"""
FastAPI web service wrapper for TRAPI validator and Biolink Model compliance testing
"""
from typing import Optional, Dict
from sys import stderr
from pydantic import BaseModel

import uvicorn
from fastapi import FastAPI, HTTPException

from bmt import Toolkit

from reasoner_validator.trapi import TRAPISchemaValidator
from reasoner_validator.versioning import get_latest_version
from reasoner_validator.validator import TRAPIResponseValidator

default_toolkit: Toolkit = Toolkit()
DEFAULT_BIOLINK_MODEL_VERSION = default_toolkit.get_model_version()

app = FastAPI()


# Dictionary of validation context identifying the  ARA and KP
# target KP and ARA knowledge sources subject to edge provenance attribute validation
# (key-value examples as given here)
# Example: TargetProvenance(ara_source="aragorn", kp_source="panther", kp_source_type="primary")
class TargetProvenance(BaseModel):
    ara_source: Optional[str] = None,
    kp_source: Optional[str] = None,
    kp_source_type: Optional[str] = None


class Query(BaseModel):

    trapi_version: Optional[str] = get_latest_version(TRAPISchemaValidator.DEFAULT_TRAPI_VERSION)

    # default: latest Biolink Model Toolkit supported version
    biolink_version: Optional[str] = DEFAULT_BIOLINK_MODEL_VERSION

    # See TargetProvenance above
    target_provenance: Optional[TargetProvenance] = None

    # Apply strict validation of element abstract or mixin status of category, attribute_type_id and predicate elements
    # and detection of absent Knowledge Graph Edge predicate and attributes (despite 'nullable: true' model permission)
    strict_validation: Optional[bool] = None

    # validation normally reports empty Message query graph, knowledge graph and results as warnings.
    # This flag suppresses the reporting of such warnings (default: False)
    suppress_empty_data_warnings: Optional[bool] = None

    # Maximum number of knowledge graph edges validated from each TRAPI Response
    # returned from test edge query (default: 0 means 'validate all edges')
    max_kg_edges: int = 0

    # Maximum number of results validated from each TRAPI Response
    # returned from each test edge query (default: 0 means 'validate all results')
    max_results: int = 0

    #
    # We don't instantiate the full TRAPI models here but just use an open-ended dictionary which should have
    # query_graph, knowledge_graph and results JSON tag-values.  A full Query.Response is (now) expected here,
    # as described in: https://github.com/NCATSTranslator/ReasonerAPI/blob/master/docs/reference.md#response-.
    #
    response: Dict


@app.post("/validate")
async def validate(query: Query):

    if not query.response:
        raise HTTPException(status_code=400, detail="Empty input message?")

    trapi_version: Optional[str] = query.trapi_version
    print(f"Specified 'trapi_version' == {trapi_version}", file=stderr)

    biolink_version: Optional[str] = query.biolink_version
    print(f"Specified 'biolink_version' == {biolink_version}", file=stderr)

    target_provenance: Optional[TargetProvenance] = query.target_provenance
    print(f"Validation Context == {target_provenance}", file=stderr)

    strict_validation: bool = query.strict_validation if query.strict_validation else False
    print(f"Validation Context == {str(strict_validation)}", file=stderr)

    suppress_empty_data_warnings: bool = \
        query.suppress_empty_data_warnings if query.suppress_empty_data_warnings else False
    print(f"suppress Empty Data Warnings == {str(suppress_empty_data_warnings)}", file=stderr)

    max_kg_edges: int = query.max_kg_edges
    print(f"Specified 'kg_edges_sample_size' == {max_kg_edges}", file=stderr)

    max_results: int = query.max_results
    print(f"Specified 'results_sample_size' == {max_results}", file=stderr)

    validator: TRAPIResponseValidator = TRAPIResponseValidator(
        trapi_version=trapi_version,
        biolink_version=biolink_version,
        target_provenance=target_provenance.dict() if target_provenance is not None else None,
        strict_validation=strict_validation,
        suppress_empty_data_warnings=suppress_empty_data_warnings
    )
    validator.check_compliance_of_trapi_response(
        response=query.response,
        max_kg_edges=max_kg_edges,
        max_results=max_results
    )

    if not validator.has_messages():
        validator.report(code="info.compliant")

    return validator.to_dict()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
