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

## Validation as a Web Service

The Reasoner Validator is available wrapped as a simple Dockerized web service.

First, from the root project directory, build the local docker container

```
docker build -t trapi-validator .
```

Then, run the service:

```
docker run -d --rm --name trapi-validator -p 80:80 trapi-validator
```

Go to  http://127.0.0.1/docs to see the service documentation.

Of course, the above docker build and run commands may be modified to suit the user of the service.
