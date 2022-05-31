MODULE := packmol_step
.PHONY: help clean clean-build clean-pyc clean-test lint format typing test dependencies
.PHONY: test-all coverage html docs servedocs release check-release dist install uninstall
.DEFAULT_GOAL := help
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts


clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	find . -name '.pytype' -exec rm -fr {} +

lint: ## check style with black and flake8
	black --check --diff $(MODULE) tests
	flake8 $(MODULE) tests

format: ## reformat with with black and isort
	black $(MODULE) tests

typing: ## check typing
	pytype $(MODULE)

test: ## run the unit tests
	py.test

test-all: ## run all the tests
	py.test --integration --timing

test-integration: ## run the integration tests
	py.test --no-unit --integration

test-timing: ## run the timing tests
	py.test --no-unit --timing

dependencies:
	pur -r requirements_dev.txt
	pip install -r requirements_dev.txt

coverage: ## code coverage using only the unit tests (fast!)
	pytest --cov-report term --cov-report html:htmlcov --cov $(MODULE)  tests/
	$(BROWSER) htmlcov/index.html

coverage-all: ## code coverage using all tests (slow)
	pytest --cov-report term --cov-report html:htmlcov --cov $(MODULE)  --integration --timing tests/
	$(BROWSER) htmlcov/index.html

coverage-integration: ## code coverage using only the integration tests
	pytest --cov-report term --cov-report html:htmlcov --cov $(MODULE)  --no-unit --integration tests/
	$(BROWSER) htmlcov/index.html

coverage-report: ## code coverage using only the unit tests (fast!) with only a text report
	pytest --cov-report term --cov $(MODULE)  tests/

coverage-all-report: ## code coverage using all tests (slow) with only a text report
	pytest --cov-report term --cov $(MODULE)  --integration --timing tests/

coverage-integration-report: ## code coverage using only the integration tests with only a text report
	pytest --cov-report term --cov $(MODULE)  --no-unit --integration tests/

html: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/developer/$(MODULE).rst
	rm -f docs/developer/modules.rst
	sphinx-apidoc -o docs/developer $(MODULE)
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

docs: html ## Make the html docs and show in the browser
	$(BROWSER) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: dist ## package and upload a release
	python -m twine upload dist/*

check-release: dist ## check the release for errors
	python -m twine check dist/*

dist: clean ## builds source and wheel package
	python -m build
	ls -l dist

install: uninstall ## install the package to the active Python's site-packages
	pip install .

uninstall: clean ## uninstall the package
	pip uninstall --yes $(MODULE)
