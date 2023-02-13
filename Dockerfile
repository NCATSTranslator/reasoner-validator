FROM python:3.9
RUN mkdir -p /code
WORKDIR /code
RUN pip install poetry
COPY ./pyproject.toml ./pyproject.toml
COPY ./poetry.lock ./poetry.lock
COPY ./reasoner_validator ./reasoner_validator
COPY ./tests ./tests
COPY ./docs ./docs
COPY ./README.md ./README.md
COPY ./CHANGELOG.md ./CHANGELOG.md
COPY api ./api
RUN python -m poetry install
EXPOSE 80
CMD ["poetry", "run", "uvicorn", "api.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
