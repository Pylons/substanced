=====================================
The Substanced D Management Interface
=====================================

Substance D's prime directive is to help developers quickly build
custom content management applications with a custom user experience.
For the Substance D parts, though, a polished, stable,
and supported management UI is provided.

The Substance D management interface (aka :term:`SDI`) is a set of :term:`view`
registrations that are imposed upon the :term:`resource tree` of your
application.  The SDI allows you to add, delete, change and otherwise manage
resources and services.

.. image:: images/sdi.png

Benefits and Features
=====================

- CRUD on content resources

- Extensible actions for each content type via management views

- Built-in support for hierarchies with security

- Already-done UIs for all supported features (e.g. references,
  principals)

- Undo facility to back out of the last transaction

- Copy and paste

Background and Motivation
=========================

In prehistoric times there was a Python-based application server,
derived from a commercial predecessor released in 1996. Zope and its
predecessor had a unique, "through-the-web" (TTW) UI for interacting
with the system. This UI, called the "Zope Management Interface" (ZMI),
had a number of capabilities for a number of audiences. Plone,
built on Zope, extended this idea. Other systems, such as Django,
have found that providing an out-of-the-box (OOTB) starting point with
attractive pixels on the screen can be a key selling point.

Substance D taps into this. In particular, lessons learned from our
long experience in this area are applied to the SDI:

- Attractive, official, supported OOTB management UI

- Be successful by being very clear what the SDI *isn't*

What Is and Isn't the SDI
=========================

The SDI is for:

- Developers to use while building their application

- Administrators to use after deployment, to manage certain Substance D
  or application settings provided by the developer

- Certain power users to use as a behind-the-scenese UI

The SDI is *not* for:

- The *retail UI* for your actual application. Unlike Plone,
  we don't expect developers to squeeze their UX expectations into an
  existing UX

- Overridable, customizable, replaceable, frameworky new expectations

The SDI does have a short list of clearly-defined places for developers
to plug in parts of their application. As a prime example, you can
define a :doc:`Management View <mgmtview>` that gets added as a new
tab on a resource.

The SDI is extensible and allows you to plug your own views into it, so you
can present nontechnical users with a way to manage arbitrary kinds of
custom content.

Once again, for clarity: the SDI is not a framework, it is an
application. It is not your retail UI.

Layout
======

The SDI has a mostly-familiar layout:

- A *header* that shows the username as a dropdown menu containing a
  link to the principal screen as well as a logout link

- *Breadcrumbs* with a path from the root

- A series of *tabs* for the management views of the current resource

- Optionally, a *flash message* showing results of the previous
  operation, a warning, or some other notice

- A *footer*

Catalog
=======

With :doc:`cataloging <cataloging>` developers have a powerful facility
that can be added to their application. Like other first-class parts of
Substance D's machinery, this includes an SDI UI for interacting with
the catalog:

.. image:: images/catalog.png

Catalogues are content, meaning they can be added to a folder. You can
add/edit/delete indices to the catalog from the list of built-in index
types. You can also visit an index in a catalog and see some statistics
for that index. Finally, you can also use the SDI to reindex the
contents of an index, if you suspect it has gotten out of sync with the
content.

The catalog also registers a management view on content resources which
gain a ``Indexing`` tab:

.. image:: images/indexing.png

This shows some statistics and allows an SDI user to reindex an
individual resource.

Principals
==========

Managing users and groups, aka principals, is more interesting in a
system like Substance D with rich hierarchies. You can add a folder of
principals to any folder or other kind of container that allows adding
principals:

.. image:: images/principals.png

A principals folder allows you to manage (e.g. add/edit/delete/rename)
users and groups via the SDI, as well as password resets. Since users
and groups are content, you gain some of the other SDI tabs for
managing them (e.g. Security, References):

.. image:: images/user.png



Implementation Notes
====================

While it doesn't matter for developers of Substance D applications,
some notes below regarding how the SDI is implemented:

- High-performance, modern, responsive UI based on Twitter Bootstrap

- We use the upstream LESS variables from Bootstrap in a LESS file for
  parts of the SDI

- Our grid is based on SlickGrid



