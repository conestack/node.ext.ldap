# -*- coding: utf-8 -*-
import ldapurl
import ldap
from node.ext.ldap import (
    LDAPConnector,
    LDAPCommunicator,
)

class LDAPSchemaInfo(object):
    
    def __init__(self, props=None):
        connector = LDAPConnector(props=props)
        communicator = LDAPCommunicator(connector)
        communicator.baseDN = 'dc=my-domain,dc=com'
        communicator.bind()
        res = communicator.search('(objectclass=*)', ldap.SCOPE_BASE, 
                                  'cn=subschema', attrlist=['*','+'])                                       
        if len(res) != 1:
            raise ValueError, 'subschema not found'        
        self.subschema = ldap.schema.SubSchema(ldap.cidict.cidict(res[0][1]))
        
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