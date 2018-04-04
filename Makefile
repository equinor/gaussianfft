NAME = nrlib
VERSION = $(shell ./bin/find-version-of-docker-image.sh)
DOCKER_REGISTRY_SERVER = git.statoil.no:4567
DOCKER_REGISTRY = $(DOCKER_REGISTRY_SERVER)/sdp/nrlib
IMAGE_NAME = $(DOCKER_REGISTRY)/$(NAME):$(VERSION)


CODE_DIR ?= $(shell pwd)
SETUP.PY := $(CODE_DIR)/setup.py

DOCKERFILE := $(CODE_DIR)/Dockerfile

TIMEOUT := timeout -s INT 3m
PYTHON ?= $(shell which python)
PIP ?= $(PYTHON) -m pip
PIPENV ?= $(PYTHON) -m pipenv
PY.TEST ?= $(TIMEOUT) $(PIPENV) run pytest
VIRTUAL_PYTHON := $(shell $(PIPENV) run which python)

DISTRIBUTION_DIR ?= $(CODE_DIR)/dist

NRLIB_LINKING ?= static

PYPI_SERVER ?= http://pypi.aps.statoil.no:8080
PYPI_NAME := statoil

define PYPIRC
[distutils]
index-servers =
    $(PYPI_NAME)

[$(PYPI_NAME)]
repository: $(PYPI_SERVER)
username: $(PYPI_USER)
password: $(PYPI_PASSWORD)
endef
export PYPIRC

.PHONY: all tests clean

docker-image:
	docker build --pull --rm --tag $(IMAGE_NAME) --file $(DOCKERFILE) $(CODE_DIR)

docker-push-image: docker-image
	docker push $(IMAGE_NAME)

docker-login:
	docker login $(DOCKER_REGISTRY_SERVER)

check-requirements: install-pipenv
	$(PIPENV) check

install-wheel:
	$(PIPENV) install $(DISTRIBUTION_DIR)/$(shell ls $(DISTRIBUTION_DIR)) || $(PIP) install -U $(DISTRIBUTION_DIR)/$(shell ls $(DISTRIBUTION_DIR))

install: install-requirements build-boost-python
	NRLIB_LINKING=$(NRLIB_LINKING) \
	CXXFLAGS="-fPIC" \
	$(PYTHON) $(SETUP.PY) build_ext --inplace build install

install-requirements: install-pipenv create-virtual-env
	$(PIPENV) install --dev

create-virtual-env:
	$(PIPENV) --python=$(PYTHON) --site-packages

install-pipenv:
	$(PIP) install 'pipenv<11'

tests:
	$(PY.TEST) $(CODE_DIR)/tests

upload: pypirc
	$(PYTHON) $(SETUP.PY) register -r $(PYPI_NAME) upload -r $(PYPI_NAME)

pypirc:
	echo "$$PYPIRC" > $(CODE_DIR)/.pypirc

build: install-requirements build-boost-python
	NRLIB_LINKING=$(NRLIB_LINKING) \
	CXXFLAGS="-fPIC" \
	$(PYTHON) $(SETUP.PY) build_ext --inplace build bdist_wheel --dist-dir $(DISTRIBUTION_DIR)

build-boost-python:
	CODE_DIR=$(CODE_DIR) \
	  $(CODE_DIR)/bootstrap.sh \
	                   --prefix=$(shell pwd)/build \
	                   --with-python=$(VIRTUAL_PYTHON) \
	                   --with-icu && \
	CPLUS_INCLUDE_PATH=$(shell $(VIRTUAL_PYTHON) -c "from sysconfig import get_paths; print(get_paths()['include'])") \
	  $(CODE_DIR)/bjam --with-python \
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

clean:
	cd $(CODE_DIR) && \
	rm -rf build \
	       nrlib.egg-info \
	       dist \
	       bin.v2 \
	       .pytest_cache \
	       project-config.jam* \
	       b2 \
	       bjam \
	       bootstrap.log \
	       .pypirc \
	       *.so
