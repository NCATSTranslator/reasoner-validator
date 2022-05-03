"""
FastAPI wrapper for TRAPI validator
"""
from typing import Dict
import uvicorn
from fastapi import FastAPI, HTTPException
from pprint import PrettyPrinter
import logging
from app.util import Query, is_valid_trapi
from reasoner_validator.util import latest

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

pp = PrettyPrinter(indent=4)

app = FastAPI()


@app.post("/validate")
async def validate(query: Query):

    trapi_version = query.version
    trapi_version = latest.get(trapi_version)

    if not query.message:
        raise HTTPException(status_code=400, detail="Empty input message?")

    message: Dict = {"message": query.message}

    # print(f"TRAPI Message:\n\t{pp.pformat(message)}\n", file=sys.stderr)

    result = is_valid_trapi(instance=message, trapi_version=trapi_version)
    return {"trapi_version": trapi_version, "result": result}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
