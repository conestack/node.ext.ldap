#!/bin/sh

./$1/bin/coverage run --source=./src/node/ext/ldap ./$1/bin/test
./$1/bin/coverage report
./$1/bin/coverage html
