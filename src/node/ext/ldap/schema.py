import ldapurl
import ldap
from node.ext.ldap import (
    LDAPConnector,
    LDAPCommunicator,
)

class LDAPSchemaInfo(object):
    
    def __init__(self, props):
        connector = LDAPConnector(props=props) 
        communicator = LDAPCommunicator(connector)
        communicator.baseDN = 'dc=my-domain,dc=com'
        communicator.bind()
        res = communicator.search('(objectclass=*)', ldap.SCOPE_BASE, 
                                  'cn=subschema', attrlist=['*','+'])                                       
        if len(res) != 1:
            raise ValueError, 'subschema not found'        
        self.subschema = ldap.schema.SubSchema(ldap.cidict.cidict(res[0][1]))
        
    def __getitem__(self, key):
        return self.subschema.get_obj(ldap.schema.AttributeType, key)
    
#    def binary(self):
#        
#        ldap_url.dn = self.baseDN
#        ldap_url.who = self.props.user
#        ldap_url.cred = self.props.password
#        uri = ldap_url.unparse()
#        rdn, subschema = urlfetch(uri)
#        syntaxes = subschema.sed[LDAPSyntax]
#        attrs = list()
#        for schemata in subschema.attribute_types(subschema.sed[ObjectClass],
#                                                  raise_keyerror=0):
#            for attr in schemata.values():
#                if not attr:
#                    continue
#                syntax = syntaxes.get(attr.syntax)
#                if syntax and syntax.not_human_readable:
#                    attrs.append(attr)
#        return attrs