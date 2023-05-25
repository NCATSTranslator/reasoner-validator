install:
	poetry install --with dev,docs,web

test:
	poetry install --with dev
	poetry run pytest tests/*

docs:
	poetry install --with docs
	cd reasoner_validator
	poetry run python validation_codes.py
	cd ..
	cd docs/
	poetry run sphinx-build -b html . _build