# -*- coding: utf-8 -*-
from zope.interface import implements
from node.events import (
    NodeCreatedEvent,                  
    NodeAddedEvent,
    NodeModifiedEvent,
    NodeRemovedEvent,
    NodeDetachedEvent
)
from .interfaces import (
    ILDAPNodeCreatedEvent,
    ILDAPNodeAddedEvent,
    ILDAPNodeModifiedEvent,
    ILDAPNodeRemovedEvent,
    ILDAPNodeDetachedEvent,
)


class LDAPNodeCreatedEvent(NodeCreatedEvent):
    implements(ILDAPNodeCreatedEvent)
  
    
class LDAPNodeAddedEvent(NodeAddedEvent):
    implements(ILDAPNodeAddedEvent)


class LDAPNodeModifiedEvent(NodeModifiedEvent):
    implements(ILDAPNodeModifiedEvent)


class LDAPNodeRemovedEvent(NodeRemovedEvent):              
    implements(ILDAPNodeRemovedEvent)


class LDAPNodeDetachedEvent(NodeRemovedEvent):
    implements(ILDAPNodeDetachedEvent)