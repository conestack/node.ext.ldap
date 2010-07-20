from bda.ldap import LDAPProps, LDAPNode
from bda.ldap import BASE, ONELEVEL, SUBTREE

class LDAPUsersConfig(object):
    """Define how users look and where they are
    """
    def __init__(self,
            props,
            baseDN='',
            id_attr='uid',
            scope=ONELEVEL,
            queryFilter='(objectClass=inetOrgPerson)'):
        self.props = props
        self.baseDN = baseDN
        self.id_attr = id_attr
        self.scope = scope
        self.queryFilter = queryFilter

def ldapUsersConfigFromLUF(luf):
    """Create LDAPUsersConfig from an LDAPUserFolder
    """
    server = luf._delegate._servers[0]
    props = self._props = LDAPProps(
            server=server['host'],
            port=int(server['port']),
            user=luf._binduid,
            password=luf._bindpwd,
            )
    uc = LDAPUsersConfig(props,
            baseDN=luf.users_base,
            id_attr=luf.getProperty('_uid_attr'),
            scope=luf._delegate.getScopes()[luf.users_scope],
            queryFilter=luf._getUserFilterString(),
            )
    #self.login_attr = luf.getProperty('_login_attr')
    return uc

class LDAPUser(LDAPNode):
    """An ldap user
    """

class LDAPUsers(LDAPNode):
    """An ldap users collection
    """
    def __init__(self, config):
        super(LDAPUsers, self).__init__(name=config.baseDN, props=config.props)
        self._search_filter = config.queryFilter
        self._search_scope = config.scope
        self._key_attr = config.id_attr
#        self.login_attr = config.login_attr
        self._childFactory = LDAPUser
