install:
	poetry install --extras dev,docs,web

test:
	poetry install --extras dev
	poetry run pytest tests/*

docs:
	poetry install --extras docs
	cd reasoner_validator && poetry run python validation_codes.py
	cd docs && poetry run sphinx-build -b html . _build

clean:
	rm -rf docs/_build

.PHONY: docs clean test install