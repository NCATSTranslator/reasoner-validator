import re
from typing import Optional

CURIE_PATTERN = re.compile(r"^[^ <()>:]*:[^/ :]+$")


def is_curie(s: str) -> bool:
    """
    Check if a given string is a CURIE.

    :param s: str, string to be validated as a CURIE
    :return: bool, whether or not the given string is a CURIE
    """
    # Method copied from kgx.prefix_manager.PrefixManager...
    if isinstance(s, str):
        m = CURIE_PATTERN.match(s)
        return bool(m)
    else:
        return False


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
