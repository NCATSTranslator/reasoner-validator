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

ARS_HOSTS = [
    'ars-prod.transltr.io',
    'ars.test.transltr.io',
    'ars.ci.transltr.io',
    'ars-dev.transltr.io',
    'ars.transltr.io'
]


def main():

    # Parse command line options
    arg_parser = argparse.ArgumentParser(description='CLI validation of ARS UUID indexed TRAPI Responses')
    arg_parser.add_argument(
        '--verbose', action='count',
        help='If set, show detailed information about ongoing processing, including validation results ' +
             '(Note that even if this flag is not given, non-empty validation results can still be ' +
             'selectively shown at end of script execution).'
    )
    arg_parser.add_argument(
        '--json', action='count',
        help='If set, dump any messages in JSON format (otherwise, dump messages in human readable format).'
    )
    arg_parser.add_argument(
        '--biolink_version', type=str,
        help='Biolink Version for validation (if omitted or None, ' +
             'defaults to the current default version of the Biolink Model Toolkit)'
    )
    arg_parser.add_argument(
        'response_id', type=str, nargs='*', help='ARS response UUID of a response to read and display'
    )
    params = arg_parser.parse_args()

    # Query and print some rows from the reference tables
    if len(params.response_id) == 0 or len(params.response_id) > 1:
        print("Please specify a single ARS response UUID")
        return

    response_id = params.response_id[0]

    response_content: Optional = None
    status_code: int = 404

    if params.verbose:
        print(f"Trying to retrieve ARS Response UUID '{response_id}'...")

    for ars_host in ARS_HOSTS:
        if params.verbose:
            print(f"\n...from {ars_host}", end=None)
        try:
            response_content = requests.get(
                f"https://{ars_host}/ars/api/messages/"+response_id,
                headers={'accept': 'application/json'}
            )
            if response_content:
                status_code = response_content.status_code
                if status_code == 200:
                    print(f"...Result returned from '{ars_host}'!")
                    break
            else:
                status_code = 404

        except Exception as e:
            print(f"Remote host {ars_host} unavailable: Connection attempt to {ars_host} triggered an exception: {e}")
            response_content = None
            status_code = 404
            continue

    if status_code != 200:
        print(f"Cannot fetch from ARS a TRAPI Response corresponding to UUID '{str(response_id)}'... Exiting.")
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

        def prompt_user(msg: str):
            text = input(f"{msg} (Type 'Y' or 'Yes' to show): ")
            text = text.upper()
            if text == "YES" or text == "Y":
                return True
            else:
                return False

        show_messages: bool = False
        if validator.has_errors() or validator.has_warnings():
            show_messages = prompt_user("Validation errors and/or warnings were reported")
        elif validator.has_information():
            show_messages = prompt_user("No validation errors or warnings, but some information was reported")

        if show_messages or params.verbose:
            if params.json:
                print(json.dumps(messages, sort_keys=True, indent=2))
            else:
                validator.dump()


if __name__ == "__main__":
    main()
