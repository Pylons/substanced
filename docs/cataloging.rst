Cataloging
==========

Substance D provides application content indexing and querying via a *catalog*.
A catalog is an object named ``catalog`` which lives in a ``__services__``
folder within your application's resource tree.  A catalog has a number of
indexes, each of which keeps a certain kind of information about your content.

Adding a Catalog
----------------

You can add a catalog to your site by visiting a ``__services__`` folder and
choosing ``Catalog`` from the ``Add`` dropdown.

Or to add a catalog to your site via code:

.. code-block:: python

   catalog = request.registry.content.create('Catalog')
   somefolder.add_service('catalog', catalog)

More than one catalog can be added to a site, but typically there's only one,
in the root ``__services__`` folder.

Once you've added a catalog, you can begin to add indexes to it.  As of this
writing, there is no way to add indexes to a catalog using the SDI.  It must be
done via code.

The easiest way to do this is to use a combination of the
:func:`~substanced.catalog.add_catalog_index` method of the Configurator and the
:meth:`~substanced.catalog.Catalog.update_indexes` method of a catalog object.

:func:`substance.catalog.add_catalog_index` adds candidate indexes of a
particular name, type, and category.  It doesn't actually add an index to a
catalog, but it makes it available to be added to one later. An example:

.. code-block:: python

    config = Configurator()
    config.include('substanced')
    config.add_catalog_index('myindex', 'field', 'myapp')

The first argument to ``add_catalog_index`` is the index name.  It should be a
simple name without any punctuation in it, as it will be used during queries. It
should be reasonably unique. The second argument is the factory name, which can
be one of ``field``, ``text``, ``keyword``, ``facet`` or ``path``.  The third is
a *category*.  A category is just a string which can be used to group indexes
belonging to the same application together.

The :meth:`~substanced.catalog.Catalog.update_indexes` method of a catalog
object causes all the indexes in a given category added via
``add_catalog_index`` to be inserted into the catalog.

.. code-block:: python

   catalog = root['__services__']['catalog']
   catalog.update_indexes('system', registry=registry, reindex=True)
   catalog.update_indexes('myapp', registry=registry, reindex=True)

A default set of indexes is available in the ``system`` category:

- path (a ``path`` index)

  Represents the path of the content object.

- name (a ``field`` index), uses ``content.__name__`` exclusively

  Represents the local name of the content object.

- oid (a ``field`` index), uses ``oid_of(content)`` exclusively.

  Represents the object identifier (globally unique) of the content object.

- interfaces (a ``keyword`` index)

  Represents the set of interfaces possessed by the content object.

- containment (a ``keyword`` index), uses a custom discriminator exclusively.

  Represents the set of interfaces and classes which are possessed by
  parents of the content object (inclusive of itself)

It is recommended that you use ``update_indexes('system')`` to install these
into your main catalog.

Object Indexing
---------------

Once a catalog has been set up with indexes, each time a new *catalogable*
object is added to the site, its attributes will be indexed.  A catalogable
object is a content object which has indicated that it should be cataloged
via its content type information, e.g.

.. code-block:: python

    @content(
        'Order',
        catalog=True,
        )
    class Order(Persistent):
       freaky = True

The ``catalog=True`` line is where the magic happens.

If value to the ``catalog`` argument can is ``True``, the object will only be
indexed in "system" indexes.  To index the object in custom application indexes,
you will need to create a *catalog view* for your content, and pass it in as
``catalog`` to the content type decorator.

.. code-block:: python

   class OrderCatalogView(object):
       def __init__(self, content):
           self.content = content

        def freaky(self, default):
            return getattr(self.content, 'freaky', default)

    @content(
        'Order',
        catalog=OrderCatalogView,
        )
    class Order(Persistent):
       pass

The catalog view must be a class that accepts a single argument ``content`` in
its constructor, and which has one or more methods named after potential index
names.  When it comes time for the system to index your content, it will create
an instance of your catalog view class, and it will then call one or more of its
methods; it will call methods on the catalog view object matching the index
names present in the catalog it's being indexed in.  The ``default`` value
passed in should be returned if the method is unable to compute a value for the
content object.

When you provide a catalog view for your content, it will be indexed in both
the system indexes and any custom indexes you have.  The name of the method
will be used to match an index name.  So during configuration:

.. code-block:: python

    config = Configurator()
    config.include('substanced')
    config.add_catalog_index('freaky', 'field', 'myapp')

Then during catalog setup:

.. code-block:: python

   catalog = root['__services__']['catalog']
   catalog.update_indexes('system', registry=registry, reindex=True)
   catalog.update_indexes('myapp', registry=registry, reindex=True)

Once this is done, whenever an Order objects is added to the system, a value
(the result of the ``freaky()`` method of the catalog view) will be indexed in
the ``freaky`` field index; system values will also be indexed, but they don't
require any help from your catalog view.

Adding Catalog Index Factories
-------------------------------

If you've created a new kind of index, you can add an index factory for that
index type by using :func:`substance.catalog.add_catalog_index_factory`.  Once
this is done, the factory name will be available as a ``factory_name`` argument
to ``add_catalog_index``.

See the ``substanced.catalog`` module for examples of existing catalog
index factories.

