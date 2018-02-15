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

ifeq ($(DISTRIBUTION_DIR),)
DISTRIBUTION_DIR := $(CODE_DIR)/dist
endif

PIP := $(shell dirname $(PYTHON))/pip

docker-image:
	docker build --rm --tag $(IMAGE_NAME) --file $(DOCKERFILE) $(CODE_DIR)

docker-push-image: docker-login docker-image
	docker push $(IMAGE_NAME)

docker-login:
	docker login $(DOCKER_REGISTRY_SERVER)

install: install-requirements build
	$(PIP) install -e $(CODE_DIR)

install-requirements:
	$(PIP) install -r $(CODE_DIR)/requirements.txt

#get-boost:
#	curl -L https://sourceforge.net/projects/boost/files/boost/$(BOOST_VERSION)/$(BOOST_PREFIX).tar.bz2 -o $(BOOST_PREFIX).tar.bz2
#	tar -xvf $(BOOST_PREFIX).tar.bz2
#	# TODO: export CPLUS_INCLUDE_PATH=/Users/snis/Projects/APS/GUI/venv/include/python3.6m
#	# TODO: ./bjam --with-python --with-filesystem --with-system python-debugging=off threading=multi variant=release link=shared <somwhere?>

tests: pytest-instalation
	pytest $(CODE_DIR)/tests

pytest-instalation:
	[[ ! type pytest 2>/dev/null ]] && $(PIP) install pytest

build: build-boost-python
	$(PYTHON) $(CODE_DIR)/setup.py bdist_wheel --relative --dist-dir $(DISTRIBUTION_DIR)

build-boost-python:
	$(CODE_DIR)/bootstrap.sh --prefix=$(shell pwd)/build --with-python=$(PYTHON) --with-icu
	CPLUS_INCLUDE_PATH=$(shell dirname $(PYTHON))/../include/python3.6m \
	$(CODE_DIR)/bjam --with-python --with-filesystem --with-system python-debugging=off threading=multi variant=release link=shared stage

#artifacts:
#	mkdir -p $ARTIFACTS
#	mv $CI_PROJECT_DIR/$GUI_FILE $ARTIFACTS
#	du -sh $ARTIFACTS
