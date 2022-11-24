# Reasoner Validator

[![Pyversions](https://img.shields.io/pypi/pyversions/reasoner-validator)](https://pypi.python.org/pypi/reasoner-validator)
[![pypi](https://github.com/NCATSTranslator/reasoner-validator/workflows/pypi/badge.svg)](https://pypi.org/project/reasoner-validator/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

This package provides software methods to Translator components (e.g. Knowledge Providers and Autonomous Relay Agents) using *any version* of the
[Translator Reasoner API (TRAPI)](https://github.com/NCATSTranslator/ReasonerAPI/blob/master/README.md) and the [Biolink Model](https://github.com/biolink/biolink-model/blob/master/README.md).

See [the full documentation](https://ncatstranslator.github.io/reasoner-validator/) and [the contributor guidelines](https://github.com/NCATSTranslator/reasoner-validator/blob/master/.github/CONTRIBUTING.md).

# Using the Package

## Installing the Module

The module may be installed directly from pypi.org.

```bash
pip install reasoner-validator
```

## Installing and working with the module locally from source

As of release 3.1.6, this project uses the [poetry dependency management](https://python-poetry.org) tool to orchestrate its installation and dependencies.

After [installing poetry](https://python-poetry.org/docs/#installation) and cloning the project, the poetry installation may be run:

```bash
git clone https://github.com/NCATSTranslator/reasoner-validator.git
cd reasoner-validator
poetry install
```

## Building the Documentation Locally

To build the documentation locally:

```bash
cd docs
make html
```

## Validation Run as a Web Service

The Reasoner Validator is available wrapped as a simple web service.  The service may be run directly or as a Docker container.

### API

The web service has a single POST endpoint `/validate` taking a simple JSON request body, as follows:

```json
{
  "trapi_version": "1.3.0",
  "biolink_version": "3.0.3",
  "sources": {
    "ara_source": "infores:aragorn",
    "kp_source": "infores:panther",
    "kp_source_type": "primary"
  },
  "strict_validation": true,
  "message": {...}
}
```

The request body consists of JSON data structure with two top level tag:

- An **optional** `trapi_version` tag can be given a value of the TRAPI version against which the message will be validated, expressed as a SemVer string (defaults to 'latest' if omitted; partial SemVer strings are resolved to their 'latest' minor and patch releases). 
- An **optional** `biolink_version` tag can be given a value of the Biolink Model version against which the message knowledge graph semantic contents will be validated, expressed as a SemVer string (defaults to 'latest' Biolink Model Toolkit supported version, if omitted). 
- An **optional** `sources` with an object dictionary (example shown) specifying the ARA and KP sources involved in the TRAPI call (specified by infores CURIE) and the expected KP provenance source type, i.e. 'primary' implies that the KP is tagged as a 'biolink:primary_knowledge_source'. Optional in that the root "sources" or any of the subsidiary tags may be omitted (default to None)
- An **optional** `strict_validation` flag (default: None or 'false'). If 'true' then follow strict validation rules, such as treating as 'error' states the use of `category`, `predicate` and `attribute_type_id` that are of type `abstract` or `mixin`  as errors. 
- A **mandatory** `message` tag should have as its value the complete TRAPI **Message** JSON data structure to be validated (see example below).

### Running the Web Service Directly

The service may be run directly as a Python module. The web services module may be directly run, as follows. 

```shell
python -m api.main
```

Note that [poetry automatically uses any existing virtual environment](https://python-poetry.org/docs/basic-usage/#using-your-virtual-environment), but you can otherwise also enter the one that is created by poetry by default:

```shell
poetry shell
# run your commands, e.g. the web service module
exit  # exit the poetry shell
```

Go to  http://localhost/docs to see the service documentation and to use the simple UI to input TRAPI messages for validation.

### Typical Output

As an example of the kind of output to expect, if one posts the following JSON message data to the **/validate** endpoint:

```json
{
  "trapi_version": "1.3.0",
  "biolink_version": "3.0.3",
  "message": {
    "query_graph": {
        "nodes": {
            "type-2 diabetes": {"ids": ["MONDO:0005148"]},
            "drug": {"categories": ["biolink:Drug"]}
        },
        "edges": {
            "treats": {"subject": "drug", "predicates": ["biolink:treats"], "object": "type-2 diabetes"}
        }
    },
    "knowledge_graph": {
        "nodes": {
            "MONDO:0005148": {"name": "type-2 diabetes"},
            "CHEBI:6801": {"name": "metformin", "categories": ["biolink:Drug"]}
        },
        "edges": {
            "df87ff82": {"subject": "CHEBI:6801", "predicate": "biolink:treats", "object": "MONDO:0005148"}
        }
    },
    "results": [
        {
            "node_bindings": {
                "type-2 diabetes": [{"id": "MONDO:0005148"}],
                "drug": [{"id": "CHEBI:6801"}]
            },
            "edge_bindings": {
                "treats": [{"id": "df87ff82"}]
            }
        }
    ]
  }
}
```

one should typically get a response body like the following JSON validation result back:

```json
{
  "trapi_version": "1.3.0",
  "biolink_version": "3.0.3",
  "report": [
    {
      "code": "warning.node.unmapped_prefix",
      "node_id": "CHEBI:6801",
      "categories": "['biolink:Drug']"
    },
    {
      "code": "error.node.missing_categories",
      "node_id": "MONDO:0005148"
    },
    {
      "code": "error.edge.attribute.missing"
    }
  ]
}
```

### Running the Web Service within Docker

The Reasoner Validator web service may be run inside a docker container, using Docker Compose.

First, from the root project directory, build the local docker container

```shell
docker-compose build
```

Then, run the service:

```shell
docker-compose up -d
```

Once again, go to  http://localhost/docs to see the service documentation.

To stop the service:

```shell
docker-compose down
```

Of course, the above docker-compose commands may be customized by the user to suit their needs. Note that the docker implementation assumes the use of uvicorn

## Change Log

Summary of earlier releases and current Change Log is [here](CHANGELOG.md).

## Code Limitations (implied Future Work?)

- Biolink Model release <= 2.4.8 versus 3.0.0 validation: the reasoner-validator uses the Biolink Model Toolkit. As it happens, the toolkit is not backwards compatible with at least one Biolink Model structural change from release 2.#.# to 3.#.#: the tagging of 'canonical' predicates. That is, the 0.8.10++ toolkit reports canonical <= 2.4.8 model predicates as 'non-canonical'.
- This release of the Reasoner Validator Web Service will detect TRAPI 1.0.* releases but doesn't strive to be completely backwards compatible with them (considering that that TRAPI 1.0.* is totally irrelevant now). 
- The web service validation doesn't do deep validation of the Results part of a TRAPI Message
- The validation is only run on the first 1000 nodes and 100 edges of graphs, to keep the validation time tractable (this risks not having complete coverage of the graph)
- Biolink Model toolkit is not (yet) cached so changing the model version during use will result in some latency in results
- The validator service doesn't (yet) deeply validate non-core node and edge slot contents of Message Knowledge Graphs
- The validator service doesn't (yet) attempt validation of Query Graph nodes and edges 'constraints' (e.g. `biolink:Association` etc. `domain` and `range` constraints)
- Query Graph node 'ids' are not validated except when an associated 'categories' parameter is provided for the given node. In general, [Query Graph Validation](https://github.com/NCATSTranslator/reasoner-validator/issues/14) could be elaborated.
- The system should leverage the [Reasoner Pydantic Models](https://github.com/NCATSTranslator/reasoner-validator/issues/15)

# Core Contributors

- Kudos to Patrick Wang, who created the original implementation of the Reasoner-Validator project while with CoVar (an entrepreneurial team contributing to the Biomedical Data Translator).
- Thanks to Kenneth Morton (CoVar) for his reviews of the latest code.
- The project is currently being extended and maintained by Richard Bruskiewich (Delphinai Corporation, on the SRI team contributing to Translator)
