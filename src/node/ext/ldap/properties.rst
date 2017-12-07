# -*- coding: utf-8 -*-

LDAP Properties
===============

Test related imports::

    >>> from node.ext.ldap import LDAPProps
    >>> from node.ext.ldap.properties import MULTIVALUED_DEFAULTS
    >>> from node.ext.ldap.properties import BINARY_DEFAULTS

Defaults::

    >>> assert(MULTIVALUED_DEFAULTS == set([
    ...     'member',
    ...     'memberUid',
    ...     'uniqueMember',
    ...     'memberOf'
    ... ]))

    >>> assert(BINARY_DEFAULTS == set([
    ...     'authorityRevocationList',
    ...     'certificateRevocationList',
    ...     'supportedAlgorithms',
    ...     'photo',
    ...     'deltaRevocationList',
    ...     'cACertificate',
    ...     'userCertificate',
    ...     'userPKCS12',
    ...     'crossCertificatePair',
    ...     'objectSid',
    ...     'userSMIMECertificate',
    ...     'jpegPhoto',
    ...     'objectGUID'
    ... ]))

Test LDAPPropes::

    >>> props = LDAPProps(
    ...     uri='ldap://localhost:12345/',
    ...     user='admin',
    ...     password='secret',
    ... )
    >>> assert(props.uri == 'ldap://localhost:12345/')
    >>> assert(props.user == 'admin')
    >>> assert(props.password == 'secret')
    >>> assert(props.cache is True)
    >>> assert(props.timeout == 43200)
    >>> assert(props.start_tls == 0)
    >>> assert(props.ignore_cert == 0)
    >>> assert(props.tls_cacertfile is None)
    >>> assert(props.retry_max == 1)
    >>> assert(props.retry_delay == 10.)
    >>> assert(props.multivalued_attributes is MULTIVALUED_DEFAULTS)
    >>> assert(props.binary_attributes is BINARY_DEFAULTS)
    >>> assert(props.page_size == 1000)
