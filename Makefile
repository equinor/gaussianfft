NAME = nrlib
VERSION = 1.1.2
IMAGE_NAME = $(NAME):$(VERSION)

BOOST_VERSION = 1.59.0
BOOST_PREFIX = boost_$(shell echo $(BOOST_VERSION) | tr "." "_")

docker-image:
	docker build --rm --tag $(IMAGE_NAME) -f Dockerfile .

install: install-requirements
	pip install --user -e .

# && python setup.py build_ext -I$GCC_PREFIX/include/c++/$GCC_VERSION/parallel:$GCC_PREFIX/include/c++/$GCC_VERSION/tr1


install-requirements:
	pip install -r requirements.txt

get-boost:
	wget https://sourceforge.net/projects/boost/files/boost/$(BOOST_VERSION)/$(BOOST_PREFIX).tar.bz2

tests:
	pip install pytest
	pytest tests
