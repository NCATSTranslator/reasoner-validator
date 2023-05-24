dev-install:
	poetry install --all-extras

install:
	poetry install

test:
	poetry run pytest tests/*