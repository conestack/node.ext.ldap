# Copyright 2008-2009, BlueDynamics Alliance, Austria - http://bluedynamics.com
# GNU General Public Licence Version 2 or later

import ldapurl
from ldap.schema.subentry import urlfetch
from ldap.schema.models import AttributeType
from ldap.schema.models import ObjectClass
from ldap.schema.models import LDAPSyntax

class LDAPSchemaInfo(object):
    
    def __init__(self, props):
        self.props = props
        self.baseDN = ''
    
    def binary(self):
        hostport = '%s:%s' % (self.props.server, self.props.port)
        ldap_url = ldapurl.LDAPUrl(hostport=hostport,
                                   dn=self.baseDN,
                                   who=self.props.user,
                                   cred=self.props.password)
        uri = ldap_url.unparse()
        rdn, subschema = urlfetch(uri)
        syntaxes = subschema.sed[LDAPSyntax]
        attrs = list()
        for schemata in subschema.attribute_types(subschema.sed[ObjectClass],
                                                  raise_keyerror=0):
            for attr in schemata.values():
                if not attr:
                    continue
                syntax = syntaxes.get(attr.syntax)
                if syntax and syntax.not_human_readable:
                    attrs.append(attr)
        return attrs