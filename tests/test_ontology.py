"""
Unit tests of the low level ontology and node normalization calling subsystem.
"""
from typing import Optional
import pytest

from reasoner_validator import post_query, NODE_NORMALIZER_SERVER
from reasoner_validator.biolink.ontology import (
    ONTOLOGY_KP_TRAPI_SERVER,
    get_parent_concept
)

pytest_plugins = ('pytest_asyncio',)


@pytest.mark.parametrize(
    "curie,category,result",
    [
        (   # Query 0 - chemical compounds are NOT in ontology hierarchy
            "CHEMBL.COMPOUND:CHEMBL2333026",
            "biolink:SmallMolecule",
            None
        ),
        (   # Query 1 - MONDO disease terms are in an ontology term hierarchy
            "MONDO:0011027",
            "biolink:Disease",
            "MONDO:0015967"
        )
    ]
)
@pytest.mark.asyncio
async def test_post_query_to_ontology(curie: str, category: str, result: Optional[str]):
    query = {
        "message": {
            "query_graph": {
                "nodes": {
                    "a": {
                        "ids": [curie]
                    },
                    "b": {
                        "categories": [category]
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
    response = post_query(url=ONTOLOGY_KP_TRAPI_SERVER, query=query, server="Post Ontology KP Query")
    assert response


@pytest.mark.parametrize(
    "curie,category",
    [
        # Query 0 - HGNC id
        ("HGNC:12791", "biolink:Gene"),

        # Query 1 - MONDO term
        ("MONDO:0011027", "biolink:Disease"),

        # Query 2 - HP term
        ("HP:0040068", "biolink:PhenotypicFeature")
    ]
)
@pytest.mark.asyncio
async def test_post_query_to_node_normalization(curie: str, category: str):
    params = {'curies': [curie]}
    result = post_query(url=NODE_NORMALIZER_SERVER, query=params, server="Node Normalizer")
    assert result
    assert curie in result
    assert "equivalent_identifiers" in result[curie]
    assert len(result[curie]["equivalent_identifiers"])
    assert category in result[curie]["type"]


@pytest.mark.parametrize(
    "curie,category,result",
    [
        (   # Query 0 - chemical compounds are NOT in an ontology hierarchy
            "CHEMBL.COMPOUND:CHEMBL2333026",
            "biolink:SmallMolecule",
            None
        ),
        (   # Query 1 - MONDO disease terms are in an ontology term hierarchy
            "MONDO:0011027",
            "biolink:Disease",
            "MONDO:0015967"
        ),
        (   # Query 2 - HP phenotype terms are in an ontology term hierarchy
            "HP:0040068",  # "Abnormality of limb bone"
            "biolink:PhenotypicFeature",
            "HP:0000924"  # Abnormality of the skeletal system
        )
    ]
)
def test_get_parent_concept(curie: str, category: str, result: Optional[str]):
    # Just use default Biolink Model release for this test
    assert get_parent_concept(curie=curie, category=category, biolink_version=None) == result