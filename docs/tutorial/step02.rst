===================================
Step 02: Hello World in Substance D
===================================

Substance D adds quite a bit atop Pyramid. In this step we do the
minimum to bootstrap Substance D, although poking around in Substance D
is saved for the next step.

Goals
=====

- Get Substance D pixels on the screen as easily as possible

- Use that as a well-understood base for adding each unit of complexity

Objectives
==========

- Include Substanced D into your ``Configurator``

- Use a ``substanced.root_factory`` as your ``root_factory``

Steps
=====

#. ``$ cp -r step01 step 02; cd step02; python setup.py develop``

#. Copy the following into ``step02/development.ini``:

   .. literalinclude:: step02/development.ini
      :linenos:

#. Copy the following into ``step02/tutorial/__init__.py``:

   .. literalinclude:: step02/tutorial/__init__.py
      :linenos:

#. Copy the following into ``step02/tutorial/views.py``:

   .. literalinclude:: step02/tutorial/views.py
      :linenos:

#. ``mkdir templates``

#. Copy the following into ``step02/tutorial/templates/hello.pt``:

   .. literalinclude:: step02/tutorial/templates/hello.pt
      :linenos:

#. ``$ pserve development.ini``

#. Open ``http://127.0.0.1:6543/`` in your browser.

Analysis
========

At this point you'll see ``Hello, Little Dummy`` on your screen. But
perhaps you also noticed that your ``step02`` directory grew some new
files: ``Data.fs``, ``Data.fs.index``, etc. What's that all about?

- The ``development.ini`` file has a ``zodbconn.uri`` parameter that
  configures the ``ZODB`` setup, as well as an inclusion of
  ``pyramid_tm`` for transaction management

- The ``__init__.py`` uses ``root_factory=root_factory`` to create a
  persistent Substance D root object instance at the root of the resource
  tree

- We tell the ``Configurator`` to include some settings from Substance
  D, such as paths to static directories

