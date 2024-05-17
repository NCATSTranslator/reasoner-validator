"""
Unit tests of the low level ontology and node normalization calling subsystem.
"""
from typing import Optional
import pytest

from reasoner_validator.utils.http import post_query
from reasoner_validator.biolink.ontology import (
    ONTOLOGY_KP_TRAPI_SERVER,
    NODE_NORMALIZER_SERVER
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
    j = {'curies': [curie]}
    result = post_query(url=NODE_NORMALIZER_SERVER, query=j, server="Post Node Normalizer Query")
    assert result
    assert curie in result
    assert "equivalent_identifiers" in result[curie]
    assert len(result[curie]["equivalent_identifiers"])
    assert category in result[curie]["type"]
