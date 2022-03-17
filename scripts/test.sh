#!/bin/bash
source ./scripts/env.sh

setenv

venv/bin/python  -m node.ext.ldap.tests.__init__

unsetenv

exit 0
