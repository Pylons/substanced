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

Setup
-----

Once ``substanced`` is installed, you must use the ``config.include``
mechanism to include it into your Pyramid project's configuration.  In your
Pyramid project's ``__init__.py``:

.. code-block:: python
   :linenos:

   config = Configurator(.....)
   config.include('substanced')

Alternately you can use the ``pyramid.includes`` configuration value in your
``.ini`` file:

.. code-block:: ini
   :linenos:

   [app:myapp]
   pyramid.includes = substanced

See the demonstration application running at http://substanced.repoze.org for
a demonstration of the Substance D management interface.  The package that
contains the code for that demo is available at
https://github.com/Pylons/substanced/tree/master/demo .

More Information
----------------

.. toctree::
   :maxdepth: 1

   content.rst
   api.rst
   glossary.rst


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

Inspiration
-----------

.. pull-quote::

	"The two hemispheres of my brain are competing?" Fred said.

	"Yes."

	"Why?"

	"Substance D. It often causes that, functionally. This is what we
	expected; this is what the tests confirm. Damage having taken place in
	the normally dominant left hemisphere, the right hemisphere is attempting
	to compensate for the impairment. But the twin functions do not fuse,
	because this is an abnormal condition the body isn't prepared for. It
	should never happen. "Cross-cuing", we call it. Related to splitbrain
	phenomena. We could perform a right hemispherectomy, but--"

	"Will this go away," Fred interrupted, "when I get off Substance D?"

	"Probably," the psychologist on the left said, nodding. "It's a
	functional impairment."

	The other man said, "It may be organic damage. It may be
	permanent. Time'll tell, and only after you are off Substance D for a
	long while. And off entirely."

	"What?" Fred said. He did not understand the answer-- was it yes or no?
	Was he damaged forever or not? Which had they said?

    -- Phillip K. Dick, A Scanner Darkly

