FROM python:3.9
WORKDIR /code
RUN pip install poetry
COPY ./pyproject.toml /code/pyproject.toml
COPY ./poetry.lock /code/poetry.lock
COPY ./reasoner_validator /code/reasoner_validator
COPY ./tests /code/tests
COPY ./docs /code/docs
COPY ./README.md /code/README.md
COPY ./CHANGELOG.md /code/CHANGELOG.md
COPY api /code/api
RUN python -m poetry install
EXPOSE 80
CMD ["poetry", "run", "uvicorn", "api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
