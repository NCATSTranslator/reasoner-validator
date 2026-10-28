"""
Validation of Infores values against the InfoRes catalog at
https://github.com/biolink/information-resource-registry/blob/main/infores_catalog.yaml
"""
from typing import Set
from functools import lru_cache

import requests
import yaml

import logging
logger = logging.getLogger(__name__)

INFORES_CATALOG_URL = \
    "https://raw.githubusercontent.com/biolink/information-resource-registry/main/infores_catalog.yaml"

DEFAULT_INFORES_CATALOG_TIMEOUT = 60  # seconds


@lru_cache(maxsize=1)
def get_infores_catalog_ids() -> Set[str]:
    """
    Retrieves (once, then cached) the set of 'id' values of the
    'information_resources' records of the InfoRes catalog.

    :return: Set[str], of InfoRes CURIEs (e.g. 'infores:aact')
    :raises RuntimeError: if the catalog cannot be retrieved or parsed
    """
    try:
        response = requests.get(INFORES_CATALOG_URL, timeout=DEFAULT_INFORES_CATALOG_TIMEOUT)
        response.raise_for_status()
        catalog = yaml.safe_load(response.text)
    except (requests.RequestException, yaml.YAMLError) as e:
        # an exception is not cached by lru_cache, so a later call will retry
        raise RuntimeError(f"Could not load the InfoRes catalog from '{INFORES_CATALOG_URL}': {e}") from e

    if not isinstance(catalog, dict):
        raise RuntimeError(f"InfoRes catalog from '{INFORES_CATALOG_URL}' has an unexpected format")

    return {
        record["id"]
        for record in catalog.get("information_resources") or []
        if isinstance(record, dict) and record.get("id")
    }


def is_infores(identifier: str) -> bool:
    """
    Predicate testing whether a given identifier is an InfoRes CURIE registered
    (as an 'id' value of an 'information_resources' record) in the InfoRes catalog.

    :param identifier: str, candidate InfoRes CURIE (e.g. 'infores:aact')
    :return: bool, True if the identifier is registered in the InfoRes catalog
    :raises RuntimeError: if the InfoRes catalog cannot be retrieved
    """
    if not identifier:
        return False
    return identifier.strip() in get_infores_catalog_ids()
