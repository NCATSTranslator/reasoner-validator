# Reasoner Validator

[![Pyversions](https://img.shields.io/pypi/pyversions/reasoner-validator)](https://pypi.python.org/pypi/reasoner-validator)
[![pypi](https://github.com/NCATSTranslator/reasoner-validator/workflows/pypi/badge.svg)](https://pypi.org/project/reasoner-validator/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![readthedocs](https://readthedocs.org/projects/reasoner-validator/badge/)](https://reasoner-validator.readthedocs.io/)

See the [documentation](https://reasoner-validator.readthedocs.io/) and/or [contributor guidelines](https://github.com/NCATSTranslator/reasoner-validator/blob/master/.github/CONTRIBUTING.md).

### Building

To build the documentation:

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
  "trapi_version": "1.0",
  "biolink_version": "2.2.16",
  "message": "<TRAPI JSON message blob...>"
}
```

The request body consists of JSON data structure with two top level tag:

- An **optional** `trapi_version` tag can be given a value of the TRAPI version against which the message will be validated, expressed as a SemVer string (defaults to 'latest' if omitted; partial SemVer strings are resolved to their 'latest' minor and patch releases). 
- An **optional** `biolink_version` tag can be given a value of the Biolink Model version against which the message knowledge graph semantic contents will be validated, expressed as a SemVer string (defaults to 'latest' Biolink Model Toolkit supported version, if omitted). 
- A **mandatory** `message` tag should have as its value the complete TRAPI **Message** JSON data structure to be validated.

### Running the Web Service Directly

The service may be run directly as a python module. It is suggested that a virtual environment first be created (using virtualenv, conda, within your IDE, or equivalent).  Then, certain Python dependencies need to be installed, as follows:

```shell
pip install -r requirements-service.txt
```

The module may afterwards be run, as follows:

```shell
python -m app.main
```

Go to  http://localhost/docs to see the service documentation and to use the simple UI to input TRAPI messages for validation.

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

## Validation Web Service Limitations (implied Future Work?)

- This release of the Reasoner Validator Web Service will detect TRAPI 1.0.* releases but doesn't strive to be completely backwards compatible with them (considering that they are less relevant now). 
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
