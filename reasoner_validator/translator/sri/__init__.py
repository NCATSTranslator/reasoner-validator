"""
General SRI support methods are placed here, e.g. Node Normalizer service access?
"""
from typing import Dict, List

import requests
from functools import lru_cache

from json import JSONDecodeError

import logging

from kgx.prefix_manager import PrefixManager

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

# Endpoint for the Translator Normalizer service
NODE_NORMALIZER_URL = 'https://nodenormalization-sri.renci.org/get_normalized_nodes'


# TODO: not sure to what maxsize for LRU cache
#       should be set so we just take the default
@lru_cache()
def get_aliases(identifier: str):
    """
    Get clique of related identifiers from the Node Normalizer
    """
    if not identifier:
        raise RuntimeError("get_aliases(): empty input identifier?")

    #
    # TODO: maybe check for IRI's here and attempt to translate
    #       (Q: now do we access the prefix map from BMT to do this?)
    # if PrefixManager.is_iri(identifier):
    #     identifier = PrefixManager.contract(identifier)

    # We won't raise a RuntimeError for other various
    # erroneous runtime conditions but simply report warnings
    if not PrefixManager.is_curie(identifier):

        logging.warning(f"get_aliases(): identifier '{identifier}' is not a CURIE thus cannot resolve its aliases?")
        return list()

    # Use the Translator Node Normalizer service to resolve the identifier clique
    response = requests.get(NODE_NORMALIZER_URL, params={'curie': identifier})

    if response.status_code != 200:
        logging.warning(f"get_aliases(): unsuccessful Node Normalizer HTTP call, status code: {response.status_code}")
        return list()
    else:
        try:
            result: Dict = response.json()
        except (JSONDecodeError, UnicodeDecodeError) as je:
            logging.warning(f"get_aliases(): Node Normalizer response JSON could not be decoded: {str(je)}?")
            return list()

    if result and identifier not in result.keys():
        logging.warning(f"get_aliases(): Node Normalizer didn't return the identifier '{identifier}' clique?")
        return list()

    clique = result[identifier]

    aliases: List[str] = list()
    if clique:
        if "id" in clique.keys():
            # TODO: Don't need the canonical identifier for method
            #       but when you do, this is how you'll get it?
            # clique_id = clique["id"]
            # preferred_curie = preferred_id["identifier"]
            # preferred_name = preferred_id["label"]
            if "equivalent_identifiers" in clique.keys():
                aliases: List[str] = [entry["identifier"] for entry in clique["equivalent_identifiers"]]
                aliases.remove(identifier)
                # print(dumps(aliases, indent=2))
            else:
                logging.warning(f"get_aliases(): missing the 'equivalent identifiers' for the '{identifier}' clique?")
        else:
            logging.warning(f"get_aliases(): missing the preferred 'id' for the '{identifier}' clique?")
    else:
        logging.warning(f"get_aliases(): '{identifier}' is a singleton in its clique thus has no aliases...")

    return aliases
