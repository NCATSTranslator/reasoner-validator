Reasoner Validator
==================

This documentation describes the use and API for the  3.0.* releases of the Reasoner-Validator Library.

In particular, this package provides various methods for validating any component *in any version* of the
`Translator Reasoner API (TRAPI) <https://github.com/NCATSTranslator/ReasonerAPI/blob/master/README.md>`_ and `Biolink Model <https://github.com/biolink/biolink-model/blob/master/README.md>`_.

This project has two dimensions of validation: one for TRAPI OpenAPI schema validation and the other for Biolink Model semantic validation.

Note that the functioning of this release is not backwards compatible with 2.2.* or earlier releases of the package.

Installation
============

As Pypi Package
---------------

.. code-block:: bash

  pip install reasoner-validator

will install the package from Pypi.org.

From Github
-----------

Checkout then setup dependencies and the standard virtual environment using poetry, as follows:

.. code-block:: bash

    git checkout https://github.com/NCATSTranslator/reasoner-validator.git
    cd reasoner-validator
    poetry install
    poetry shell

These operations install the software and creates a virtual operation for running the software in a simple fashion.

You can optionally, `use a tool like pyenv to set your local shell Python version to a 3.9 release <https://python-poetry.org/docs/managing-environments/>`_  prior to the poetry installation.

Basic Programmatic Usage
========================

Unlike earlier release of the reasoner-validator package, the current (major release 3.*.*) wraps validation in a general Python class object, 'ValidatorReporter' which is subclassed into various validator types (TRAPI Schema, Biolink, etc.).

Top level programmatic validation of a TRAPI Response uses a TRAPIResponseValidator class wrapper as follows (sample script):

