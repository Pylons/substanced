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
    'pyramid>=1.5dev', # route_name argument to resource_url
    'ZODB',
    'hypatia>=0.2', # query objects have intersection/union methods
    'venusian>=1.0a3',  # pyramid wants this too (prefer_finals...)
    'deform>=2.0a2', # asset spec in ZPTRendererFactory
    'colander>=1.0a1', # subclassable schemanodes
    'pyramid_zodbconn>=0.6', # connection opened/closed events
    'pyramid_chameleon',
    'pyramid_mailer',
    'cryptacular',
    'python-magic',
    'PyYAML',
    'zope.copy',
    'zope.component', # implictly depended upon by zope.copy
    'zope.deprecation',
    'statsd',
    'walkabout',
    'pytz',
    'unidecode',
    ]

docs_extras = ['Sphinx', 'repoze.sphinx.autointerface']
testing_extras = ['nose', 'coverage', 'mock', 'virtualenv']
i18n_extras = ['Babel', 'transifex-client', 'lingua<2.0']

setup(name='substanced',
      version='1.0a1',
      description='An application server built using Pyramid',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
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
      message_extractors={
          'substanced': [
              ('**.py', 'python', None),  # babel extractor supports plurals
              ('**.pt', 'lingua_xml', None),
          ],
      },
      entry_points="""
      [console_scripts]
      sd_evolve = substanced.scripts.evolve:main
      sd_reindex = substanced.scripts.reindex:main
      sd_drain_indexing = substanced.scripts.drain_indexing:main
      sd_dump = substanced.scripts.dump:main
      sd_adduser = substanced.scripts.add_user:main
      [pyramid.scaffold]
      substanced=substanced.scaffolds:SubstanceDProjectTemplate
      """,
      extras_require = {
          'testing':testing_extras,
          'docs':docs_extras,
          'i18n':i18n_extras,
          },
      )
