.. _glossary:

Glossary
========

.. glossary::
   :sorted:

   Pyramid
      A `web framework <http://pylonsproject.org>`_.

   Resource
     An object representing a node in the :term:`resource tree` of your
     Substance D application. A resource becomes the :term:`context` of a
     :term:`view` when someone visits a URL in your application.

   Resource tree
     A nested set of :term:`folder` objects and other kinds of content
     objects, each of which is a :term:`resource`.  Your content objects are
     laid out hierarchically in the resource tree as they're added.

   Folder
     An resource object which contains other resource objects.  See
     :class:`substanced.folder.Folder`.

   Content
     A :term:`resource` which is particularly well-behaved when viewed via
     the Substance D management interface.

   SDI
     An acronym for the "Substance D (Management) Interface".  What you see
     when you visit ``/manage``.

   Resource factory
     An object which creates a :term:`resource` when it's called.  It's often
     just a class that implements the resource itself.

   Content type
     An :term:`interface` associated with a particular kind of content
     object.  A content type also has metadata like an icon, an add view
     name, and other things.

