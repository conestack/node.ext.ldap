# -*- coding: utf-8 -*-
from node.events import NodeAddedEvent
from node.events import NodeCreatedEvent
from node.events import NodeDetachedEvent
from node.events import NodeModifiedEvent
from node.events import NodeRemovedEvent
from node.ext.ldap.interfaces import ILDAPNodeAddedEvent
from node.ext.ldap.interfaces import ILDAPNodeCreatedEvent
from node.ext.ldap.interfaces import ILDAPNodeDetachedEvent
from node.ext.ldap.interfaces import ILDAPNodeModifiedEvent
from node.ext.ldap.interfaces import ILDAPNodeRemovedEvent
from zope.interface import implementer


@implementer(ILDAPNodeCreatedEvent)
class LDAPNodeCreatedEvent(NodeCreatedEvent):
    pass


@implementer(ILDAPNodeAddedEvent)
class LDAPNodeAddedEvent(NodeAddedEvent):
    pass


@implementer(ILDAPNodeModifiedEvent)
class LDAPNodeModifiedEvent(NodeModifiedEvent):
    pass


@implementer(ILDAPNodeRemovedEvent)
class LDAPNodeRemovedEvent(NodeRemovedEvent):
    pass


@implementer(ILDAPNodeDetachedEvent)
class LDAPNodeDetachedEvent(NodeDetachedEvent):
    pass
