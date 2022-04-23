.SUFFIXES:

# TWV = twarchive version
TWV := $(shell venv/bin/twarchive version --quiet)
DIST_WHEEL := dist/twarchive-$(TWV)-py3-none-any.whl
DIST_TARGZ := dist/twarchive-$(TWV).tar.gz

.PHONY: help
help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo "If you get an error like this:"
	@echo "	make: venv/bin/twarchive: Command not found"
	@echo "Run 'make venv' and it will go away"

.PHONY: clean
clean: ## Remove venv, builds, etc
	rm -rf venv dist *.egg-info

venv: ## Create the virtual environment
	python3 -m venv venv
	venv/bin/pip install --upgrade pip setuptools twine build
	venv/bin/pip install -e .

$(DIST_WHEEL) $(DIST_TARGZ): venv
	venv/bin/python -m build

showdist: venv ## Show files in the dist/ directory
	@ls -alF $(DIST_WHEEL)
	@ls -alF $(DIST_TARGZ)

.PHONY: pybuild
pybuild: $(DIST_WHEEL) $(DIST_TARGZ) ## Build Python packages for uploading to PyPi

.PHONY: twineupload
twineupload: venv $(DIST_WHEEL) $(DIST_TARGZ) ## Upload Python packages to PyPi
	venv/bin/twine check $(DIST_WHEEL) $(DIST_TARGZ)
	venv/bin/twine upload $(DIST_WHEEL) $(DIST_TARGZ)
