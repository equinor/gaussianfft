NAME = gaussianfft

EMPTY :=

# Use packages provided by a distribution, e.g. RMS
USE_SITE_PACKAGES ?= yes
USE_USER_INSTALL ?= no
USE_SKIP_LOCKING ?= no
USE_TEST_PYPI ?= yes

SITE_PACAGES_OPTION := $(EMPTY)
KEEP_OUTDATED := $(EMPTY)
USER_INSTALL := $(EMPTY)
SKIP_LOCKING := $(EMPTY)
PYPI_REPOSITORY := pypi

ifeq ($(USE_SITE_PACKAGES),yes)
SITE_PACAGES_OPTION := --site-packages
KEEP_OUTDATED := --keep-outdated
USER_INSTALL := --user
else
# Override user installation
ifeq ($(USE_USER_INSTALL),yes)
USER_INSTALL := --user
endif
endif

ifeq ($(USE_SKIP_LOCKING),yes)
SKIP_LOCKING := --skip-lock
endif

ifeq ($(USE_TEST_PYPI),yes)
PYPI_REPOSITORY := testpypi
endif


CODE_DIR ?= $(shell pwd)
SETUP.PY := $(CODE_DIR)/setup.py

BOOST_VERSION ?= 1.76.0
BOOST_DIR := $(CODE_DIR)/sources/boost/$(BOOST_VERSION)
BOOST_ARCHIVE := $(BOOST_DIR).tar.gz

PYTHON ?= $(shell which python3)
PIP ?= $(PYTHON) -m pip --proxy "$(HTTPS_PROXY)"
ifeq ($(origin VIRTUAL_PYTHON), undefined)
all: venv
VIRTUAL_PYTHON = $(CODE_DIR)/venv/bin/python
endif
PY.TEST ?= $(VIRTUAL_PYTHON) -m pytest
PIP_INSTALL := $(VIRTUAL_PYTHON) -m pip install --upgrade
MINIMUM_NUMPY_VERSION ?= $(shell $(PYTHON) $(CODE_DIR)/bin/find_lowest_supported_numpy.py)

ifeq ($(OS),Windows_NT)
    detected_OS := Windows
else
    detected_OS := $(shell uname -s)
endif

NRLIB_LINKING ?= static

define PYPROJECT_TOML
[build-system]
requires = [
    "setuptools>=42",
    "wheel",
    # We use the oldest compatible version, to make life easier with Emerson RMS
    # If we use a newer version, the compilation of Boost.Python, will cause the module to crach
    # (segmentation fault) when imported
    "numpy==$(MINIMUM_NUMPY_VERSION)",
    "mkl-devel",
    "mkl-static",
]
build-backend = "setuptools.build_meta"
endef
export PYPROJECT_TOML

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


install: build-boost-python
	NRLIB_LINKING=$(NRLIB_LINKING) \
	CXXFLAGS="-fPIC" \
	$(PYTHON) $(SETUP.PY) build_ext --inplace build install

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

pyproject.toml:
	echo "$$PYPROJECT_TOML" > $(CODE_DIR)/pyproject.toml

build-wheel: build
	$(VIRTUAL_PYTHON) $(SETUP.PY) bdist_wheel --dist-dir $(DISTRIBUTION_DIR)

build-sdist: venv boost pyproject.toml
	$(PIP_INSTALL) build
	PYTHONPATH=$(CODE_DIR):$(PYTHONPATH) \
	$(VIRTUAL_PYTHON) -m build --sdist

build: venv boost pyproject.toml
	$(PIP_INSTALL) build
	NRLIB_LINKING=$(NRLIB_LINKING) \
	CXXFLAGS="-fPIC -fpermissive" \
	PYTHONPATH=$(CODE_DIR):$(PYTHONPATH) \
	$(VIRTUAL_PYTHON) -m build

ifeq ($(detected_OS),Linux)
	# Format wheels to be compatible with PEP 600, PEP 513, PEP 571, and/or PEP 599
	$(PIP_INSTALL) auditwheel
	for wheel in $(CODE_DIR)/dist/$(shell echo $(NAME) | tr '-' '_')-*.whl ; do \
	    $(VIRTUAL_PYTHON) -m auditwheel repair $$wheel ; \
	done

	cp $(CODE_DIR)/dist/$(NAME)-*.tar.gz $(CODE_DIR)/wheelhouse
else
	mv $(CODE_DIR)/dist $(CODE_DIR)/wheelhouse
endif


build-boost-python: venv boost _build-boost-python

_build-boost-python:
	CODE_DIR=$(CODE_DIR) \
	  $(CODE_DIR)/bootstrap.sh \
	                   --prefix=$(shell pwd)/build \
	                   --with-python=$(VIRTUAL_PYTHON) \
	                   --with-icu && \
	CPLUS_INCLUDE_PATH=$(shell $(VIRTUAL_PYTHON) -c "from sysconfig import get_paths; print(get_paths()['include'])") \
	  $(CODE_DIR)/b2   --with-python \
	                   --with-filesystem \
	                   --with-system \
	                   -q \
	                   cxxflags=-fPIC \
	                   cflags=-fPIC \
	                   python-debugging=off \
	                   threading=multi \
	                   variant=release \
	                   link=$(NRLIB_LINKING) \
	                   runtime-link=$(NRLIB_LINKING) \
	                   stage

boost: $(BOOST_ARCHIVE) $(BOOST_DIR)

$(BOOST_ARCHIVE):
	mkdir -p $(CODE_DIR)/sources/boost
	curl -L --output $(BOOST_DIR).tar.gz \
	https://boostorg.jfrog.io/artifactory/main/release/$(BOOST_VERSION)/source/boost_$(shell echo $(BOOST_VERSION) | tr '.' '_').tar.gz

$(BOOST_DIR):
	mkdir -p $(BOOST_DIR)
	tar -xvf $(BOOST_ARCHIVE) -C $(BOOST_DIR) --strip-components=1

	# Remove unnecessary files, some of these are binary, and others are encoded in an encoding incompatible with UTF-8
	rm -rf $(shell find $(BOOST_DIR) -name 'doc' -type d)
	rm -rf $(shell find $(BOOST_DIR) -name 'test' -type d)
	rm -f  $(shell find $(BOOST_DIR) -name '*.html' -type f)

	cp -r $(BOOST_DIR)/boost $(CODE_DIR)

	# Copy necessary 'libs' files
	mkdir -p $(CODE_DIR)/libs
	for item in config filesystem headers python system Jamfile.v2 ; do \
		cp -r $(BOOST_DIR)/libs/$$item $(CODE_DIR)/libs ; \
	done

	# Copy necessary bootstrapping files
	for item in tools boost-build.jam boostcpp.jam bootstrap.sh Jamroot ; do \
		cp -r $(BOOST_DIR)/$$item $(CODE_DIR) ; \
	done

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
