# -*- coding: utf-8 -*-
import posix
import samba

# required default callbacks for several object classes.
creation_defaults = dict()

creation_defaults['posixAccount'] = dict()
creation_defaults['posixAccount']['cn'] = posix.cn
creation_defaults['posixAccount']['uid'] = posix.uid
creation_defaults['posixAccount']['uidNumber'] = posix.uidNumber
creation_defaults['posixAccount']['gidNumber'] = posix.gidNumber
creation_defaults['posixAccount']['homeDirectory'] = posix.homeDirectory

creation_defaults['posixGroup'] = dict()
creation_defaults['posixGroup']['cn'] = posix.cn
creation_defaults['posixGroup']['gidNumber'] = posix.gidNumber

creation_defaults['shadowAccount'] = dict()
creation_defaults['shadowAccount']['uid'] = posix.uid

creation_defaults['sambaSamAccount'] = dict()
creation_defaults['sambaSamAccount']['sambaSID'] = samba.sambaUserSID

creation_defaults['sambaGroupMapping'] = dict()
creation_defaults['sambaGroupMapping']['gidNumber'] = posix.gidNumber
creation_defaults['sambaGroupMapping']['sambaSID'] = samba.sambaGroupSID
creation_defaults['sambaGroupMapping']['sambaGroupType'] = samba.sambaGroupType

