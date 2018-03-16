NAME = nrlib
VERSION = $(shell ./bin/find-version-of-docker-image.sh)
DOCKER_REGISTRY_SERVER = git.statoil.no:4567
DOCKER_REGISTRY = $(DOCKER_REGISTRY_SERVER)/sdp/nrlib
IMAGE_NAME = $(DOCKER_REGISTRY)/$(NAME):$(VERSION)


CODE_DIR ?= $(shell pwd)
SETUP.PY := $(CODE_DIR)/setup.py

DOCKERFILE := $(CODE_DIR)/Dockerfile

PYTHON ?= $(shell which python)
PIPENV ?= $(PYTHON) -m pipenv
PY.TEST ?= $(PYTHON) -m pytest

DISTRIBUTION_DIR ?= $(CODE_DIR)/dist

NRLIB_LINKING ?= static

docker-image:
	docker build --rm --tag $(IMAGE_NAME) --file $(DOCKERFILE) $(CODE_DIR)

docker-push-image: docker-image
	docker push $(IMAGE_NAME)

docker-login:
	docker login $(DOCKER_REGISTRY_SERVER)

install-wheel:
	$(PIPENV) install -U $(DISTRIBUTION_DIR)/$(shell ls $(DISTRIBUTION_DIR))

install: install-requirements build-boost-python
	NRLIB_LINKING=$(NRLIB_LINKING) \
	CXXFLAGS="-fPIC" \
	$(PYTHON) $(SETUP.PY) build_ext --inplace build install

install-requirements:
	$(PIPENV) --python=$(PYTHON) --site-packages
	$(PIPENV) install --dev

tests:
	$(PY.TEST) $(CODE_DIR)/tests

build: install-requirements build-boost-python
	NRLIB_LINKING=$(NRLIB_LINKING) \
	CXXFLAGS="-fPIC" \
	$(PYTHON) $(SETUP.PY) build_ext --inplace build bdist_wheel --dist-dir $(DISTRIBUTION_DIR)

build-boost-python:
	CODE_DIR=$(CODE_DIR) \
	  $(CODE_DIR)/bootstrap.sh --prefix=$(shell pwd)/build --with-python=$(PYTHON) --with-icu && \
	CPLUS_INCLUDE_PATH=$(shell $(PYTHON) -c "from sysconfig import get_paths; print(get_paths()['include'])") \
	  $(CODE_DIR)/bjam --with-python \
	                   --with-filesystem \
	                   --with-system \
	                   cxxflags=-fPIC \
	                   cflags=-fPIC \
	                   python-debugging=off \
	                   threading=multi \
	                   variant=release \
	                   link=$(NRLIB_LINKING) \
	                   runtime-link=$(NRLIB_LINKING) \
	                   stage

clean:
	rm -rf build \
	       nrlib.egg-info \
	       dist \
	       bin.v2 \
	       .pytest_cache \
	       project-config.jam* \
	       b2 \
	       bjam \
	       bootstrap.log \
	       *.so
