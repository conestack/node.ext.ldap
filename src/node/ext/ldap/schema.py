# -*- coding: utf-8 -*-
from node.ext.ldap import LDAPCommunicator
from node.ext.ldap import LDAPConnector
import ldap


class LDAPSchemaInfo(object):

    def __init__(self, props=None):
        self._props = props

    @property
    def subschema(self):
        if hasattr(self, '_subschema'):
            return self._subschema
        connector = LDAPConnector(props=self._props)
        communicator = LDAPCommunicator(connector)
        communicator.bind()
        res = communicator.search('(objectclass=*)', ldap.SCOPE_BASE,
                                  'cn=subschema', attrlist=['*', '+'])
        if len(res) != 1:
            raise ValueError('subschema not found')
        self._subschema = ldap.schema.SubSchema(ldap.cidict.cidict(res[0][1]))
        return self._subschema

    def attribute(self, name):
        return self.subschema.get_obj(ldap.schema.AttributeType, name)

    def objectclass(self, name):
        return self.subschema.get_obj(ldap.schema.ObjectClass, name)

    def attributes_of_objectclass(self, name):
        res = list()
        oc = self.objectclass(name)
        for at in oc.must:
            record = dict()
            record['name'] = at
            record['required'] = True
            record['info'] = self.attribute(at)
            res.append(record)
        for at in oc.may:
            record = dict()
            record['name'] = at
            record['required'] = False
            record['info'] = self.attribute(at)
            res.append(record)
        return res
