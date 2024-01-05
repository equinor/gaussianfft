NAME = gaussianfft

EMPTY :=

# Use packages provided by a distribution, e.g. RMS
USE_TEST_PYPI ?= yes

PYPI_REPOSITORY := pypi

ifeq ($(USE_TEST_PYPI),yes)
PYPI_REPOSITORY := testpypi
endif


CODE_DIR ?= $(shell pwd)
SETUP.PY := $(CODE_DIR)/setup.py

PYTHON ?= $(shell which python3)
PIP ?= $(PYTHON) -m pip --proxy "$(HTTPS_PROXY)"
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

define PYPIRC
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = $(PYPI_API_TOKEN)

[testpypi]
username = __token__
password = $(PYPI_TEST_API_TOKEN)
endef
export PYPIRC

.PHONY: all tests clean build


install:
	$(PYTHON) -m pip install $(CODE_DIR)

venv:
	$(PYTHON) -m venv venv

tests: venv
	$(PIP_INSTALL) pip
	$(PIP_INSTALL) wheelhouse/*.whl
	$(PIP_INSTALL) pytest scipy
	$(PY.TEST) $(CODE_DIR)/tests

upload: .pypirc venv
	$(PIP_INSTALL) twine
	$(VIRTUAL_PYTHON) -m twine upload \
			--repository $(PYPI_REPOSITORY) \
			--non-interactive \
			--config-file $(CODE_DIR)/.pypirc \
			--verbose \
			$(CODE_DIR)/wheelhouse/*

.pypirc:
	echo "$$PYPIRC" > $(CODE_DIR)/.pypirc

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

	cp $(CODE_DIR)/dist/$(NAME)-*.tar.gz $(CODE_DIR)/wheelhouse
else
	mkdir -p $(CODE_DIR)/wheelhouse
	mv $(CODE_DIR)/dist/* $(CODE_DIR)/wheelhouse/
endif


clean-boost:
	rm -rf $(CODE_DIR)/boost \
	       $(CODE_DIR)/tools \
	       $(CODE_DIR)/libs \
	       $(CODE_DIR)/boost-build.jam \
	       $(CODE_DIR)/boostcpp.jam \
	       $(CODE_DIR)/bootstrap.sh \
	       $(CODE_DIR)/Jamroot \
	       $(CODE_DIR)/project-config.jam* \
	       $(CODE_DIR)/boost_source_files.txt

clean:
	cd $(CODE_DIR) && \
	rm -rf build \
	       venv \
	       nrlib.egg-info \
	       dist \
	       bin.v2 \
	       .pytest_cache \
	       project-config.jam* \
	       b2 \
	       bjam \
	       bootstrap.log \
	       .pypirc \
	       boost_source_files.txt \
	       .numpy.json \
	       pyproject.toml \
	       .pypirc \
	       *.so


print-%  : ; @echo $($*)
