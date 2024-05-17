from sys import stderr
from typing import Dict

import requests


def post_query(url: str, query: Dict, params=None, server: str = ""):
    """
    Post a JSON query to the specified URL and return the JSON response.

    :param url, str URL target for HTTP POST
    :param query, JSON query for posting
    :param params, optional parameters
    :param server, str human-readable name of server called (for error message reports)
    """
    if params is None:
        response = requests.post(url, json=query)
    else:
        response = requests.post(url, json=query, params=params)
    if not response.status_code == 200:
        print(
            f"Server {server} at '\nUrl: '{url}', Query: '{query}' with " +
            f"parameters '{params}' returned HTTP error code: '{response.status_code}'",
            file=stderr
        )
        return {}
    return response.json()
