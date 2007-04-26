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

"""
setup.py bdist_egg
"""

from setuptools import setup, find_packages
import sys, os

version = '1.0'

setup(
    name='bda.ldap',
    version=version,
    description="LDAP lib BlueDynamics Alliance",
    long_description="""""",
    classifiers=[],
    keywords='ldap zope',
    author='Robert Niederreiter',
    author_email='dev@bluedynamics.com',
    url='http://svn.plone.org/svn/collective/bda.ldap',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['bda'],
    include_package_data=True,
    zip_safe=False,
)
