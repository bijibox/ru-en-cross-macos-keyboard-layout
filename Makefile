.PHONY: build icons test test-macos install clean

PYTHON ?= python3

build:
	$(PYTHON) ru_en_cross.py build

icons:
	mkdir -p build/swift-module-cache
	xcrun swift -module-cache-path build/swift-module-cache tools/generate_icons.swift

test:
	$(PYTHON) -m unittest discover -s tests

test-macos:
	$(PYTHON) tools/check_macos.py

install:
	$(PYTHON) ru_en_cross.py install

clean:
	$(PYTHON) ru_en_cross.py clean
