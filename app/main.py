"""
FastAPI wrapper for TRAPI validator
"""
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

from app.util import is_valid_trapi
from reasoner_validator.util import latest

# Default is actually specifically 1.2.0 as of April 2022,
# but the Reasoner validator should discern this
DEFAULT_TRAPI_VERSION = "1"


class TrapiMessage(BaseModel):
    contents: str                  # Candidate TRAPI message, uploaded as a string
    version: Optional[str] = None  # target TRAPI version, defaults to 'latest'


app = FastAPI()


@app.post("/validate/")
async def create_item(trapi_message: TrapiMessage):

    trapi_version = trapi_message.version if trapi_message.version else DEFAULT_TRAPI_VERSION
    trapi_version = latest.get(trapi_version)

    if is_valid_trapi(instance=trapi_message.contents, trapi_version=trapi_version):
        result = "successful"
    else:
        result = "invalid"

    return result
