"""
Ontology KP interface
"""
from typing import Optional, List
from functools import lru_cache

from reasoner_validator.biolink import get_biolink_model_toolkit
from reasoner_validator import post_query, NODE_NORMALIZER_SERVER

ONTOLOGY_KP_TRAPI_SERVER = "https://automat.renci.org/ubergraph/query"

CACHE_SIZE = 1024


def convert_to_preferred(curie, allowed_list):
    """
    :param curie
    :param allowed_list
    """
    query = {'curies': [curie]}
    result = post_query(url=NODE_NORMALIZER_SERVER, query=query, server="Node Normalizer")
    if not (result and curie in result and result[curie] and 'equivalent_identifiers' in result[curie]):
        return None
    new_ids = [v['identifier'] for v in result[curie]['equivalent_identifiers']]
    for nid in new_ids:
        if nid.split(':')[0] in allowed_list:
            return nid
    return None


def get_ontology_ancestors(curie, btype) -> List[str]:
    """
    :param curie:
    :param btype:
    """
    query = {
        "message": {
            "query_graph": {
                "nodes": {
                    "a": {
                        "ids": [curie]
                    },
                    "b": {
                        "categories": [btype]
                    }
                },
                "edges": {
                    "ab": {
                        "subject": "a",
                        "object": "b",
                        "predicates": ["biolink:subclass_of"]
                    }
                }
            }
        }
    }
    response = post_query(url=ONTOLOGY_KP_TRAPI_SERVER, query=query, server="Ontology KP")
    ancestors = []
    if response:
        original_prefix = curie.split(':')[0]
        for result in response['message']['results']:
            parent_id = result['node_bindings']['b'][0]['id']
            if parent_id == curie:
                # everything is a subclass of itself
                continue
            if not parent_id.startswith(original_prefix):
                # Don't give me UPHENO:000001 if I asked for a parent of HP:000012312
                continue
            # good enough
            ancestors.append(parent_id)
    else:
        print("### No response from the Ontology server: it may be offline?")

    return ancestors


# **Deprecated** strategy here of looking for the "closest" parent since within a
# Directed Acyclic Graph (DAG) structured ontology, a given term may have multiple parents.
def get_ontology_parents(curie, category):
    """
    :param curie, str CURIE identifier
    :param category, Biolink category of the CURIE
    :return List of ontology term ancestors of the curie
    """
    # Here's a bunch of ancestors
    ancestors = get_ontology_ancestors(curie, category)

    if not ancestors:
        return None

    # Now, to get the one closest to the input, we see
    # how many ancestors each ancestor has.  Largest number == lowest down
    ancestor_count = []
    for anc in ancestors:
        second_ancestors = get_ontology_ancestors(anc, category)
        if not second_ancestors:
            continue
        ancestor_count.append((len(second_ancestors), anc))
    if ancestor_count:
        ancestor_count.sort()
        return ancestor_count[-1][1]
    else:
        return None


@lru_cache(CACHE_SIZE)
def get_parent_concepts(curie, category, biolink_version) -> Optional[List[str]]:
    """
    Given a CURIE of a concept and its category,
    attempt to return the parent concept if available
    within an ontology modelled by specified Biolink Model release.

    :param curie: CURIE of a concept instance
    :param category: Biolink Category of the concept instance
    :param biolink_version: Biolink Model version to use in validation (SemVer string specification)
    :return List of parent concept identifiers, if the input CURIE lies within an ontology (DAG) hierarchy
    """
    tk = get_biolink_model_toolkit(biolink_version=biolink_version)
    if not tk.is_category(category):
        assert False, f"'{category}' is not a Biolink Model Category!"

    # Not every Biolink Category has a prefix namespace with ontological hierarchy.
    # We replace the previous hard coded namespace list with retrieval of id_prefixes
    # registered for the given concept category within the Biolink Model.
    # preferred_prefixes = {'CHEBI', 'HP', 'MONDO', 'UBERON', 'CL', 'EFO', 'NCIT'}
    preferred_prefixes = tk.get_element(category).id_prefixes

    # Normalize the input curie identifier
    input_prefix = curie.split(':')[0]
    if input_prefix in preferred_prefixes:
        query_entity = curie
    else:
        query_entity = convert_to_preferred(curie, preferred_prefixes)
    if query_entity is None:
        return None

    # A "query_entity" within a DAG ontology hierarchy
    # may return a List of zero or more general ontology terms
    ancestors: List[str] = get_ontology_ancestors(query_entity, category)
    if not ancestors:
        return None

    # Sanity check for mixed ontology namespaces, return
    # identifiers only from the preferred input namespace?
    ancestors = [
        convert_to_preferred(term, [input_prefix])
        for term in ancestors
        if term.split(':')[0] == input_prefix
    ]

    return ancestors
