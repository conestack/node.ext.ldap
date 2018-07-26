# -*- coding: utf-8 -*-
from node.ext.ldap.interfaces import ILDAPProps
from zope.interface import implementer


MULTIVALUED_DEFAULTS = set([
    'member',
    'uniqueMember',
    'memberUid',
    'memberOf'
])


BINARY_DEFAULTS = set([
    # core.schema
    'userCertificate',
    'cACertificate',
    'authorityRevocationList',
    'certificateRevocationList',
    'crossCertificatePair',
    'supportedAlgorithms',
    'deltaRevocationList',
    # inetOrgPerson
    'userSMIMECertificate',
    'userPKCS12',
    'photo',
    'jpegPhoto',
    # active directory
    'objectSid',
    'objectGUID'
])


@implementer(ILDAPProps)
class LDAPServerProperties(object):
    """Wrapper Class for LDAP Server connection properties.
    """

    def __init__(
        self,
        server=None,
        port=None,
        user='',
        password='',
        cache=True,  # XXX: default False
        timeout=43200,
        uri=None,
        start_tls=0,
        ignore_cert=0,
        tls_cacertfile=None,
        # tls_cacertdir=None,
        # tls_clcertfile=None,
        # tls_clkeyfile=None,
        retry_max=1,
        retry_delay=10.0,
        multivalued_attributes=MULTIVALUED_DEFAULTS,
        binary_attributes=BINARY_DEFAULTS,
        page_size=1000):
        """Take the connection properties as arguments.

        SSL/TLS still unsupported.

        :param server: DEPRECATED use uri! servername, defaults to 'localhost'
        :param port: DEPRECATED uss uri! server port, defaults to 389
        :param user: Username to bind, defaults to ''
        :param password: Password to bind, defaults to ''
        :param cache: Bool wether to enable caching or not, defaults to True
        :param timeout: Cache timeout in seconds. only takes affect if cache is
            enabled.
        :param uri: Overrides server/port, forget about server and port, use
            this to specify how to access the ldap server, eg:
                - ldapi:///path/to/socket
                - ldap://<server>:<port> (will try start_tls, which you can
                  enforce, see start_tls)
                - ldaps://<server>:<port>
        :param start_tls: Determines if StartTLS extended operation is tried on
            a LDAPv3 server, if the LDAP URL scheme is ldap:. If LDAP URL
            scheme is not 'ldap:' (e.g. 'ldaps:' or 'ldapi:') this parameter
            is ignored.
                0 - Don't use StartTLS ext op
                1 - Try StartTLS ext op but proceed when unavailable
                2 - Try StartTLS ext op and re-raise exception if it fails
        :param ignore_cert: Ignore TLS/SSL certificate errors. Useful for
            self-signed certificates. Defaults to False
        :param tls_cacertfile: Provide a specific CA Certifcate file. This is
            needed if the CA is not in the default CA keyring (i.e. with
            self-signed certificates). Under Windows its possible that
            python-ldap lib does recognize the system keyring.
        :param tls_cacertdir: Not yet
        :param tls_clcertfile: Not yet
        :param tls_clkeyfile: Not yet
        :param retry_max: Maximum count of reconnect trials. Value has to be >= 1
        :param retry_delay: Time span to wait between two reconnect trials.
        :param multivalued_attributes: Set of attributes names considered as
            multivalued to be returned as list.
        :param binary_attributes: Set of attributes names considered as binary.
            (no unicode conversion)
        :param page_size: Oage size for LDAP search requests, defaults to 1000.
            Number of objects requested at once.
            In iterations after this number of objects a new search query is
            sent for the next batch using returned the LDAP cookie.
        """
        if uri is None:
            # old school
            self.server = server or 'localhost'
            self.port = port or 389
            uri = "ldap://%s:%d/" % (self.server, self.port)
        self.uri = uri
        self.user = user
        self.password = password
        self.cache = cache
        self.timeout = timeout
        self.start_tls = start_tls
        self.ignore_cert = ignore_cert
        self.tls_cacertfile = tls_cacertfile
        # self.tls_cacertdir = tls_cacertdir
        # self.tls_clcertfile = tls_clcertfile
        # self.tls_clkeyfile = tls_clkeyfile
        self.retry_max = retry_max
        self.retry_delay = retry_delay
        self.multivalued_attributes = multivalued_attributes
        self.binary_attributes = binary_attributes
        self.page_size = page_size

# B/C
LDAPProps = LDAPServerProperties
