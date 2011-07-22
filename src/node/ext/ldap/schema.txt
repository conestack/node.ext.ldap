############
# XXX: later

    >>> from node.ext.ldap import LDAPProps, LDAPSchemaInfo
    >>> from node.ext.ldap.testing import props
    
    >>> info = LDAPSchemaInfo(props)
    >>> info.baseDN = 'dc=my-domain,dc=com'
    >>> binary = info.binary()
    
    >> for attr in binary:
    ...     print attr.names
    ...     print attr.desc
    ...     print attr.oid
    ('cACertificate',)
    RFC2256: X.509 CA certificate, use ;binary
    2.5.4.37
    ('userCertificate',)
    RFC2256: X.509 user certificate, use ;binary
    2.5.4.36
    ('userPassword',)
    RFC4519/2307: password of user
    2.5.4.35
    ('authorityRevocationList',)
    RFC2256: X.509 authority revocation list, use ;binary
    2.5.4.38
    ('certificateRevocationList',)
    RFC2256: X.509 certificate revocation list, use ;binary
    2.5.4.39
    ('pwdHistory',)
    The history of users passwords
    1.3.6.1.4.1.42.2.27.8.1.20
    ('userSMIMECertificate',)
    RFC2798: PKCS#7 SignedData used to support S/MIME
    2.16.840.1.113730.3.1.40
    ('audio',)
    RFC1274: audio (u-law)
    0.9.2342.19200300.100.1.55
    ('supportedAlgorithms',)
    RFC2256: supported algorithms
    2.5.4.52
    ('deltaRevocationList',)
    RFC2256: delta revocation list; use ;binary
    2.5.4.53
    ('jpegPhoto',)
    RFC2798: a JPEG image
    0.9.2342.19200300.100.1.60
    ('crossCertificatePair',)
    RFC2256: X.509 cross certificate pair, use ;binary
    2.5.4.40
    ('userPKCS12',)
    RFC2798: personal identity information, a PKCS #12 PFX
    2.16.840.1.113730.3.1.216
    ('olcDbCryptKey',)
    DB encryption key
    1.3.6.1.4.1.4203.1.12.2.3.2.1.14
