===============================
Step 01: Hello World in Pyramid
===============================

Before we get into Substance D, we need to get Pyramid installed and a
sample application working.

Goals
=====

- Get Pyramid pixels on the screen as easily as possible

- Use that as a well-understood base for adding each unit of complexity

Objectives
==========

- Create a module with a view that acts as an HTTP server

- Visit the URL in your browser

Background
==========

Microframeworks are all the rage these days. They provide low-overhead
on execution. But also, they have a low mental overhead: they do so
little, the only things you have to worry about are *your things*.

Pyramid is special because it can act as a single-file module
microframework. You have a single Python file that can be executed
directly by Python. But Pyramid also scales to the largest of
applications.

Steps
=====

#. Make sure you have followed the steps in :doc:`setup`.

#. ``$ mkdir step01; cd step01``

#. Copy the following into ``step01/setup.py``:

   .. literalinclude:: step01/setup.py
      :linenos:

#. Copy the following into ``step01/setup.cfg``:

   .. literalinclude:: step01/setup.cfg
      :linenos:

#. Copy the following into ``step01/development.ini``:

   .. literalinclude:: step01/development.ini
      :linenos:

#. ``mkdir tutorial; cd tutorial``

#. Copy the following into ``step01/tutorial/__init__.py``:

   .. literalinclude:: step01/tutorial/__init__.py
      :linenos:

#. ``cd ..; python ./setup.py develop``

   *Make sure you are using the Python from your virtualenv!*

#. ``$ pserve development.ini``

#. Open ``http://127.0.0.1:6543/`` in your browser.

