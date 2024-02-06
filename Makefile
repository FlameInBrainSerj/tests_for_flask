quality-check: isort black flake8 mypy

poetry:
	pip install poetry
	poetry install

pre-commit:
	pre-commit install
	pre-commit autoupdate

isort:
	isort . --profile black

black:
	black .

mypy:
	mypy .

flake8:
	flake8 .

run-test:
	coverage run -m pytest tests

test-cov: run-test
	pytest --cov --cov-report=html:coverage_report