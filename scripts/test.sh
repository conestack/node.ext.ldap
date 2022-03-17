#!/bin/bash
source ./scripts/env.sh

setenv

#PYTHON_BIN=venv/bin/python
PYTHON_BIN=python

$PYTHON_BIN --version
$PYTHON_BIN -m node.ext.ldap.tests.__init__

unsetenv

exit 0
