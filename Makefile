NAME = nrlib
VERSION = $(shell ./bin/find-version-of-docker-image.sh)
DOCKER_REGISTRY = git.statoil.no:4567/sdp/nrlib
IMAGE_NAME = $(DOCKER_REGISTRY)/$(NAME):$(VERSION)

BOOST_VERSION = 1.65.1
BOOST_PREFIX = boost_$(shell echo $(BOOST_VERSION) | tr "." "_")

# TODO: check whether PIP is set
PIP := pip

docker-image:
	docker build --rm --tag $(IMAGE_NAME) -f Dockerfile .

install: install-requirements
	$(PIP) install -e .

install-requirements:
	$(PIP) install -r requirements.txt

get-boost:
	curl -L https://sourceforge.net/projects/boost/files/boost/$(BOOST_VERSION)/$(BOOST_PREFIX).tar.bz2 -o $(BOOST_PREFIX).tar.bz2
	tar -xvf $(BOOST_PREFIX).tar.bz2
	# TODO: export CPLUS_INCLUDE_PATH=/Users/snis/Projects/APS/GUI/venv/include/python3.6m
	# TODO: ./bjam --with-python --with-filesystem --with-system python-debugging=off threading=multi variant=release link=shared <somwhere?>

tests: pytest-instalation
	pytest tests

pytest-instalation:
	[[ ! type pytest 2>/dev/null ]] && $(PIP) install pytest

build:

artifacts:
	mkdir -p $ARTIFACTS
	mv $CI_PROJECT_DIR/$GUI_FILE $ARTIFACTS
	du -sh $ARTIFACTS
