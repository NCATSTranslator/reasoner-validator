"""
General SRI support methods are placed here, e.g. Node Normalizer service access?
"""
import logging
import re
from functools import lru_cache
from json import JSONDecodeError
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Endpoint for the Translator Normalizer service
NODE_NORMALIZER_URL = 'https://nodenormalization-sri.renci.org/get_normalized_nodes'
CURIE_PATTERN = re.compile(r"^[^ <()>:]*:[^/ :]+$")


def is_curie(s: str) -> bool:
    """
    Check if a given string is a CURIE.

    :param s: str, string to be validated as a CURIE
    :return: bool, whether the given string is a CURIE
    """
    # Method copied from kgx.prefix_manager.PrefixManager...
    if isinstance(s, str):
        m = CURIE_PATTERN.match(s)
        return bool(m)
    else:
        return False


# TODO: not sure to what maxsize for LRU cache but saving 1K identifiers for now
@lru_cache(maxsize=1024)
def get_aliases(identifier: str) -> List[str]:
    """
    Get clique of related identifiers from the Node Normalizer
    """
    if not identifier:
        raise RuntimeError("get_aliases(): empty input identifier?")

    aliases: Optional[List[str]] = None
    #
    # TODO: maybe check for IRI's here and attempt to translate
    #       (Q: now do we access the prefix map from BMT to do this?)
    # if PrefixManager.is_iri(identifier):
    #     identifier = PrefixManager.contract(identifier)

    # We won't raise a RuntimeError for other various
    # erroneous runtime conditions but simply report warnings
    if not is_curie(identifier):
        logging.warning(f"get_aliases(): identifier '{identifier}' is not a CURIE thus cannot resolve its aliases?")
    else:
        # Use the Translator Node Normalizer service to resolve the identifier clique
        response = requests.get(NODE_NORMALIZER_URL, params={'curie': identifier})

        result: Optional[Dict] = None
        if response.status_code != 200:
            logging.warning(
                f"get_aliases(): unsuccessful Node Normalizer HTTP call, status code: {response.status_code}"
            )
        else:
            try:
                result = response.json()
            except (JSONDecodeError, UnicodeDecodeError) as je:
                logging.warning(f"get_aliases(): Node Normalizer response JSON could not be decoded: {str(je)}?")

        if result:
            if identifier not in result.keys():
                logging.warning(f"get_aliases(): Node Normalizer didn't return the identifier '{identifier}' clique?")
            else:
                clique = result[identifier]
                if clique:
                    if "id" in clique.keys():
                        # TODO: Don't need the canonical identifier for method
                        #       but when you do, this is how you'll get it?
                        # clique_id = clique["id"]
                        # preferred_curie = preferred_id["identifier"]
                        # preferred_name = preferred_id["label"]
                        if "equivalent_identifiers" in clique.keys():
                            aliases = [entry["identifier"] for entry in clique["equivalent_identifiers"]]
                            #
                            # Decided that it was a bad idea to remove
                            # the original identifier from the aliases...
                            # aliases.remove(identifier)
                            #
                            # print(dumps(aliases, indent=2))
                        else:
                            logging.warning(
                                f"get_aliases(): missing the 'equivalent identifiers' for the '{identifier}' clique?"
                            )
                    else:
                        logging.warning(
                            f"get_aliases(): missing the preferred 'id' for the '{identifier}' clique?"
                        )
                else:
                    logging.warning(
                        f"get_aliases(): '{identifier}' is a singleton in its clique thus has no aliases..."
                    )

    if not aliases:
        # Logging various errors but always
        # return the identifier as its own alias
        aliases = [identifier]

    return aliases


def get_reference(curie: str) -> Optional[str]:
    """
    Get the object_id reference of a given CURIE.

    Parameters
    ----------
    curie: str
        The CURIE

    Returns
    -------
    Optional[str]
        The reference of a CURIE

    """
    # Method adapted from kgx.prefix_manager.PrefixManager...
    reference: Optional[str] = None
    if is_curie(curie):
        reference = curie.split(":", 1)[1]
    return reference
