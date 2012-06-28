====================================
Step 03: Substance D "SDI" Interface
====================================

As mentioned earlier, Substanced D is a framework for building 
content-oriented applications. Along the way, it provides a default 
admin interface that is extensible by developers. In this step we poke 
around the "SDI" management interface.

Goals
=====

- One small step to get visibility of SDI

Objectives
==========

- Show how custom views can get the SDI look

- Provide a link to log into the SDI

Steps
=====

#. ``$ cp -r step03 step 03; cd step03; python setup.py develop``

#. ``rm Data.f*`` to clear out data from previous step.

#. Copy the following into ``step03/tutorial/views.py``:

   .. literalinclude:: step03/tutorial/views.py
      :linenos:

#. Copy the following into ``step03/tutorial/templates/hello.pt``:

   .. literalinclude:: step03/tutorial/templates/hello.pt
      :linenos:

#. ``$ pserve development.ini``

#. Open ``http://127.0.0.1:6543/`` in your browser.

#. Click on ``Substance D`` in the header.

#. Login with username ``admin`` and password ``admin``.

Analysis
========

This is the management UI for Substance D, and a visualization of the
content-oriented approach to building applications. As you click
through and add content, the object database is storing your resources
transactionally.