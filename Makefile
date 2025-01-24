NAME = gaussianfft

EMPTY :=

CODE_DIR ?= $(shell pwd)

PYTHON ?= $(shell which python3)
ifeq ($(origin VIRTUAL_PYTHON), undefined)
all: venv
VIRTUAL_PYTHON = $(CODE_DIR)/venv/bin/python
endif

ifeq ($(OS),Windows_NT)
    detected_OS := Windows
else
    detected_OS := $(shell uname -s)
endif

.PHONY: all tests clean


install:
	$(PYTHON) -m pip install $(CODE_DIR)

clean:
	cd $(CODE_DIR) && \
	rm -rf build \
	       venv \
	       dist \
	       .pytest_cache \
	       .numpy.json \
	       *.so


print-%  : ; @echo $($*)
