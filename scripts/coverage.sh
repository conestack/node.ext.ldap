#!/bin/bash
source ./scripts/env.sh

setenv

$PYTHON_BIN --version
$COVERAGE_BIN run \
    --source=src/node/ext/ldap \
    --omit=src/node/ext/ldap/main.py \
    -m node.ext.ldap.tests.__init__

$COVERAGE_BIN report --fail-under=99

unsetenv

exit 0
