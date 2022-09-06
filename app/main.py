"""
FastAPI web service wrapper for TRAPI validator and Biolink Model compliance testing
"""
from typing import Optional, Dict
from pydantic import BaseModel

import uvicorn
from fastapi import FastAPI, HTTPException

from reasoner_validator.report import ValidationReporter
from reasoner_validator.trapi import TRAPIValidator
from reasoner_validator.util import latest
from reasoner_validator.biolink import (
    check_biolink_model_compliance_of_query_graph,
    check_biolink_model_compliance_of_knowledge_graph, BiolinkValidator
)

app = FastAPI()


#
# We don't instantiate the full TRAPI models here but
# just use an open-ended dictionary which should have
# query_graph, knowledge_graph and results JSON tag-values
#
class Query(BaseModel):
    trapi_version: Optional[str] = TRAPIValidator.DEFAULT_TRAPI_VERSION

    # default: latest Biolink Model Toolkit supported version
    biolink_version: Optional[str] = None

    message: Dict


@app.post("/validate")
async def validate(query: Query):

    if not query.message:
        raise HTTPException(status_code=400, detail="Empty input message?")

    trapi_validator = TRAPIValidator(trapi_version=latest.get(query.trapi_version))
    biolink_version = query.biolink_version

    validator: ValidationReporter = ValidationReporter()
    
    trapi_validator.is_valid_trapi_query(instance={"message": query.message})
    if trapi_validator.has_messages():
        validator.merge(trapi_validator)

    # Verify that the response has a Query Graph
    if not query.message['query_graph']:
        # An empty Query Graph is Not considered an absolute error, but we issue a warning
        validator.warning(f"Empty TRAPI Message Query Graph?")
    else:
        # Verify that the provided TRAPI Message Query Graph is compliant to the current Biolink Model release
        biolink_validator: BiolinkValidator  = \
            check_biolink_model_compliance_of_query_graph(
                graph=query.message['query_graph'],
                biolink_version=biolink_version
            )
        if biolink_validator.has_messages():
            validator.merge(biolink_validator)

    # Verify that the response had a non-empty Knowledge Graph
    if not query.message['knowledge_graph']:
        # An empty Knowledge Graph is Not considered an absolute error, but we issue a warning
        validator.warning(f"TRAPI Message Warning: empty TRAPI Message Knowledge Graph?")
    else:
        # Verify that the provided TRAPI Message Knowledge Graph is compliant to the current Biolink Model release
        biolink_validator: BiolinkValidator = \
            check_biolink_model_compliance_of_knowledge_graph(
                graph=query.message['knowledge_graph'],
                biolink_version=biolink_version
            )
        if biolink_validator.has_messages():
            validator.merge(biolink_validator)

    # Verify that the response had some Result
    if not query.message['results']:
        # An empty Result is Not considered an absolute error, but we issue a warning
        validator.warning(f"TRAPI Message Warning: empty TRAPI Message Result?")

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

    if not validator:
        validator.info(f"Biolink Model-compliant TRAPI Message!")

    return validator.to_dict()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
