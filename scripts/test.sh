#!/bin/bash
source ./scripts/env.sh

setenv

$PYTHON_BIN --version
$PYTHON_BIN -m node.ext.ldap.tests.__init__

unsetenv

exit 0
