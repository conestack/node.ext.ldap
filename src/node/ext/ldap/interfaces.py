# -*- coding: utf-8 -*-
from node.interfaces import INodeAddedEvent
from node.interfaces import INodeCreatedEvent
from node.interfaces import INodeDetachedEvent
from node.interfaces import INodeModifiedEvent
from node.interfaces import INodeRemovedEvent
from node.interfaces import IStorage
from zope.interface import Attribute
from zope.interface import Interface


class ICacheProviderFactory(Interface):
    """Create some ICacheProvider implementing object on __call__.

    Must be registered as utility.
    """
    def __call__():
        """See above.
        """


class ILDAPProps(Interface):
    """LDAP properties configuration interface.
    """

    uri = Attribute(u'LDAP URI')

    user = Attribute(u'LDAP User')

    password = Attribute(u'Bind Password')

    cache = Attribute(u'Flag wether to use cache or not')

    timeout = Attribute(u'Timeout in seconds')

    start_tls = Attribute(u'TLS enabled')

    ignore_cert = Attribute(u'Ignore TLS/SSL certificate errors')

    tls_cacertfile = Attribute(u'Name of CA Cert file')

    tls_cacertdir = Attribute(u'Path to CA Cert directory')  # unused

    tls_clcertfile = Attribute(u'Name of CL Cert file')  # unused

    tls_clkeyfile = Attribute(u'Path to CL key file')  # unused

    retry_max = Attribute(u'Retry count')

    retry_delay = Attribute(u'Retry delay in seconds')

    multivalued_attributes = Attribute(u'Attributes considered multi valued')

    binary_attributes = Attribute(u'Attributes considered binary')

    page_size = Attribute(u'Page size for LDAP queries.')


class ILDAPPrincipalsConfig(Interface):
    """LDAP principals configuration interface.
    """

    baseDN = Attribute(u'Principals base DN')

    attrmap = Attribute(u'Principals Attribute map as ``odict.odict``')

    scope = Attribute(u'Search scope for principals')

    queryFilter = Attribute(u'Search Query filter for principals')

    # XXX
    # member_relation = Attribute(u'Optional member relation to be used to '
    #                             u'speed up groups search, i.e. '
    #                             u''uid:memberUid'')

    objectClasses = Attribute(u'Object classes for new principals.')

    defaults = Attribute(
        u'Dict like object containing default values for principal creation.'
        u'A value could either be static or a callable. This defaults take'
        u'precedence to defaults detected via set object classes.'
    )

    strict = Attribute(
        u'Flag whether to initialize Aliaser for LDAP attributes in strict '
        u'mode. Defaults to True.'
    )

    memberOfSupport = Attribute(
        u'Flag whether to use "memberOf" attribute (AD) or memberOf overlay '
        u'(openldap) for Group membership resolution where appropriate.'
    )

    # XXX: currently expiresAttr only gets considered for user authentication
    #      group and role expiration is not implemented yet.
    expiresAttr = Attribute(
        u'Attribute containing an expiration timestamp from epoch in UTC. '
        u'If None, entry never expires.'
    )

    expiresUnit = Attribute(
        u'Expiration unit. Either ``node.ext.ldap.ugm.EXPIRATION_DAYS`` or '
        u'``EXPIRATION_SECONDS``. defaults to days.'
    )


class ILDAPUsersConfig(ILDAPPrincipalsConfig):
    """LDAP users configuration interface.
    """


class ILDAPGroupsConfig(ILDAPPrincipalsConfig):
    """LDAP groups configuration interface.
    """


class ILDAPStorage(IStorage):
    """A LDAP Node.
    """

    ldap_session = Attribute(
        u'``node.ext.ldap.session.LDAPSession`` instance.'
    )

    DN = Attribute(u'LDAP object DN.')

    # rdn_attr = Attribute(u'RDN attribute name.')

    changed = Attribute(u'Flag whether node has been modified.')

    search_scope = Attribute(u'Default child search scope')

    search_filter = Attribute(u'Default child search filter')

    search_criteria = Attribute(u'Default child search criteria')

    search_relation = Attribute(u'Default child search relation')

    child_defaults = Attribute(
        u'Default child attributes. Will be set to all children attributes'
        u'on __setitem__ if not present yet.'
    )

    def child_dn(key):
        """Return child DN for ``key``.
        """

    def search(queryFilter=None, criteria=None, relation=None,
               attrlist=None, exact_match=False, or_search=False):
        """Search the directors.

        All search criteria are additive and will be ``&``ed. ``queryFilter``
        and ``criteria`` further narrow down the search space defined by
        ``self.search_filter``, ``self.search_criteria`` and
        ``self.search_relation``.

        Returns a list of matching keys if ``attrlist`` is None, otherwise a
        list of 2-tuples containing (key, attrdict).

        queryFilter
            ldap queryFilter, e.g. ``(objectClass=foo)``, as string or
            LDAPFilter instance.

        criteria
            dictionary of attribute value(s) (string or list of string)

        relation
            the nodes we search has a relation to us.  A relation is defined as
            a string of attribute pairs:
            ``<relation> = '<our_attr>:<child_attr>'``.
            The value of these attributes must match for relation to match.
            Multiple pairs can be or-joined with.

        attrlist
            Normally a list of keys is returned. By defining attrlist the
            return format will be ``[(key, {attr1: [value1, ...]}), ...]``. To
            get this format without any attributs, i.e. empty dicts in the
            tuples, specify an empty attrlist. In addition to the normal ldap
            attributes you can also the request the DN to be included. DN is
            also the only value in result set as string instead of list.

        exact_match
            raise ValueError if not one match, return format is a single key or
            tuple, if attrlist is specified.

        or_search
            flag whether criteria should be ORer or ANDed. defaults to False.
        """


###############################################################################
# events
###############################################################################


class ILDAPNodeCreatedEvent(INodeCreatedEvent):
    """new LDAP node was born.
    """


class ILDAPNodeAddedEvent(INodeAddedEvent):
    """LDAP node has been added to its parent.
    """


class ILDAPNodeModifiedEvent(INodeModifiedEvent):
    """LDAP node has been modified.
    """


class ILDAPNodeRemovedEvent(INodeRemovedEvent):
    """LDAP node has been removed from its parent.
    """


class ILDAPNodeDetachedEvent(INodeDetachedEvent):
    """LDAP node has been detached from its parent.
    """
