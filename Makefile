SHELL=/bin/bash
MAKE=make --no-print-directory

install:
	python setup.py install --user

test:
	python -m unittest discover ./pyconfigmanager/test

uninstall:
	pip uninstall pyconfigmanager

.PHONY:
	install uninstall
