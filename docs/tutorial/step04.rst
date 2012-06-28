============================
Step 04: Simple Content Type
============================

Content-oriented applications are the target for Substance D. Which 
means custom content types. In this tutorial, we do the minimum needed 
to make a content type.

Goals
=====

- Minimal introduction to the machinery and concepts for content types

Objectives
==========

- Show how custom views can get the SDI look

- Provide a link to log into the SDI

Steps
=====

#. ``$ cp -r step04 step 04; cd step04; python setup.py develop``

#. ``rm Data.f*`` to clear out data from previous step.

#. Copy the following into ``step04/tutorial/views.py``:

   .. literalinclude:: step04/tutorial/views.py
      :linenos:

#. Copy the following into ``step04/tutorial/resources.py``:

   .. literalinclude:: step04/tutorial/views.py
      :linenos:

#. ``$ pserve development.ini``

#. Open ``http://127.0.0.1:6543/manage/`` in your browser and login with
   as ``admin``:``admin``.

#. Click on the triangle by the ``Add`` button, choose ``Document``,
   and add a document resource. Then try editing it. Also try undoing
   your edit.

Analysis
========

This is a very simple example of a Substance D content type, but already
you see some of the philosophy behind Substance D.

First, things are a little bit more verbose than other system. Part of
this is due to the options available (e.g. multiple property sheets.)
But part is due to a philosophy of loose coupling between the structure
of your content and the form schemas that add/edit your resources.

Experience (painfully gained) has shown that eliminating a few lines of
code via magic leads to frameworkiness run amok. Stated differently,
the exceptions outnumber the rules. Even this simple case has such an
example: we didn't want to make the user type in a ``name``
(identifier) in the form, but we did want to store that name.

As is shown, a class becomes a content type definition via the
``@content`` decorator. In our case, all the frameworkiness (except
``Persistent``) is packed into the decorator.

We inject a Pyramid view into the SDI via the ``@mgmt_view`` decorator.
In this case, our view is a form. In fact, a Substance D ``FormView``.
Our new ``@mgmt_view`` is registered against an **interface**,
which is a concept we will cover in a later step.

As you can see, we have one code path that handles the add case
(``add_success`` on the ``FormView``) and another for the edit case
(``DocumentBasicPropertySheet.get``). This defeats the DRY principle,
but as it turns out, adding is often quite different than editing. In
many cases, your application code can eliminate some of the repetition
if warranted.

You can have multiple property sheets associated with a content type in
the SDI. That's the reason that ``propertysheets`` is a tuple: just
list them in the order you want them to appear. Property sheets can be
given security settings, hiding them from certain groups of users.

Forms, form handling, schemas, etc. in Substance D are a little bit
more work. The payoff is in less magicification of the frameworkiness.