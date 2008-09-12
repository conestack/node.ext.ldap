# -*- coding: utf-8 -*-
#
# Copyright 2006-2008, BlueDynamics Alliance, Austria
# www.bluedynamics.com
#
# GNU General Public Licence Version 2 or later - see LICENCE.GPL

"""
setup.py bdist_egg
"""

from setuptools import setup, find_packages
import sys, os

version = '1.1-rc2'
shortdesc = "LDAP convenience library"
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.txt')).read()

setup(
    name='bda.ldap',
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Operating System :: OS Independent',
            'Programming Language :: Python',          
    ], # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    keywords='ldap',
    author='Robert Niederreiter',
    author_email='dev@bluedynamics.com',
    url='http://svn.plone.org/svn/collective/bda.ldap',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['bda'],
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        'setuptools',                        
        # -*- Extra requirements: -*
    ],    
)
