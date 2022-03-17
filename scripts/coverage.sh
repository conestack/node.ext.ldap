#!/bin/bash
source ./scripts/env.sh

setenv

venv/bin/coverage run \
    --source=src/node/ext/ldap \
    --omit=src/node/ext/ldap/main.py \
    -m node.ext.ldap.tests.__init__

venv/bin/coverage report --fail-under=99

unsetenv

exit 0
