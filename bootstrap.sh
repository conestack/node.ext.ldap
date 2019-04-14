#!/bin/bash
set -e
if [ -x "$(which python)" ]; then
    rm -r py2
    virtualenv --clear --no-site-packages -p python py2
    cd py2
    cp ../ldap.cfg .
    cp ../versions.cfg .
    cp ../base.cfg .
    cp ../buildout.cfg .
    ./bin/pip install --upgrade pip setuptools zc.buildout
    ./bin/buildout
    cd ..
fi
if [ -x "$(which python3)" ]; then
    rm -r py3
    virtualenv --clear --no-site-packages -p python3 py3
    cd py3
    cp ../ldap.cfg .
    cp ../versions.cfg .
    cp ../base.cfg .
    cp ../buildout.cfg .
    ./bin/pip install --upgrade pip setuptools zc.buildout
    ./bin/buildout
    cd ..
fi
