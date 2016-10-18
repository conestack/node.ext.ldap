# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup
import os


version = '1.0b3'
shortdesc = 'LDAP/AD convenience with Node-trees based on python-ldap'
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'CHANGES.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'TODO.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'LICENSE.rst')).read()


setup(
    name='node.ext.ldap',
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='ldap authentication node tree access users groups',
    author='BlueDynamics Alliance',
    author_email='dev@bluedynamics.com',
    url='https://github.com/bluedynamics/node.ext.ldap',
    license='Simplified BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['node', 'node.ext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'python-ldap',
        'smbpasswd',
        'argparse',
        'bda.cache',
        'node.ext.ugm',
    ],
    extras_require={
        'test': [
            'interlude',
            'plone.testing',
            'zope.configuration',
            'zope.testing',
        ]
    },
    entry_points="""
    [console_scripts]
    testldap = node.ext.ldap.main:slapd
    """,
)
