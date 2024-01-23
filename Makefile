NAME = gaussianfft

EMPTY :=

CODE_DIR ?= $(shell pwd)

PYTHON ?= $(shell which python3)
ifeq ($(origin VIRTUAL_PYTHON), undefined)
all: venv
VIRTUAL_PYTHON = $(CODE_DIR)/venv/bin/python
endif
PY.TEST ?= $(VIRTUAL_PYTHON) -m pytest
PIP_INSTALL := $(VIRTUAL_PYTHON) -m pip install --upgrade

ifeq ($(OS),Windows_NT)
    detected_OS := Windows
else
    detected_OS := $(shell uname -s)
endif

.PHONY: all tests clean build


install:
	$(PYTHON) -m pip install $(CODE_DIR)

venv:
ifeq ($(ENFORCE_CLEAN_GIT),true)
	# Ensure git 'trusts' the directory inside docker
	git config --global --add safe.directory $(CODE_DIR)
	$(CODE_DIR)/bin/ensure-clean-working-directory.sh

endif
	$(PYTHON) -m venv venv

tests: venv
	$(PIP_INSTALL) pip
	$(PIP_INSTALL) dist/*.whl
	$(PIP_INSTALL) pytest scipy
	$(PY.TEST) $(CODE_DIR)/tests

build-wheel: build
	$(VIRTUAL_PYTHON) -m build --wheel --outdir $(DISTRIBUTION_DIR)

build-sdist: venv
	$(PIP_INSTALL) build
	PYTHONPATH=$(CODE_DIR):$(PYTHONPATH) \
	$(VIRTUAL_PYTHON) -m build --sdist

build: venv
	$(PIP_INSTALL) build
	PYTHONPATH=$(CODE_DIR):$(PYTHONPATH) \
	$(VIRTUAL_PYTHON) -m build

ifeq ($(detected_OS),Linux)
	# Format wheels to be compatible with PEP 600, PEP 513, PEP 571, and/or PEP 599
	# auditweel have not released an update for Python 3.12 yet, so we install it from main
	$(PIP_INSTALL) git+https://github.com/pypa/auditwheel 2>/dev/null || { \
	    # Fall back to the regual version for older versions of Python, which are no longer supported ; \
	    $(PIP_INSTALL) auditwheel ; \
	}
	for wheel in $(CODE_DIR)/dist/$(shell echo $(NAME) | tr '-' '_')-*.whl ; do \
	    $(VIRTUAL_PYTHON) -m auditwheel repair $$wheel ; \
	done
endif

clean:
	cd $(CODE_DIR) && \
	rm -rf build \
	       venv \
	       dist \
	       .pytest_cache \
	       .numpy.json \
	       *.so


print-%  : ; @echo $($*)
