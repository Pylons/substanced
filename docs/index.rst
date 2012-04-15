Substance D
===========

Overview
--------

An application development environment built using the :term:`Pyramid` web
application framework.  It is a package which provides integration between
the Pyramid web application framework, :term:`ZODB`, the ``repoze.catalog``,
``repoze.evolution``, ``deform`` and ``colander`` packages.

Substance D owes much of its spirit to the Zope 2 application server.

It will run under CPython 2.6, and 2.7.  

Installation
------------

Install using setuptools, e.g. (within a virtualenv)::

  $ easy_install substanced

Demonstration Application
--------------------------

See the application running at http://substanced.repoze.org for a
demonstration of the Substance D management interface.  The package that
contains the code for that demo is available at
https://github.com/Pylons/substanced/tree/master/demo .

Narrative Documentation
-----------------------

.. toctree::
   :maxdepth: 1

   intro.rst
   content.rst
   mgmtview.rst
   retail.rst

API Documentation
-----------------

.. toctree::
   :maxdepth: 1

   api.rst


Reporting Bugs / Development Versions
-------------------------------------

Visit http://github.com/Pylons/substanced to download development or
tagged versions.

Visit http://github.com/Pylons/substanced/issues to report bugs.

Indices and tables
------------------

* :ref:`glossary`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. add glossary in a hidden toc to avoid warnings

.. toctree::
   :hidden:

   glossary
