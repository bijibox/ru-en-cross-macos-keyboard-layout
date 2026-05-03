.PHONY: build test install clean

PYTHON ?= python3

build:
	$(PYTHON) ru_en_cross.py build

test:
	$(PYTHON) -m unittest discover -s tests

install:
	$(PYTHON) ru_en_cross.py install

clean:
	$(PYTHON) ru_en_cross.py clean
