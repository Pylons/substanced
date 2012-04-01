Substance D
===========

Overview
--------

A Zope2-like system built using the :term:`Pyramid` web application
framework.  It is a package which provides integration between the Pyramid
web application framework, :term:`ZODB`, and the ``repoze.catalog`` package.

It will run under CPython 2.6, and 2.7.  

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

Using
-----

.. pull-quote::

   Unlike other drugs, Substance D had --apparently-- only one source. It was
   synthetic, not organic; therefore, it came from a lab. It could be
   synthesized, and already had been in federal experiments. But the
   constituents were themselves derived from complex substances almost
   equally difficult to synthesize. Theoretically it could be manufactured by
   anyone who had, first, the formula and, second, the technological capacity
   to set up a factory. But in practice the cost was out of reach. Also,
   those who had invented it and were making it available sold it too cheaply
   for effective competition.

   -- Phillip K. Dick, A Scanner Darkly

More Information
----------------

.. toctree::
   :maxdepth: 1

   api.rst
   glossary.rst


Reporting Bugs / Development Versions
-------------------------------------

Visit http://github.com/Pylons/pyramid_catalog to download development or
tagged versions.

Visit http://github.com/Pylons/pyramid_catalog/issues to report bugs.

Indices and tables
------------------

* :ref:`glossary`
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
