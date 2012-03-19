# -*- coding: utf-8 -*-
from zope.interface import implements
from node.ext.ldap.interfaces import ILDAPProps

MULTIVALUED_DEFAULTS = [
    'member', 
    'uniqueMember', 
    'memberUid', 
    'memberOf'
]

BINARY_DEFAULTS = [
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
] 


class LDAPServerProperties(object):
    """Wrapper Class for LDAP Server connection properties.
    """
    implements(ILDAPProps)

    def __init__(self,
                 server=None,
                 port=None,
                 user='',
                 password='',
                 cache=True, # XXX: default False
                 timeout=43200,
                 uri=None,
                 start_tls=0,
                 #tls_cacertfile=None,
                 #tls_cacertdir=None,
                 #tls_clcertfile=None,
                 #tls_clkeyfile=None,
                 retry_max=1,
                 retry_delay=10.0,
                 escape_queries=False,
                 multivalued_attributes=MULTIVALUED_DEFAULTS,
                 binary_attributes=BINARY_DEFAULTS,
                 ):
        """Take the connection properties as arguments.

        SSL/TLS still unsupported

        server
            DEPRECATED use uri! servername, defaults to 'localhost'
            
        port
            DEPRECATED uss uri! server port, defaults to 389
        
        user
            username to bind, defaults to ''
        
        password
            password to bind, defaults to ''
        
        cache
            Bool wether to enable caching or not, defaults to True
        
        timeout
            Cache timeout in seconds. only takes affect if cache is enabled.
        
        uri
            overrides server/port, forget about server and port, use
            this to specify how to access the ldap server, eg:
                - ldapi:///path/to/socket
                - ldap://<server>:<port> (will try start_tls, which you can
                  enforce, see start_tls)
                - ldaps://<server>:<port>
        
        start_tls
            Determines if StartTLS extended operation is tried on
            a LDAPv3 server, if the LDAP URL scheme is ldap:. If LDAP URL 
            scheme is not 'ldap:' (e.g. 'ldaps:' or 'ldapi:') this parameter
            is ignored.
                0 - Don't use StartTLS ext op
                1 - Try StartTLS ext op but proceed when unavailable
                2 - Try StartTLS ext op and re-raise exception if it fails
        
        tls_cacertfile
            Not yet
        
        tls_cacertdir
            Not yet
            
        tls_clcertfile
            Not yet
            
        tls_clkeyfile
            Not yet
            
        retry_max
            Maximum count of reconnect trials
            Not yet
            
        retry_delay
            Time span to wait between two reconnect trials
            Not yet
        
        escape_queries
            Flag whether to escape queries
            
        multivalued_attributes
            List of attributes names considered as multivalued to be returned 
            as list. 

        binary_attributes
            List of attributes names considered as binary. 
            (no unicode conversion)
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
        #self.tls_cacertfile = tls_cacertfile
        #self.tls_cacertdir = tls_cacertdir
        #self.tls_clcertfile = tls_clcertfile
        #self.tls_clkeyfile = tls_clkeyfile
        self.retry_max = retry_max
        self.retry_delay = retry_delay
        self.escape_queries = escape_queries
        self.multivalued_attributes = multivalued_attributes
        self.binary_attributes = binary_attributes

LDAPProps = LDAPServerProperties