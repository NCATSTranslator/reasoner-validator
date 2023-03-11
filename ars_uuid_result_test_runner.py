#!/usr/bin/env python
##################################################
# Thanks to Eric Deutsch (Expander Agent) for this
# validator of ARS UUID specified TRAPI Responses
##################################################

from typing import Dict, List, Optional

import requests
from requests.exceptions import JSONDecodeError
import json
import argparse

from bmt import Toolkit
from reasoner_validator import TRAPIResponseValidator
from reasoner_validator.biolink import get_biolink_model_toolkit


def main():

    # Parse command line options
    arg_parser = argparse.ArgumentParser(description='CLI validation of ARS UUID indexed TRAPI Responses')
    arg_parser.add_argument('--verbose', action='count', help='If set, print more information about ongoing processing')
    arg_parser.add_argument('--biolink_version', type=str, help='Biolink Version for validation (if omitted or None, defaults to the current default version of the Biolink Model Toolkit)')
    arg_parser.add_argument('response_id', type=str, nargs='*', help='ARS response UUID of a response to read and display')
    params = arg_parser.parse_args()

    # Query and print some rows from the reference tables
    if len(params.response_id) == 0 or len(params.response_id) > 1:
        print("Please specify a single ARS response UUID")
        return

    response_id = params.response_id[0]

    response_content = requests.get(
        'https://ars-dev.transltr.io/ars/api/messages/'+response_id, headers={'accept': 'application/json'}
    )
    status_code = response_content.status_code

    if status_code != 200:
        print("Cannot fetch from ARS a response corresponding to response_id="+str(response_id))
        return

    # Unpack the response content into a dict
    try:
        response_dict = response_content.json()
    except JSONDecodeError:
        print("Cannot decode ARS UUID "+str(response_id)+" to a Translator Response")
        return

    if 'fields' in response_dict and \
            'actor' in response_dict['fields'] and \
            str(response_dict['fields']['actor']) == '9':
        print("The supplied response id is a collection id. Please supply the UUID for a response")
        return

    if 'fields' in response_dict and 'data' in response_dict['fields']:
        envelope = response_dict['fields']['data']
        if envelope is None:
            envelope = {}
            return envelope

        # explicitly resolve the Biolink Model version to be used
        bmt: Toolkit = get_biolink_model_toolkit(biolink_version=params.biolink_version)
        resolved_biolink_version: str = bmt.get_model_version()
        if params.verbose:
            print(
                f"Validating ARS UUID '{str(response_id)}' output " +
                f"against Biolink Model version '{resolved_biolink_version}'")

        # Perform a validation on it
        validator = TRAPIResponseValidator(trapi_version="1.3.0", biolink_version=resolved_biolink_version)
        validator.check_compliance_of_trapi_response(envelope)
        messages: Dict[str, Dict[str, Optional[Dict[str, Optional[List[Dict[str, str]]]]]]] = validator.get_messages()

        if params.verbose:
            print(json.dumps(messages, sort_keys=True, indent=2))

    return


if __name__ == "__main__":
    main()
