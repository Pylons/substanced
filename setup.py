##############################################################################
#
# Copyright (c) 2008-2012 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = CHANGES = ''

install_requires = [
    'pyramid>=1.4dev',
    'ZODB3',
    'hypatia>=0.1a2',
    'venusian',
    'deform',
    'colander',
    'deform_bootstrap',
    'repoze.evolution',
    'pyramid_zodbconn',
    'pyramid_mailer',
    'cryptacular',
    'python-magic',
    ]

docs_extras = ['Sphinx', 'repoze.sphinx.autointerface']
testing_extras = ['nose', 'coverage', 'mock']

setup(name='substanced',
      version='0.0',
      description='A Zope2-like framework built using Pyramid',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "License :: Repoze Public License",
        ],
      keywords='wsgi pylons pyramid zodb catalog zope',
      author="Chris McDonough",
      author_email="pylons-devel@googlegroups.com",
      url="http://docs.pylonsproject.org",
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=install_requires,
      test_suite="substanced",
      entry_points="""
      [console_scripts]
      sd_evolve = substanced.scripts.evolve:main
      sd_reindex = substanced.scripts.reindex:main
      [pyramid.scaffold]
      substanced=substanced.scaffolds:SubstanceDProjectTemplate
      """,
      extras_require = {
          'testing':testing_extras,
          'docs':docs_extras,
          },
      )
