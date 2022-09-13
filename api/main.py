"""
FastAPI web service wrapper for TRAPI validator and Biolink Model compliance testing
"""
from typing import Optional, Dict
from sys import stderr
from pydantic import BaseModel

import uvicorn
from fastapi import FastAPI, HTTPException

from reasoner_validator.report import ValidationReporter
from reasoner_validator.trapi import TRAPIValidator
from reasoner_validator.versioning import latest
from reasoner_validator.biolink import check_biolink_model_compliance_of_trapi_response

app = FastAPI()


#
# We don't instantiate the full TRAPI models here but
# just use an open-ended dictionary which should have
# query_graph, knowledge_graph and results JSON tag-values
#
class Query(BaseModel):
    trapi_version: Optional[str] = latest.get(TRAPIValidator.DEFAULT_TRAPI_VERSION)

    # default: latest Biolink Model Toolkit supported version
    biolink_version: Optional[str] = None

    message: Dict


@app.post("/validate")
async def validate(query: Query):

    if not query.message:
        raise HTTPException(status_code=400, detail="Empty input message?")

    trapi_version = latest.get(query.trapi_version)
    print(f"trapi_version == {trapi_version}", file=stderr)

    biolink_version = query.biolink_version
    print(f"biolink_version == {biolink_version}", file=stderr)

    validator: ValidationReporter = check_biolink_model_compliance_of_trapi_response(
        message=query.message,
        trapi_version=trapi_version,
        biolink_version=biolink_version
    )

    if not validator.has_messages():
        validator.info(f"Biolink Model-compliant TRAPI Message!")

    return validator.to_dict()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
