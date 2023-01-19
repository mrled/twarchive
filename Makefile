.SUFFIXES:

# TWV = twarchive version
TWV := $(shell venv/bin/twarchive version --quiet)
DIST_WHEEL := twarchive/dist/twarchive-$(TWV)-py3-none-any.whl
DIST_TARGZ := twarchive/dist/twarchive-$(TWV).tar.gz

# The now-defunct Twitter SMS shortcode
DEVPORT := 40404

.PHONY: help
help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo "If you get an error like this:"
	@echo "	make: venv/bin/twarchive: Command not found"
	@echo "Run 'make venv' and it will go away"

.PHONY: clean
clean: ## Remove venv, builds, etc
	rm -rf venv dist *.egg-info twarchive/dist twarchive/*.egg-info

venv: ## Create the virtual environment
	python3 -m venv venv
	venv/bin/pip install --upgrade pip setuptools twine build
	venv/bin/pip install -e ./twarchive

$(DIST_WHEEL) $(DIST_TARGZ): venv
	cd ./twarchive && ../venv/bin/python -m build

showdist: venv ## Show files in the dist/ directory
	@ls -alF $(DIST_WHEEL)
	@ls -alF $(DIST_TARGZ)

.PHONY: pybuild
pybuild: $(DIST_WHEEL) $(DIST_TARGZ) ## Build Python packages for uploading to PyPi

.PHONY: twineupload
twineupload: venv $(DIST_WHEEL) $(DIST_TARGZ) ## Upload Python packages to PyPi
	venv/bin/twine check $(DIST_WHEEL) $(DIST_TARGZ)
	venv/bin/twine upload $(DIST_WHEEL) $(DIST_TARGZ)

.PHONY: tests
tests: venv ## Run unit tests for the Python project
	cd ./twarchive && ../venv/bin/python -m unittest discover

.PHONY: dev
dev: ## Run a dev server for the exampleSite
	cd ./exampleSite && hugo serve --port $(DEVPORT)
