NAME = nrlib
VERSION = $(shell ./bin/find-version-of-docker-image.sh)
DOCKER_REGISTRY_SERVER = git.statoil.no:4567
DOCKER_REGISTRY = $(DOCKER_REGISTRY_SERVER)/sdp/nrlib
IMAGE_NAME = $(DOCKER_REGISTRY)/$(NAME):$(VERSION)


ifeq ($(CODE_DIR),)
CODE_DIR := $(shell pwd)
endif

DOCKERFILE := $(CODE_DIR)/Dockerfile

ifeq ($(PYTHON),)
PYTHON := $(shell which python)
endif
ifeq ($(PIP),)
PIP := $(shell dirname $(PYTHON))/pip
endif

ifeq ($(DISTRIBUTION_DIR),)
DISTRIBUTION_DIR := $(CODE_DIR)/dist
endif

BOOST_LINKING ?= static

docker-image:
	docker build --rm --tag $(IMAGE_NAME) --file $(DOCKERFILE) $(CODE_DIR)

docker-push-image: docker-image
	docker push $(IMAGE_NAME)

docker-login:
	docker login $(DOCKER_REGISTRY_SERVER)

install: build
	$(PIP) install -e $(CODE_DIR)

install-requirements:
	$(PIP) install --user -r $(CODE_DIR)/requirements.txt || $(PIP) install -r $(CODE_DIR)/requirements.txt

tests: pytest-instalation
	pytest $(CODE_DIR)/tests

pytest-instalation:
	type pytest 2>/dev/null || { $(PIP) install pytest; }

build: install-requirements build-boost-python
	BOOST_LINKING=$(BOOST_LINKING) \
	$(PYTHON) $(CODE_DIR)/setup.py bdist_wheel --dist-dir $(DISTRIBUTION_DIR)

build-boost-python:
	CODE_DIR=$(CODE_DIR) \
	  $(CODE_DIR)/bootstrap.sh --prefix=$(shell pwd)/build --with-python=$(PYTHON) --with-icu && \
	CPLUS_INCLUDE_PATH=$(shell python -c "from sysconfig import get_paths; print(get_paths()['include'])") \
	  $(CODE_DIR)/bjam --with-python \
	                   --with-filesystem \
	                   --with-system \
	                   python-debugging=off \
	                   threading=multi \
	                   variant=release \
	                   link=shared \
	                   stage
