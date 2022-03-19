# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup
import codecs
import os


def read_file(name):
    with codecs.open(
        os.path.join(os.path.dirname(__file__), name),
        encoding='utf-8'
    ) as f:
        return f.read()


version = '1.0'
shortdesc = 'LDAP/AD convenience with Node-trees based on python-ldap'
longdesc = '\n\n'.join([read_file(name) for name in [
    'README.rst',
    'CHANGES.rst',
    'TODO.rst',
    'LICENSE.rst'
]])


setup(
    name='node.ext.ldap',
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
    keywords='ldap authentication node tree access users groups',
    author='Node Contributors',
    author_email='dev@conestack.org',
    url='https://github.com/conestack/node.ext.ldap',
    license='Simplified BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['node', 'node.ext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'argparse',
        'bda.cache',
        'node.ext.ugm>=1.0',
        'passlib',
        'python-ldap>=2.4.14',
        'setuptools'
    ],
    extras_require={
        'test': [
            'coverage',
            'plone.testing',
            'zope.configuration',
            'zope.testing',
            'zope.testrunner'
        ]
    },
    entry_points="""
    [console_scripts]
    testldap = node.ext.ldap.main:slapd
    """,
)
