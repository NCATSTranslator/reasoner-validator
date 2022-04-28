"""
FastAPI web service wrapper for TRAPI validator and Biolink Model compliance testing
"""
from typing import Optional, Dict, List
from urllib.error import HTTPError
from pydantic import BaseModel

import uvicorn
from fastapi import FastAPI, HTTPException

from reasoner_validator import DEFAULT_TRAPI_VERSION, is_valid_trapi_query
from reasoner_validator.util import latest
from biolink import (
    set_biolink_model_toolkit,
    check_biolink_model_compliance_of_knowledge_graph
)

app = FastAPI()


#
# We don't instantiate the full TRAPI models here but
# just use an open-ended dictionary which should have
# query_graph, knowledge_graph and results JSON tag-values
#
class Query(BaseModel):
    trapi_version: Optional[str] = DEFAULT_TRAPI_VERSION

    # default: latest Biolink Model Toolkit supported version
    biolink_version: Optional[str] = None

    message: Dict


@app.post("/validate")
async def validate(query: Query):

    if not query.message:
        raise HTTPException(status_code=400, detail="Empty input message?")

    trapi_version = latest.get(query.trapi_version)
    try:
        set_biolink_model_toolkit(biolink_version=query.biolink_version)
    except TypeError as te:
        return {"validation": str(te)}
    except HTTPError:
        return {"validation": f"Unknown Biolink Model version: '{query.biolink_version}'?"}

    results: List[str] = list()
    
    error = is_valid_trapi_query(instance={"message": query.message}, trapi_version=trapi_version)
    if error:
        results.append(error)

    # Verify that the response has a Query Graph
    if not len(query.message['query_graph']):
        results.append(f"Incomplete TRAPI Message: empty TRAPI Message Query Graph?")

    # Verify that the response had some Result
    if not len(query.message['results']):
        results.append(f"Incomplete TRAPI Message: empty TRAPI Message Result?")

    # Verify that the response had a non-empty Knowledge Graph
    if not len(query.message['knowledge_graph']) > 0:
        results.append(f"Incomplete TRAPI Message: empty TRAPI Message Knowledge Graph?")

    # Verify that the TRAPI message associated Knowledge Graph is compliant to the current Biolink Model release
    biolink_model_version, errors = \
        check_biolink_model_compliance_of_knowledge_graph(graph=query.message['knowledge_graph'])
    if errors:
        results.extend(errors)

    # Finally, check that the Results contained the object of the query -
    # TODO: Not sure about this part of the TRAPI validation yet
    # object_ids = [r['node_bindings'][output_node_binding][0]['id'] for r in message['results']]
    # if case[output_element] not in object_ids:
    #     # The 'get_aliases' method uses the Translator NodeNormalizer to check if any of
    #     # the aliases of the case[output_element] identifier are in the object_ids list
    #     output_aliases = get_aliases(case[output_element])
    #     if not any([alias == object_id for alias in output_aliases for object_id in object_ids]):
    #         assert False, f"{err_msg_prefix} neither the input id '{case[output_element]}' " +\
    #                       f"nor resolved aliases [{','.join(output_aliases)}] were returned in the " +\
    #                       f"Result object IDs {pp.pformat(object_ids)} for node '{output_node_binding}' binding?"

    if not results:
        results.append("Valid TRAPI Message")

    return {
        "trapi_version": trapi_version,
        "biolink_version": biolink_model_version,
        "validation": results
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
