#!/bin/bash
set -e

function cleanup() {
    if [ -e "$1" ]; then
        rm -rf $1
    fi
}

function create_venv() {
    virtualenv --clear --no-site-packages -p $1 $2
}

function copy_config() {
    cp ../ldap.cfg .
    cp ../versions.cfg .
    cp ../base.cfg .
    cp ../buildout.cfg .
}

function run_buildout() {
    pushd $1
    copy_config
    ./bin/pip install --upgrade pip setuptools zc.buildout
    ./bin/buildout
    popd
}

if [ -x "$(which python)" ]; then
    cleanup py2
    create_venv python py2
    run_buildout py2
fi

if [ -x "$(which python3)" ]; then
    cleanup py3
    create_venv python3 py3
    run_buildout py3
fi
