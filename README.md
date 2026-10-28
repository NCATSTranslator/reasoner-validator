# Reasoner Validator

[![Pyversions](https://img.shields.io/pypi/pyversions/reasoner-validator)](https://pypi.python.org/pypi/reasoner-validator)
[![Publish Python Package](https://github.com/NCATSTranslator/reasoner-validator/actions/workflows/pypi_publish.yml/badge.svg)](https://pypi.org/project/reasoner-validator/)
[![Sphinx Documentation](https://github.com/NCATSTranslator/reasoner-validator/actions/workflows/doc_pages.yml/badge.svg)](https://github.com/NCATSTranslator/reasoner-validator/actions/workflows/doc_pages.yml)
[![Run tests](https://github.com/NCATSTranslator/reasoner-validator/actions/workflows/test.yml/badge.svg)](https://github.com/NCATSTranslator/reasoner-validator/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

This package provides software methods to validate Translator components (e.g. Knowledge Providers and Autonomous Relay Agents) using release 2.0 of the
[Translator Reasoner API (TRAPI)](https://github.com/NCATSTranslator/ReasonerAPI/blob/master/README.md) and the [Biolink Model](https://github.com/biolink/biolink-model/blob/master/README.md).

See [the full documentation](https://ncatstranslator.github.io/reasoner-validator/) and [the contributor guidelines](https://github.com/NCATSTranslator/reasoner-validator/blob/master/.github/CONTRIBUTING.md).

# Using the Package

## Python Dependency

The Reasoner Validator now requires Python release 3.10 to 3.12 (library dependencies now force this); however, 3.12 is recommended.

## Installing the Module

The module may be installed directly from pypi.org using (Python 3) `pip` or `pip3`, namely:

```bash
pip install reasoner-validator
```

## Installing and working with the module locally from source

As of release 3.1.6, this project uses the [poetry dependency management](https://python-poetry.org) tool to orchestrate its installation and dependencies.

After [installing poetry](https://python-poetry.org/docs/#installation) and cloning the project, the poetry installation may be run (within the available poetry shell):

```bash
git clone https://github.com/NCATSTranslator/reasoner-validator.git
cd reasoner-validator
pyenv local 3.12  # or whatever version you want to use, remember to use `pyenv install` to install it first
poetry env use 3.12  # or the version you chose above
poetry env activate
poetry install
```

Note that the **`poetry env`** can be set to Python 3.10 through 3.12 at the present time (3.12 is recommended).

This installation also installs testing dependencies (in the poetry 'dev' group in the pyproject.toml) and documentation dependencies (in the corresponding poetry 'docs' group). If you don't want the overhead of these dependencies, then the installation of these poetry group dependencies may be excluded:

```bash
poetry install --without dev,docs
```

If you plan to run the web service API (see below), then install it with the optional web group:

```bash
poetry install --with web
```

## Running Validation against an ARS UUID Result(*) or using a Local TRAPI Request Query

A local script **`trapi_validator.py`** is available to run TRAPI Response validation against either a PK (UUID)
indexed query result of the Biomedical Knowledge Translator "Autonomous Relay System" (ARS), a local JSON Response
text file or a locally triggered _ad hoc_ query Request against a directly specified TRAPI endpoint.

Note that it is best run within a **`poetry shell`** created by **`poetry install`**.

For script usage, type:

```bash
./trapi_validator.py --help
```

(*) Thank you to Eric Deutsch for the prototype code for this script, and Vlado Dancik for suggestions for improvement.

## Running tests

Run the available unit tests with a coverage report:

```bash
poetry run pytest --cov
```

Note that [poetry automatically uses any existing virtual environment](https://python-poetry.org/docs/basic-usage/#using-your-virtual-environment), but you can otherwise also enter the one that is created by poetry by default:

```shell
poetry shell
# run your commands, e.g. the web service module
exit  # exit the poetry shell
```

The use of the Poetry shell command allows for running of the tests without the `poetry run` prefix. We will continue in this manner.

```bash
% poetry shell
(reasoner-validator-py3.12) % pytest --cov
```

Run the tests with a detailed coverage report in a HTML page:

```bash
pytest --cov --cov-report html
```

Serve the report on http://localhost:3000:

```bash
python -m http.server 3000 --directory ./htmlcov
```

## Building the Documentation Locally

All paths here are relative to the root project directory. The validation codes MarkDown file should first be regenerated if needed (i.e. if the **`codes.yaml`** was revised):

```bash
cd reasoner_validator
python ./validation_codes.py
```

Then build the documentation locally (note: a local unix-like make utility is required and all python dependencies must be installed in a local poetry shell):

```bash
cd ../docs
make html
```

The resulting **index.html** and related pages describing the programmatic API are now available for viewing within the docs subfolder __build/html_.  

## Validation Run as a Web Service

The Reasoner Validator is available wrapped as a simple web service.  The service may be run directly or as a Docker container.

### API

The web service has a single POST endpoint `/validate` taking a simple JSON request body, as follows:

```json
{
  "trapi_version": "2.0.0",
  "biolink_version": "4.4.5",
  "target_provenance": {
    "ara_source": "infores:aragorn",
    "kp_source": "infores:panther",
    "kp_source_type": "primary"
  },
  "strict_validation": true,
  "response": "{<some full JSON object of a TRAPI query Response...>}"
}
```

The request body consists of JSON data structure with two top level tag:

- An **optional** `trapi_version` tag can be given a value of the TRAPI version against which the message will be validated, expressed as a SemVer string (defaults to 'latest' if omitted; partial SemVer strings are resolved to their 'latest' minor and patch releases). This value may also be a GitHub branch name (e.g. '**master**').
- An **optional** `biolink_version` tag can be given a value of the Biolink Model version against which the message knowledge graph semantic contents will be validated, expressed as a SemVer string (defaults to 'latest' Biolink Model Toolkit supported version, if omitted). 
- An **optional** `target_provenance` with an object dictionary (example shown) specifying the ARA and KP infores-specified knowledge sources expected to be recovered in the TRAPI query results (specified by infores CURIE) and the expected KP provenance source type, i.e. 'primary' implies that the KP is tagged as a 'biolink:primary_knowledge_source'. Optional in that the root "target_provenance" or any of the subsidiary tags may be omitted (default to None)
- An **optional** `strict_validation` flag (default: None or 'false'). If 'true' then follow strict validation rules, such as treating as 'error' states the use of `category`, `predicate` and `attribute_type_id` that are of type `abstract` or `mixin`  as errors. 
- A **mandatory** `message` tag should have as its value the complete JSON TRAPI **Response** to be validated (See the example below)

### Running the Web Service Directly

First, install the web-specific dependencies, if not already done:

```bash
poetry install --with web
```

The service may be run directly as a Python module. The web services module may be directly run, as follows. 

```shell
python -m api.main
```

Go to http://localhost/docs to see the service documentation and to use the simple UI to input TRAPI messages for validation.

### Typical Output

As an example of output to expect, if one posts the following TRAPI 2.0 Response JSON data structure to the **/validate** endpoint:

```json
{
  "trapi_version": "2.0.0",
  "biolink_version": "4.4.5",
  "response": {
      "message": {
        "query_graph": {
          "nodes": {
            "nA": {
              "categories": [
                "biolink:Drug"
              ]
            },
            "nI": {
              "categories": [
                "biolink:Gene"
              ],
              "set_interpretation": "COLLATE"
            },
            "nB": {
              "ids": [
                "MONDO:111"
              ],
              "categories": [
                "biolink:Disease"
              ]
            }
          },
          "edges": {
            "e1": {
              "subject": "nA",
              "object": "nI",
              "constraints": {
                "sources": {
                  "behavior": "DENY",
                  "values": [
                    "infores:semmeddb"
                  ]
                },
                "qualifiers": [
                  {
                    "biolink:object_direction_qualifier": "increased",
                    "biolink:object_aspect_qualifier": "activity_or_abundance"
                  }
                ]
              }
            },
            "e2": {
              "subject": "nI",
              "object": "nB",
              "constraints": {
                "knowledge_level": {
                  "behavior": "ALLOW",
                  "values": [
                    "knowledge_assertion",
                    "text_co_occurrence"
                  ]
                },
                "agent_type": {
                  "behavior": "ALLOW",
                  "values": [
                    "automated_agent"
                  ]
                },
                "attributes": [
                  {
                    "id": "biolink:z_score",
                    "operator": ">",
                    "value": 5
                  }
                ]
              }
            }
          }
        },
        "knowledge_graph": {
          "nodes": {
            "MONDO:111": {
              "categories": [
                "biolink:Disease"
              ],
              "name": "type 1 diabetes mellitus"
            },
            "CHEBI:1234": {
              "categories": [
                "biolink:Drug"
              ],
              "name": "Metformin"
            },
            "NCBIGene:7777": {
              "categories": [
                "biolink:Gene"
              ],
              "name": "EIF2_AK3"
            },
            "NCBIGene:5555": {
              "categories": [
                "biolink:Gene"
              ],
              "name": "HMOX1"
            }
          },
          "edges": {
            "e2_B": {
              "predicate": "biolink:affects",
              "subject": "NCBIGene:7777",
              "object": "MONDO:111",
              "knowledge_level": "knowledge_assertion",
              "agent_type": "automated_agent",
              "sources": [
                {
                  "resource_id": "infores:ctd",
                  "resource_role": "primary_knowledge_source"
                }
              ],
              "attributes": [
                {
                  "attribute_type_id": "biolink:z_score",
                  "value": 7.963
                }
              ]
            },
            "e1_B": {
              "predicate": "biolink:affects",
              "subject": "CHEBI:1234",
              "object": "NCBIGene:7777",
              "knowledge_level": "not_provided",
              "agent_type": "text_mining_agent",
              "sources": [
                {
                  "resource_id": "infores:text-mining-provider-targeted",
                  "resource_role": "primary_knowledge_source"
                }
              ],
              "qualifiers": [
                {
                  "qualifier_type_id": "biolink:qualified_predicate",
                  "qualifier_value": "biolink:causes"
                },
                {
                  "qualifier_type_id": "biolink:object_direction_qualifier",
                  "qualifier_value": "increased"
                },
                {
                  "qualifier_type_id": "biolink:object_aspect_qualifier",
                  "qualifier_value": "activity_or_abundance"
                }
              ]
            },
            "e2_A": {
              "predicate": "biolink:occurs_together_in_literature_with",
              "subject": "NCBIGene:5555",
              "object": "MONDO:111",
              "knowledge_level": "text_co_occurrence",
              "agent_type": "data_analysis_pipeline",
              "sources": [
                {
                  "resource_id": "infores:diseases",
                  "resource_role": "primary_knowledge_source"
                }
              ],
              "attributes": [
                {
                  "attribute_type_id": "biolink:z_score",
                  "value": 6.435
                }
              ]
            },
            "e1_A": {
              "predicate": "biolink:affects",
              "subject": "CHEBI:1234",
              "object": "NCBIGene:5555",
              "knowledge_level": "knowledge_assertion",
              "agent_type": "manual_agent",
              "sources": [
                {
                  "resource_id": "infores:chembl",
                  "resource_role": "primary_knowledge_source"
                }
              ],
              "qualifiers": [
                {
                  "qualifier_type_id": "biolink:qualified_predicate",
                  "qualifier_value": "biolink:causes"
                },
                {
                  "qualifier_type_id": "biolink:object_direction_qualifier",
                  "qualifier_value": "increased"
                },
                {
                  "qualifier_type_id": "biolink:object_aspect_qualifier",
                  "qualifier_value": "activity_or_abundance"
                }
              ]
            }
          }
        },
        "results": [
          {
            "node_bindings": {
              "nA": {
                "ids": [
                  "CHEBI:1234"
                ]
              },
              "nI": {
                "ids": [
                  "NCBIGene:5555",
                  "NCBIGene:7777"
                ]
              },
              "nB": {
                "ids": [
                  "MONDO:111"
                ]
              }
            },
            "analyses": [
              {
                "resource_id": "infores:retriever",
                "edge_bindings": {
                  "e1": {
                    "ids": [
                      "e1_A",
                      "e1_B"
                    ]
                  },
                  "e2": {
                    "ids": [
                      "e2_A",
                      "e2_B"
                    ]
                  }
                }
              }
            ]
          }
        ]
      },
      "parameters": {
        "log_level": "DEBUG",
        "bypass_cache": true,
        "timeout": 300,
        "tiers": [
          1
        ]
      },
      "biolink_version": "4.3.2",
      "schema_version": "1.6.0",
      "status": "Complete",
      "logs": [
        {
          "level": "INFO",
          "message": "Begin processing...",
          "timestamp": "1"
        },
        {
          "level": "DEBUG",
          "message": "Found 2 starting branches...",
          "timestamp": "2"
        }
      ]
    }
}
```

one should typically get a response body something like the following JSON validation result back:

```json
{
  "messages": {
    "Validate TRAPI Response": {
      "Standards Test": {
        "info": {
          "info.query_graph.edge.predicate.mixin": {
              "biolink:treats": [
                {
                  "edge_id": "drug[biolink:Drug]--['biolink:treats']->type-2 diabetes[None]"
                }
              ]
          }
        },
        "skipped": {},
        "warning": {},
        "error": {
          "error.query_graph.edge.predicate.invalid": {
              "biolink:treats": [
                {
                  "edge_id": "drug[biolink:Drug]--['biolink:treats']->type-2 diabetes[None]"
                }
              ]
          }
        },
        "critical": {}
      }
    }
  },
  "trapi_version": "v2.0.0-beta2",
  "biolink_version": "4.4.5"
}
```

To minimize redundancy in validation messages, messages are uniquely indexed in dictionaries at two levels:

1. the (codes.yaml recorded) dot-delimited validation code path string
2. for messages with templated parameters, by a mandatory 'identifier' field (which is expected to exist as a field in a template if such template has one or more parameterized fields)

### OpenTelemetry and Jaeger

NOTE: OpenTelemetry is temporarily disabled in this code release (to be updated later)

The web service may be monitored for OpenTelemetry by setting an environment variable **TELEMETRY_ENDPOINT**  to a suitable trace collecting endpoint in an application like [Jaeger](https://www.jaegertracing.io/) (see also the [Translator SRI Jaeger-Demo](https://github.com/TranslatorSRI/Jaeger-demo)).

**Note:** the current system Docker (Compose) design only supports OpenTemplate tracing using the internal Jaeger container and may require further refinements to enable use of an external telemetry collector.

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

Of course, the user may customize the above docker-compose commands to suit their needs. Note that the docker implementation assumes the use of uvicorn

## Change Log

Summary of earlier releases and current Change Log is [here](CHANGELOG.md).

## Code Limitations (implied Future Work?)

- The v7.0.0 release of the reasoner-validator is only warranted to validate TRAPI 2.0.* responses.
- The release of the reasoner-validator after v5.0.0 will not validate TRAPI JSON data models prior to 1.5.0 (in fact, its behavior will be undefined for such data).
- Biolink Model release <= 2.4.8 versus 3.0.0 validation: the reasoner-validator uses the Biolink Model Toolkit. As it happens, the toolkit is not backwards compatible with at least one Biolink Model structural change from release 2.#.# to 3.#.#: the tagging of 'canonical' predicates. That is, the 0.8.10++ toolkit reports canonical <= 2.4.8 model predicates as 'non-canonical'.
- The web service validation doesn't do deep validation of the Results part of a TRAPI Message
- The validation is only run on the first 1000 nodes and 100 edges of a knowledge graph, to keep the validation time tractable (this risks not having complete coverage of the graph)
- Biolink Model toolkit is not (yet) cached, so changing the model version during use will result in some latency in results
- The validator service doesn't (yet) deeply validate non-core node and edge slot contents of Message Knowledge Graphs
- The validator service doesn't (yet) attempt validation of Query Graph nodes and edges 'constraints' (e.g. `biolink:Association` etc. `domain` and `range` constraints)
- Query Graph node 'ids' are not validated except when an associated 'categories' parameter is provided for the given node. In general, [Query Graph Validation](https://github.com/NCATSTranslator/reasoner-validator/issues/14) could be elaborated.
- The system should leverage the [Reasoner Pydantic Models](https://github.com/NCATSTranslator/reasoner-validator/issues/15)

# Core Contributors

- Kudos to Patrick Wang, who created the original implementation of the Reasoner-Validator project while with CoVar (an entrepreneurial team contributing to the Biomedical Data Translator).
- Thanks to Kenneth Morton (CoVar) for his reviews of the latest code.
- The project is currently being extended and maintained by Richard Bruskiewich (Delphinai Corporation, subcontractor to the LBNL team contributing to Translator)