.. code-block:: python

    #!/usr/bin/env python
    from typing import Optional, List, Dict
    from reasoner_validator import TRAPIResponseValidator
    from reasoner_validator import MESSAGE_CATALOG

    SAMPLE_RESPONSE = {
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
    validator = TRAPIResponseValidator(
        trapi_version="1.4.2",

        # If omit or set the Biolink Model version parameter to None,
        # then the current Biolink Model Toolkit default release applies
        biolink_version="3.5.0",

        # 'sources' are set to trigger checking of expected edge knowledge source provenance
        sources={
                "ara_source": "infores:molepro",
                "kp_source": "infores:hmdb",
                "kp_source_type": "primary"
        },
        # Optional flag: if omitted or set to 'False', we let the system decide the
        # default validation strictness by validation context unless we override it here
        strict_validation=False
    )

    # Unlike earlier release of the package, validation methods do NOT throw an exception,
    # but rather, return validation outcomes as a dictionary of validation messsages
    # Here, the 'message' parameter here is just the Python equivalent dictionary of the
    # TRAPI.Message JSON schema model component of the TRAPI Response (not the full TRAPI Response...yet)

    # this method validates a complete TRAPI Response JSON result
    validator.check_compliance_of_trapi_response(response=SAMPLE_RESPONSE)

    # Raw message data is retrieved from the validator object as follows:
    messages: MESSAGE_CATALOG = validator.get_messages()

    # this method dumps a human readable text report of
    # the validation messages (default) to stdout
    # See the method signature for options that
    # allow customization of the text format.
    validator.dump()

The 'messages' returned are partitioned into 'information', 'warning', 'error' and 'critical' (error) messages
in a dictionary looking something like the following (as an example):

.. code-block:: python

    messages: Dict[str, List[Dict[str,str]]] = {
        "information": {
            "info.excluded": {
                # source scope of the validation error ("global" or some knowledge source path string
                "global": {
                    # the uniquely discriminating 'identifier' here is the edge_id
                    "(ZFIN:ZDB-GENE-060825-345$biolink:Gene)--[biolink:active_in]->(GO:0042645$biolink:CellularComponent)": None
                    # messages with only a contextual identifier may have no additional parameters
                },
                {...}  # another message (same code type)
            },
            "info.compliant": None  # parameterless messages don't have distinct instances
             # other 'info' code-indexed messages
        },
        "warnings": {
            "warning.edge.predicate.non_canonical": {
                "infores:chebi -> infores:molepro -> infores:arax": {
                    # the uniquely discriminating 'identifier' here is the is the predicate term
                    "biolink:participates_in":
                    {   # the secondary context is the 'edge_id'
                        "edge_id": "a--['biolink:participates_in']->b",
                    },
                    {...}  # another predicate indexed message (same code type)                
                }
            },
            "warning.trapi.response.status.unknown" {
                "global": {
                    "500": None  # unexpected http status code returned
                }
            },
            # other 'warning' code-indexed messages
        },
        "errors": {
            "error.biolink.model.noncompliance": {
                "infores:chebi -> infores:molepro -> infores:arax": {
                    "biolink:vitamin": {
                        "biolink_release": "3.4.5"
                    }
                }
            },
            # other 'errors' code-indexed messages
        },
        "critical": {
            "critical.trapi.request.invalid": {
                "global": {
                    # subject node descriptor is the 'identifier'
                    "CHEBI:37565[biolink:SmallMolecule]":
                    {
                        "test": "raise_subject_entity"
                        "reason": "has no 'is_a' parent since it is either not an ontology term or does not map onto a parent ontology term."
                    },
                    {...} # another message (same code type)                
                }
            },
            # other 'critical' code-indexed messages
        }
    }


Every message has a 'code' and optional context-specific parameters which correspond to
named fields in the Python string templates found in the `reasoner_validator package 'codes.yaml' file <https://github.com/NCATSTranslator/reasoner-validator/blob/master/reasoner_validator/codes.yaml>`_.

Note that the trapi_version parameter to the TRAPIResponseValidator can also be a local path to a .yaml TRAPI schema file, which is read in and used as the validation standard. In such a case, though, it is necessary to encode the TRAPI version as a suffix to the root filename, e.g. my_trapi_schema_1.4.0-beta5.yaml. Note that the TRAPI version suffix to the root file name is assumed to be delimited by a leading underscore character. The simplistic parsing of this version is as follows:

.. code-block:: python
    root_path: str = string.replace(".yaml", "")
    semver_string = root_path.split("_")[-1]

Python API
----------
.. toctree::
   :maxdepth: 2

   TRAPI Response Validation <reasoner_validator>
   TRAPI Schema Validation <reasoner_validator.trapi>
   TRAPI Result Mapping <reasoner_validator.trapi.mapping>
   Biolink Validation <reasoner_validator.biolink>
   Validator Reporter <reasoner_validator.report>
   Validation Codes Dictionary <reasoner_validator.validation_codes>
   Validation Codes <validation_codes_dictionary>
   SemVer Version Utilities <reasoner_validator.versioning>

Refer to the `reasoner_validator package unit tests <https://github
.com/NCATSTranslator/reasoner-validator/blob/master/tests>`_ for additional guidance on how to use the Python API.


Running Validation against an ARS UUID Result(*) or using a Local TRAPI Request Query
=====================================================================================

A local script trapi_validator.py is available to run TRAPI Response validation against either a PK (UUID)
indexed query result of the Biomedical Knowledge Translator "Autonomous Relay System" (ARS), a local JSON Response
text file or a locally triggered _ad hoc_ query Request against an directly specified TRAPI endpoint.

Note that it is best run within a **`poetry shell`** created by **`poetry install`**.

For script usage, type:

.. code-block:: bash

    ./trapi_validator.py --help


Validation Run as a Web Service
===============================

The Reasoner Validator is available wrapped as a simple web service.  The service may be run directly or as a Docker container.

Web Service API
---------------

The web service has a single POST endpoint `/validate` taking a simple JSON request body, as follows:

.. code-block:: json

    {
        # If the TRAPI version is omitted or set to None, then the 'latest' TRAPI version is used.

        # Note: for TRAPI releases from 1.4.0 onwards, the Response message will state the assumed 'schema_version'.
        # This modifies slightly the interpretation of this parameter, as follows:
        # If the following trapi_version parameter is given, then it overrides the TRAPI Response 'schema_version';
        # Otherwise, the TRAPI Response 'schema_version' (not 'latest') becomes the default validation version.

        trapi_version="1.4.2",

        # If the Biolink Model version is omitted or set to None, then the current Biolink Model Toolkit is used.

        # Note: for TRAPI releases from 1.4.0 onwards, the Response message will state the assumed 'biolink_version'.
        # This modifies slightly the interpretation of this parameter, as follows:
        # If the 'biolink_version' given here is assumed, which overrides the TRAPI Response stated 'biolink_version';
        # Otherwise, the TRAPI Response stated 'biolink_version' (not BMT) becomes the default validation version.

        biolink_version="3.5.0",

        "sources": {
            "ara_source": "infores:aragorn",
            "kp_source": "infores:panther",
            "kp_source_type": "primary"
        },
        "strict_validation": true,
        "response": {"some TRAPI Response JSON - see below"}
    }


The request body consists of JSON data structure with two top level tag:

* An **optional** `trapi_version` tag can be given a value of the TRAPI version against which the message will be validated, expressed as a SemVer string (defaults to 'latest' if omitted; partial SemVer strings are resolved to their 'latest' minor and patch releases).
* An **optional** `biolink_version` tag can be given a value of the Biolink Model version against which the message knowledge graph semantic contents will be validated, expressed as a SemVer string (defaults to 'latest' Biolink Model Toolkit supported version, if omitted).
* An **optional** `sources` with an object dictionary (example shown) specifying the ARA and KP sources involved in the TRAPI call (specified by infores CURIE) and the expected KP provenance source type, i.e. 'primary' implies that the KP is tagged as a 'biolink:primary_knowledge_source'. Optional in that the root "sources" or any of the subsidiary tags may be omitted (default to None)
* An **optional** `strict_validation` flag (default: None or 'false'). If 'true' then follow strict validation rules, such as treating as 'error' states the use of `category`, `predicate` and `attribute_type_id` that are of type `abstract` or `mixin`  as errors.
* A **mandatory** `response` tag should have as its value the complete TRAPI **Response** JSON data structure to be validated (see example below).

Running the Web Service Directly
--------------------------------

The service may be run directly as a Python module after certain dependencies are installed using poetry, as follows:

.. code-block:: bash

    poetry install
    poetry shell

The module may afterwards be run, as follows:

.. code-block:: bash

    python -m api.main

Run on your local machine, an OpenAPI web service form may now be viewed at http://localhost/docs/

Typical Output
--------------

As an example of the kind of output to expect, if one posts the following TRAPI Response JSON data as input to the **/validate** endpoint:

.. code-block:: json

    {
        "schema_version": "1.4.2",
        "biolink_version": "3.5.0",
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
                    "df87ff82": {
                        "subject": "CHEBI:6801",
                        "predicate": "biolink:treats",
                        "object": "MONDO:0005148",
                        "sources": [
                           {
                               "resource_id": "infores:aragorn",
                               "resource_role": "primary_knowledge_source"
                           },
                           {
                               "resource_id": "infores:chebi",
                               "resource_role": "primary_knowledge_source"
                           }
                        ]
                    }
                }
            },
            "results": [
                {
                    "node_bindings": {
                        "type-2 diabetes": [{"id": "MONDO:0005148"}],
                        "drug": [{"id": "CHEBI:6801"}]
                    },
                    "analyses": [
                        {
                            "resource_id": "infores:aragorn",
                            "edge_bindings": {
                                    "treats": [{"id": "df87ff82"}]
                            }
                        }
                    ]
                }
            ]
        },
        "workflow": [
            {
                "id": "lookup"
            }
        ]
    }

