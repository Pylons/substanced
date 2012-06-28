==============
Tutorial Setup
==============

This tutorial presumes you have Python 2.6 or higher, a network
connection, and the editor of your choice. The following is enough to
get you started on the first step. Other steps might ask to install
extra packages.

.. note::

   Windows users will need to adapt the Unix-isms below to match
   their environment.

Each "step" in the tutorial is its own Python package. Thus,
at the start of each tutorial step, you will see a reminder to
develop-install that step.

Steps
=====

#. Open a shell window and ``cd`` to a working directory.

#. ``$ mkdir tutorial_workspace; cd tutorial_workspace``

#. ``$ virtualenv env``

#. ``$ export PATH=/path/to/tutorial_workspace/env/bin:$PATH``

#. ``$ which easy_install``

   This should report the ``easy_install`` from ``env/bin``.


Code Examples
=============

Each step in the tutorial asks the reader to enter code examples and
produce a working application. The directories for these steps are
*Python packages*: fully-working, standalone examples that demonstrate
the topic being discussed.

The example files are available for those that don't want to enter the
code as part of the tutorial process.
