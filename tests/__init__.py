from typing import Tuple, List
from sys import stderr
from os.path import abspath, dirname, sep
from copy import deepcopy

from reasoner_validator.trapi import TRAPI_1_3_0, LATEST_TRAPI_RELEASE, LATEST_TRAPI_MAJOR_RELEASE

TESTS_DIRECTORY = abspath(dirname(__file__))
print(f"Test Directory: {TESTS_DIRECTORY}", file=stderr)

PATCHED_SCHEMA_VERSION = "v1.4.0-beta5"
PATCHED_140_SCHEMA_FILEPATH = f"{TESTS_DIRECTORY}{sep}test_data{sep}patched_trapi_schema_{PATCHED_SCHEMA_VERSION}.yaml"
BROKEN_SCHEMA_FILEPATH = f"broken-{PATCHED_SCHEMA_VERSION}.yaml"

PRE_1_4_0_TEST_VERSIONS: List = ["1.2", "1.2.0", "1.3", TRAPI_1_3_0]
LATEST_TEST_RELEASES: List = ["1", LATEST_TRAPI_MAJOR_RELEASE, LATEST_TRAPI_RELEASE]

ALL_TEST_VERSIONS: List[str] = PRE_1_4_0_TEST_VERSIONS + LATEST_TEST_RELEASES


SIMPLE_SAMPLE_NODES = {
    "NCBIGene:29974": {
        "categories": [
           "biolink:Gene"
        ]
    },
    "PUBCHEM.COMPOUND:597": {
        "name": "cytosine",
        "categories": [
            "biolink:SmallMolecule"
        ]
    }
}
SAMPLE_NODES_WITH_ATTRIBUTES = deepcopy(SIMPLE_SAMPLE_NODES)
SAMPLE_NODES_WITH_ATTRIBUTES["PUBCHEM.COMPOUND:597"]["attributes"] = [
    {
        "attribute_source": "infores:chembl",
        "attribute_type_id": "biolink:highest_FDA_approval_status",
        "attributes": [],
        "original_attribute_name": "max_phase",
        "value": "FDA Clinical Research Phase 2",
        "value_type_id": "biolink:FDA_approval_status_enum"
    }
]

# complete edge dereferencing SAMPLE_NODES_WITH_ATTRIBUTES
SAMPLE_EDGE_WITH_ATTRIBUTES_AND_SOURCES = {
    "edge_1": {
        "subject": "NCBIGene:29974",
        "predicate": "biolink:physically_interacts_with",
        "object": "PUBCHEM.COMPOUND:597",
        "attributes": [
            {
                "attribute_source": "infores:hmdb",
                "attribute_type_id": "biolink:stoichiometry",
                "value": 2,
                "attributes": [],
            }
        ],
        "sources": [
            {
                "resource_id": "infores:molepro",
                "resource_role": "primary_knowledge_source"
            }
        ]
    }
}

SAMPLE_NODES_WITH_UNUSED_NODE = deepcopy(SIMPLE_SAMPLE_NODES)
SAMPLE_NODES_WITH_UNUSED_NODE["unused_node"] = {
    "categories": [
       "biolink:NamedThing"
    ]
}