then, one should typically get a response body like the following JSON validation result back:

.. code-block:: json

    {
      "trapi_version": "1.4.2",
      "biolink_version": "3.5.0",
      "messages": {
        "critical": {},
        "errors": {
          "error.knowledge_graph.node.category.missing": {
             "infores:chebi -> infores:molepro -> infores:arax": {
                "MONDO:0005148": [
                  {
                    "context": "Knowledge Graph"
                  }
                ]
            }
          }
        },
        "warnings": {
          "warning.knowledge_graph.node.id.unmapped_prefix": {
            "infores:chebi -> infores:molepro -> infores:arax": {
                "CHEBI:6801": [
                  {
                    "categories": "['biolink:Drug']"
                  }
                ]
            }
          },
          "warning.knowledge_graph.edge.provenance.kp.missing": {
            "infores:chebi -> infores:molepro -> infores:arax": {
                "infores:panther": [
                  {
                    "kp_source_type": "biolink:primary_knowledge_source",
                    "identifier": "CHEBI:6801--biolink:treats->MONDO:0005148"
                  }
                ]
            }
          }
        },
        "information": {}
      }
    }

Validation Code Definitions
===========================

The validation message codes issued by the validation software is formally indexed in a single file called codes.yaml.

Running the Web Service within Docker
=====================================

The Reasoner Validator web service may be run inside a docker container, using Docker Compose.

First, from the root project directory, build the local docker container

.. code-block:: bash

    docker-compose build


Then, run the service:

.. code-block:: bash

    docker-compose up -d


Once again, go to `http://localhost/docs <http://localhost/docs>`_ to see the web service API documentation.

To stop the service:

.. code-block:: bash

    docker-compose down

Of course, the above docker-compose commands may be customized by the user to suit their needs. Note that the docker implementation assumes the use of uvicorn


Quick History of Releases
=========================

The Reasoner Validator package is evolving along with progress in TRAPI and Biolink standards within the NCATS Biomedical Knowledge Translator. This documentation pertains to the 3.* releases of the package. A synopsis of the evolution of the package is:

* 1.# releases - very preliminary releases of the validation code, now obsolete
* 2.# releases - had a base TRAPI schema 'validate' with errors throwing a Python exception; later minor iterations added in Biolink Model validation returning a flat dictionary of arcane string messages
* 3.0.# releases
  - wrapped the all validation with a ValidatorReporter class serving to collect and return validation messages in a disciplined, codified manner (as a [master YAML file with hierarchically-indexed Python string templates](reasoner_validator/codes.yaml)). Generally still reliably validates Biolink Model release <= 2.4.8
* 3.1.# releases: mainly supports Biolink Model releases >= 3.0.* and will likely generate some spurious validation warnings or errors for Biolink Model release <= 2.4.8 (reflects non-backward compatible changes to the Biolink Model Toolkit)

The `full change log is here <https://github.com/NCATSTranslator/reasoner-validator/blob/master/CHANGELOG.md>`_.

Community
=========

See `project README for full details <https://github.com/NCATSTranslator/reasoner-validator/blob/master/README.md>`_

Contribute
----------

- `Report a bug <https://github.com/NCATSTranslator/reasoner-validator/issues/new?template=bug_report.md>`_
- `Request a feature <https://github.com/NCATSTranslator/reasoner-validator/issues/new?template=feature_request.md>`_

Support
-------

- `Ask a question <https://github.com/NCATSTranslator/reasoner-validator/issues/new?template=question.md>`_

License
-------

The project is licensed under the MIT license.
