#!/bin/bash
set -e

function setenv() {
    export TESTRUN_MARKER="1"
    export LDAP_ADD_BIN="openldap/bin/ldapadd"
    export LDAP_DELETE_BIN="openldap/bin/ldapdelete"
    export SLAPD_BIN="openldap/libexec/slapd"
    export SLAPD_URIS="ldap://127.0.0.1:12345"
    export ADDITIONAL_LDIF_LAYERS=""
}

function unsetenv() {
    unset TESTRUN_MARKER
    unset LDAP_ADD_BIN
    unset LDAP_DELETE_BIN
    unset SLAPD_BIN
    unset SLAPD_URIS
    unset ADDITIONAL_LDIF_LAYERS
}

trap unsetenv ERR INT
