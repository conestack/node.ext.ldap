#!/bin/bash
source ./scripts/env.sh

setenv

venv/bin/zope-testrunner --auto-color --auto-progress \
    --test-path=sources/node.ext.ldap/src \
    --module=$1

unsetenv

exit 0
