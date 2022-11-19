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

From Github
-----------

.. code-block:: bash

    git checkout https://github.com/NCATSTranslator/reasoner-validator.git
    cd reasoner-validator
    pip install -e .

Basic Programmatic Usage
========================

Unlike earlier release of the reasoner-validator package, the current (major release 3.*.*) wraps validation in a general Python class object, 'ValidatorReporter' which is subclassed into various validator types (TRAPI Schema, Biolink, etc.).

Top level programmatic validation of a TRAPI Response uses a TRAPIResponseValidator class wrapper as follows:

.. code-block:: python

    from reasoner_validator import TRAPIResponseValidator

    validator = TRAPIResponseValidator(
        trapi_version="1.3.0",

        # If omit or set the Biolink Model version parameter to None,
        # then the current Biolink Model Toolkit default release applies
        biolink_version="3.0.3",

        # 'sources' are set to trigger checking of expected edge knowledge source provenance
        sources={
                "ara_source": "infores:molepro",
                "kp_source": "infores:hmdb",
                "kp_source_type": "primary"
        },
        # Optional flag: if omitted or set to 'None', we let the system decide the
        # default validation strictness by validation context unless we override it here
        strict_validation=None
    )

    # Unlike earlier release of the package, validation methods do NOT throw an exception,
    # but rather, return validation outcomes as a dictionary of validation messsages
    # Here, the 'message' parameter here is just the Python equivalent dictionary of the
    # TRAPI.Message JSON schema model component of the TRAPI Response (not the full TRAPI Response...yet)
    validator.check_compliance_of_trapi_response(message=...)

    # Messages are retrieved from the validator object as follows:
    messages: Dict[str, List[Dict[str,str]]] = validator.get_messages()


The 'messages' returned are partitioned into 'information', 'warning' and 'error' messages
in a dictionary looking something like the following (as an example):

.. code-block:: python

    messages: Dict[str, List[Dict[str,str]]] = {
        "information": [
            {
                "edge_id": "(ZFIN:ZDB-GENE-060825-345$biolink:Gene)--[biolink:active_in]->(GO:0042645$biolink:CellularComponent)",
                "code": "info.excluded"
            }
        ],
        "warnings": [
            {
                "context": "Query Graph",
                "edge_id": "a--['biolink:participates_in']->b",
                "predicate": "biolink:participates_in",
                "code": "warning.edge.predicate.non_canonical"
            }
        ],
        "errors": [
            {
                "context": "raise_subject_entity() test predicate CHEBI:37565[biolink:SmallMolecule]",
                "reason": "has no 'is_a' parent since it is either not an ontology term or does not map onto a parent ontology term.",
                "code": "error.trapi.request.invalid"
            }
        ]
    }


Every message has a 'code' and optional context-specific parameters which correspond to
named fields in the Python string templates found in the `reasoner_validator package 'codes.yaml' file <https://github.com/NCATSTranslator/reasoner-validator/blob/master/reasoner_validator/codes.yaml>`_ file.

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

Validation Run as a Web Service
===============================

The Reasoner Validator is available wrapped as a simple web service.  The service may be run directly or as a Docker container.

Web Service API
---------------

The web service has a single POST endpoint `/validate` taking a simple JSON request body, as follows:

.. code-block:: json

    {
      "trapi_version": "1.3.0",
      "biolink_version": "3.0.3",
      "sources": {
        "ara_source": "infores:aragorn",
        "kp_source": "infores:panther",
        "kp_source_type": "primary"
      },
      "strict_validation": true,
      "message": {"some message"}
    }


The request body consists of JSON data structure with two top level tag:

* An **optional** `trapi_version` tag can be given a value of the TRAPI version against which the message will be validated, expressed as a SemVer string (defaults to 'latest' if omitted; partial SemVer strings are resolved to their 'latest' minor and patch releases).
* An **optional** `biolink_version` tag can be given a value of the Biolink Model version against which the message knowledge graph semantic contents will be validated, expressed as a SemVer string (defaults to 'latest' Biolink Model Toolkit supported version, if omitted).
* An **optional** `sources` with an object dictionary (example shown) specifying the ARA and KP sources involved in the TRAPI call (specified by infores CURIE) and the expected KP provenance source type, i.e. 'primary' implies that the KP is tagged as a 'biolink:primary_knowledge_source'. Optional in that the root "sources" or any of the subsidiary tags may be omitted (default to None)
* An **optional** `strict_validation` flag (default: None or 'false'). If 'true' then follow strict validation rules, such as treating as 'error' states the use of `category`, `predicate` and `attribute_type_id` that are of type `abstract` or `mixin`  as errors.
* A **mandatory** `message` tag should have as its value the complete TRAPI **Message** JSON data structure to be validated (see example below).

Running the Web Service Directly
--------------------------------

The service may be run directly as a python module. It is suggested that a virtual environment first be created (using virtualenv, conda, within your IDE, or equivalent).  Then, certain Python dependencies need to be installed, as follows:

.. code-block:: bash

    pip install -r requirements-service.txt


The module may afterwards be run, as follows:

.. code-block:: bash

    python -m api.main


Typical Output
--------------

As an example of the kind of output to expect, if one posts the following JSON message data to the **/validate** endpoint:

.. code-block:: json

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

one should typically get a response body like the following JSON validation result back:

.. code-block:: json

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
