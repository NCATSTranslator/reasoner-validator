from sys import stderr
from os.path import abspath, dirname, sep
from copy import deepcopy

from bmt import Toolkit

from reasoner_validator.trapi import (
    TRAPI_2_0_0_BETA2,
    LATEST_TRAPI_RELEASE,
    LATEST_TRAPI_MAJOR_MINOR_RELEASE,
    LATEST_TRAPI_MAJOR_MINOR_PATCH_RELEASE
)

TESTS_DIRECTORY = abspath(dirname(__file__))
print(f"Test Directory: {TESTS_DIRECTORY}", file=stderr)

LOCAL_SCHEMA_VERSION = "v1.5.0"
LOCAL_TRAPI_150_SCHEMA_FILEPATH = f"{TESTS_DIRECTORY}{sep}test_data{sep}trapi_schema_v1.5.0.yaml"
BROKEN_SCHEMA_FILEPATH = f"broken-{LOCAL_SCHEMA_VERSION}.yaml"

TRAPI_2_0_TEST_VERSIONS: list = ["2.0", TRAPI_2_0_0_BETA2]

LATEST_TEST_RELEASES: list = [
    "2",
    LATEST_TRAPI_MAJOR_MINOR_RELEASE,
    LATEST_TRAPI_MAJOR_MINOR_PATCH_RELEASE,
    LATEST_TRAPI_RELEASE
]

ALL_TEST_VERSIONS: list[str] = LATEST_TEST_RELEASES

LATEST_BIOLINK_MODEL_VERSION = Toolkit().get_model_version()

SIMPLE_SAMPLE_NODES = {
    "NCBIGene:29974": {
        "name": "APOBEC1 complementation factor",
        "categories": [
           "biolink:Gene"
        ],
        "attributes": []
    },
    "PUBCHEM.COMPOUND:597": {
        "name": "cytosine",
        "categories": [
            "biolink:SmallMolecule"
        ],
        "attributes": []
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
        ],
        "knowledge_level": "not_provided",
        "agent_type": "not_provided"
    }
}

SAMPLE_NODES_WITH_UNUSED_NODE = deepcopy(SIMPLE_SAMPLE_NODES)
SAMPLE_NODES_WITH_UNUSED_NODE["NCBITaxon:9606"] = {
    "name": "Homo sapiens",
    "categories": [
       "biolink:OrganismTaxon"
    ],
    "attributes": []
}

SAMPLE_EDGE_WITH_WITHOUT_ATTRIBUTES = {
    "edge_1": {
        "subject": "NCBIGene:29974",
        "predicate": "biolink:physically_interacts_with",
        "object": "PUBCHEM.COMPOUND:597",
        "attributes": [],
        "sources": [
            {
                "resource_id": "infores:molepro",
                "resource_role": "primary_knowledge_source"
            }
        ],
        "knowledge_level": "not_provided",
        "agent_type": "not_provided"
    }
}


# From TRAPI 2.0, message components cannot be nullable and
# for nodes, must include some minimum content, which is faked here
TRAPI_2_0_COMPLIANT_QUERY_TEMPLATE = {
    "message": {
        "knowledge_graph": {
            "nodes": {
                "OMIM:603903": {
                    "categories": ["biolink:Disease"],
                    "name": "Sickle Cell Disease"
                }
            }
        },
        "query_graph": {
            "nodes": {
                "n0": {
                    "ids": ["OMIM:603903"],
                    "categories": ["biolink:Disease"]
                }
            }
        },
        "results": [
            {
                "node_bindings": {
                    "n0": {
                        "ids": ["OMIM:603903"]
                    }
                }
            }
        ],
    },
    "log_level": None,
}
