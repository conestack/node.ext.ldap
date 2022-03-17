#!/bin/bash
source ./scripts/env.sh

setenv

venv/bin/coverage run \
    --source=src/node/ext/ldap \
    -m zope.testrunner --auto-color --auto-progress \
    --test-path=src \

venv/bin/coverage report

unsetenv

exit 0
