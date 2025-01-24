NAME = gaussianfft

EMPTY :=

CODE_DIR ?= $(shell pwd)

PYTHON ?= $(shell which python3)
ifeq ($(origin VIRTUAL_PYTHON), undefined)
all: venv
VIRTUAL_PYTHON = $(CODE_DIR)/venv/bin/python
endif
PIP_INSTALL := $(VIRTUAL_PYTHON) -m pip install --upgrade

ifeq ($(OS),Windows_NT)
    detected_OS := Windows
else
    detected_OS := $(shell uname -s)
endif

.PHONY: all tests clean


install:
	$(PYTHON) -m pip install $(CODE_DIR)

venv:
ifeq ($(ENFORCE_CLEAN_GIT),true)
	# Ensure git 'trusts' the directory inside docker
	git config --global --add safe.directory $(CODE_DIR)
	$(CODE_DIR)/bin/ensure-clean-working-directory.sh

endif
	$(PYTHON) -m venv venv

build-sdist: venv
	$(PIP_INSTALL) build
	PYTHONPATH=$(CODE_DIR):$(PYTHONPATH) \
	$(VIRTUAL_PYTHON) -m build --sdist

clean:
	cd $(CODE_DIR) && \
	rm -rf build \
	       venv \
	       dist \
	       .pytest_cache \
	       .numpy.json \
	       *.so


print-%  : ; @echo $($*)
