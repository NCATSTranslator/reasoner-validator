# Reasoner Validator

[![pypi](https://github.com/NCATSTranslator/reasoner-validator/workflows/pypi/badge.svg)](https://pypi.org/project/reasoner-validator/)
[![readthedocs](https://readthedocs.org/projects/reasoner-validator/badge/)](https://reasoner-validator.readthedocs.io/)

See the [documentation](https://reasoner-validator.readthedocs.io/) and/or [contributor guidelines](https://github.com/NCATSTranslator/reasoner-validator/blob/master/.github/CONTRIBUTING.md).

### Building

To build the documentation:

```bash
cd docs
make html
```

## Validation Run as a Web Service

The Reasoner Validator is available wrapped as a simple web service, which may be run directly as a python module:

```shell
python -m app.main
```

Go to  http://localhost/docs to see the service documentation and to use the simple UI to input TRAPI messages for validation.

### API
The web service has a single POST endpoint `/validate` taking a simple JSON request body, as follows:

```json
{
  "version": "1",
  "message": "<TRAPI JSON message blob...>"
}
```

The request body consists of JSON data structure with two top level tag:

- An optional `version` tag should be given a value of the TRAPI version against which the message will be validated, expressed as a SemVer string (defaults to 'latest' if omitted; partial SemVer strings are resolved to their 'latest' minor and patch releases). 
- A mandatory `message` tag should have as its value the complete TRAPI **Message** JSON data structure to be validated.

### Docker Container

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
