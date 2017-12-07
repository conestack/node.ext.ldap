#!/bin/sh

# see https://community.plone.org/t/not-using-bootstrap-py-as-default/620
for dir in lib include local bin; do
    if [ -d "$dir" ]; then
        rm -r "$dir"
    fi
done
virtualenv --clear .
./bin/pip install --upgrade pip setuptools zc.buildout
./bin/buildout
