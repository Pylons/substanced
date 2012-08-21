Services
--------

A :term:`service` is a name for an object that lives inside a folder named
``__services__``.  For example::

   root
     |
     \ __services__
                   \
                    |-- objectmap
                    |
                    |-- principals

In the above example, two services exist within the ``/__services__`` folder.
One is named ``objectmap``, the other is named ``principals``.

Services expose APIs that exist for the benefit of application developers.
For instance, the ``objectmap`` service provides an API that allows a
developer to relate one object to another, to look up all the objects below a
path, and to resolve an object identifier to an object.  The ``principals``
service allows a developer to add and enumerate users and groups.

A service can be looked up in one of two ways: using the
:func:`pryamid.content.find_service` API or the
:meth:`pyramid.folder.Folder.find_service` API.  They are functionally
equivalent.  The latter exists only as a convenience so you don't need to
import a function if you know you're dealing with a :term:`folder`.

Either variation of ``find_service`` will look up the resource hierarchy
until it finds a parent folder that has a ``__services__`` subfolder.  It
will then look inside that ``__services__`` folder for an object by some
name.

Here's how to use :func:`pyramid.content.find_service`:

.. code-block:: python

   from substanced.content import find_service
   objectmap = find_service(somecontext, 'objectmap')

``somecontext`` above is any :term:`resource` in the :term:`resource tree`.
For example, ``somecontext`` could be a "document" object you've added to a
folder.

Here's how to use :meth:`pyramid.folder.Folder.find_service`:

.. code-block:: python

   objectmap = somefolder.find_service('objectmap')

``somefolder`` above is any :class:`substanced.folder.Folder` object (or any
object which inherits from that class) present in the :term:`resource tree`.
