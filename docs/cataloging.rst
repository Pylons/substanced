Cataloging
==========

Substance D provides application content indexing and querying via a *catalog*.
A catalog is an object named ``catalog`` which lives in a folder named
``catalogs`` within your application's resource tree.  A catalog has a number
of indexes, each of which keeps a certain kind of information about your
content.

The Default Catalog
-------------------

A default catalog is installed when you start Pyramid named ``system``.

A default set of indexes is available in the ``system`` catalog:

- path (a ``path`` index)

  Represents the path of the content object.

- name (a ``field`` index), uses ``content.__name__`` exclusively

  Represents the local name of the content object.

- interfaces (a ``keyword`` index)

  Represents the set of interfaces possessed by the content object.

- containment (a ``keyword`` index), uses a custom discriminator exclusively.

  Represents the set of interfaces and classes which are possessed by
  parents of the content object (inclusive of itself)

- allowed (an ``allowed`` index), uses a custom discriminator exclusively.

  Represents the set of users granted a permission to each content object.

Querying the Catalog
--------------------

You execute a catalog query using APIs of the catalog's indexes.

.. code-block:: python

   from substanced.util import find_catalog

   catalog = find_catalog(somecontext, 'system')
   name = catalog['name']
   path = catalog['path']
   # find me all the objects that exist under /somepath with the name 'somename'
   q = name.eq('somename') & path.eq('/somepath')
   resultset = q.execute()
   for contentob in resultset:
       print contentob

The calls to ``name.eq()`` and ``path.eq()`` above each return a query
object.  Those two queries are ANDed together into a single query via the
``&`` operator between them (there's also the ``|`` character to OR the
queries together, but we don't use it above).  Parenthesis can be used to
group query expressions together for the purpose of priority.

Different indexes have different query methods, but most support the ``eq``
method.  Other methods that are often supported by indexes: ``noteq``,
``ge``, ``le``, ``gt``, ``any``, ``notany``, ``all``, ``notall``,
``inrange``, ``notinrange``.  The Allowed index supports an additional
``allows`` method.
   
Query objects support an ``execute`` method.  This method returns a
ResultSet.  A ResultSet can be iterated over; each iteration returns a
content object.  ResultSet also has methods like ``one`` and ``first``, which
return a single content object instead of a set of content objects. A
ResultSet also has a ``sort`` method which accepts an index object (the sort
index) and returns another (sorted) ResultSet.

.. code-block:: python

   catalog = find_catalog(somecontext, 'system')
   name = catalog['name']
   path = catalog['path']
   # find me all the objects that exist under /somepath with the name 'somename'
   q = name.eq('somename') & path.eq('/somepath')
   resultset = q.execute()
   newresultset = resultset.sort(name)

If you don't call ``sort`` on the resultset you get back, the results will
not be sorted in any particular order.

Adding a Catalog
----------------

The system index won't have enough information to form all the queries you
need.  You'll have to add a catalog via code related to your application.

.. code-block:: python

   catalogs = root['catalogs']
   catalog = catalogs.add_catalog('mycatalog', update_indexes=True)

This will add a catalog named ``mycatalog`` to your database and it will add
the indexes related to that catalog type.

However, before you'll be able to do this successfully, the ``mycatalog``
catalog type must be described by a *catalog factory* in code.  A catalog
factory is a collection of index descriptions.  Creating a catalog factory or
doesn't actually add a catalog to your databas3, but it makes it possible to
add one later.

Here's an example catalog factory::

.. code-block:: python

   from substanced.catalog import (
       catalog_factory,
       Field,
       Text,
       )

   @catalog_factory('mycatalog')
   class MyCatalogFactory(object):
       freaky = Text()

You'll need to *scan* code that contains a ``catalog_factory`` in order to use
:meth:`substanced.catalog.CatalogsService.add_catalog` using that factory's
name.

Once you've done this, you can then add the catalog to the database in any bit
of code that has access to the database.  For example, in an event handler when
the system starts up:

.. code-block:: python

    from pyramid.events import ApplicationCreated, subscriber

    @subscriber(ApplicationCreated)
    def created(event):
        root = event.object
        service = root['catalogs']
        service.add_catalog('app1', update_indexes=True)

Object Indexing
---------------

Once a new catalog has been added to the database, each time a new
*catalogable* object is added to the site, its attributes will be indexed by
each catalog in its lineage that "cares about" the object.  The object will
always be indexed in the "system" catalog.  To make sure it's cataloged in
custom catalogs, you'll need to do some work.  To index the object in custom
application indexes, you will need to create a *indexview* for your content,
and register it using :func:`substanced.catalog.add_indexview` (a configurator
directive).

Right now this is a bit painful.  For example::

.. code-block:: python

   class MyCatalogViews(object):
       def __init__(self, content):
           self.content = content

        def freaky(self, default):
            return getattr(self.content, 'freaky', default)

   def includeme(config): # pragma: no cover
       for name in ('freaky',):
           config.add_indexview(
               MyCatalogViews,
               catalog_name='mycatalog',
               index_name=name,
               attr=name
               )

The index view should be a class that accepts a single argument,
(conventionally named ``resource``), in its constructor, and which has one or
more methods named after potential index names.  When it comes time for the
system to index your content, it will create an instance of your indexview
class, and it will then call one or more of its methods; it will call methods
on the indexview object matching the ``attr`` passed in to ``add_indexview``.
The ``default`` value passed in should be returned if the method is unable to
compute a value for the content object.

Hopefully soon we'll make this registration bit a bit less verbose.  But in any
case, once this is done, whenever an object is added to the system, a value
(the result of the ``freaky()`` method of the catalog view) will be indexed in
the ``freaky`` field index.
