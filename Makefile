.POSIX:
.SUFFIXES:

help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

venv: ## Create the virtual environment
	python3 -m venv venv

.PHONY: pipinstall
pipinstall: venv ## Install twarchive as a pip package in the venv
	venv/bin/pip install --upgrade pip setuptools twine build
	venv/bin/pip install -e .

.PHONY: pybuild
pybuild: ## Build a package for uploading to pypi
	venv/bin/python -m build
	venv/bin/twine check dist/*
