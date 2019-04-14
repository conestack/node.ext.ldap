#!/bin/sh
if [ -x "$(which python)" ]; then
    rm -r py2

    virtualenv --clear --no-site-packages -p python py2
    ./py2/bin/pip install --upgrade pip setuptools zc.buildout
    ./py2/bin/buildout
fi
if [ -x "$(which python3)" ]; then
    rm -r py3

    virtualenv --clear --no-site-packages -p python3 py3
    ./py3/bin/pip install --upgrade pip setuptools zc.buildout
    ./py3/bin/buildout
fi
