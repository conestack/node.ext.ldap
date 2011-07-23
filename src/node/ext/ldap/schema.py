import ldapurl
from ldap.schema.subentry import urlfetch
from ldap.schema.models import AttributeType
from ldap.schema.models import ObjectClass
from ldap.schema.models import LDAPSyntax

############
# XXX: later

#class LDAPSchemaInfo(object):
#    
#    def __init__(self, props):
#        self.props = props
#        self.baseDN = ''
#    
#    def binary(self):
#        base_uri = self.props.uri or "ldap://%s:%d/" % (self.props.server,
#                self.props.port)
#        ldap_url = ldapurl.LDAPUrl(ldapUrl=base_uri)
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