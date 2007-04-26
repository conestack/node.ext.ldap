# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2007 by:
#     Blue Dynamics Alliance
#         * Klein & Partner KEG, Austria
#         * Squarewave Computing Robert Niederreiter, Austria
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

"""Module bda.ldap.properties

This module provides a Class for wrapping LDAP directory Server connection
properties.
"""

__version__ = '1.0'
__docformat__ = 'plaintext'
__author__ = """Robert Niederreiter <rnix@squarewave.at>"""

class LDAPServerProperties(object):
    """Wrapper Class for LDAP Server connection properties.
    """
    
    def __init__(self, server='localhost', port=389, user='', password=''):
        """Take the connection properties as arguments.
        
        Defaults are:
            server: 'localhost'
            port: 389
            user: ''
            pass: ''
        """
        self.server = server
        self.port = port
        self.user = user
        self.password = password
