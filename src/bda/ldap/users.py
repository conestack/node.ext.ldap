from bda.ldap import LDAPProps, LDAPNode
from bda.ldap import BASE, ONELEVEL, SUBTREE

class LDAPUsersConfig(object):
    """Define how users look and where they are
    """
    def __init__(self,
            props,
            baseDN='',
            id_attr='uid',
            login_attr='uid',
            scope=ONELEVEL,
            queryFilter='(objectClass=inetOrgPerson)'):
        self.props = props
        self.baseDN = baseDN
        self.id_attr = id_attr
        self.login_attr = login_attr
        self.scope = scope
        self.queryFilter = queryFilter

# XXX: hanging out, waiting for a better home
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
            login_attr=luf.getProperty('_login_attr'),
            scope=luf._delegate.getScopes()[luf.users_scope],
            queryFilter=luf._getUserFilterString(),
            )
    return uc

class LDAPUser(LDAPNode):
    """An ldap user

    XXX: should this be a node or an adpater for a node?

    Filtering attributes, eg userPassword and providing a setpassword and
    authenticate method might be good. On the other hand, why to filter out
    userPassword?

    If we want to hide the userpassword from the attrs, we either need
    two-stage __setitem__ on LDAPNodeAttributes or LDAPUsers needs to be
    adapter around a real normal node.
    """
    @property
    def id(self):
        return self.__name__

    @property
    def login(self):
        return self.attrs[self.__parent__._login_attr]

    def authenticate(self, pw):
        return self._session.authenticate(self.DN, pw)

    def passwd(self, oldpw, newpw):
        """set a users password
        """
        self._session.passwd(self.DN, oldpw, newpw)

class LDAPUsers(LDAPNode):
    """An ldap users collection
    """
    # principals have ids
    ids = LDAPNode.keys

    def __init__(self, config):
        super(LDAPUsers, self).__init__(name=config.baseDN, props=config.props)
        self._search_filter = config.queryFilter
        self._search_scope = config.scope
        self._key_attr = config.id_attr
        self._login_attr = config.login_attr
        self._ChildClass = LDAPUser

    def authenticate(self, id=None, login=None, pw=None):
        """Authenticate a user either by id xor by login

        If successful, the user's id is returned, otherwise None
        """
        if id is not None and login is not None:
            raise ValueError(u"Either specify id or login, not both.")
        if pw is None:
            raise ValueError(u"You need to specify a password")
        if login:
            id = self.search(criteria={self._login_attr: login}, exact_match=True)
        userdn = self.child_dn(id)
        if self._session.authenticate(userdn, pw):
            return id
        else:
            return None

    def passwd(self, id, oldpw, newpw):
        """Change a users password
        """
        self._session.passwd(self.child_dn(id), oldpw, newpw)
