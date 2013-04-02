Cataloging
==========

Substance D provides application content indexing and querying via a *catalog*.
A catalog is an object named ``catalog`` which lives in a folder named
``catalogs`` within your application's resource tree.  A catalog has a number
of indexes, each of which keeps a certain kind of information about your
content.

The Default Catalog
-------------------

A default catalog named ``system`` is installed into the root folder's
``catalogs`` subfolder when you start Pyramid. This ``system`` catalog
contains a default set of indexes:

- path (a ``path`` index)

  Represents the path of the content object.

- name (a ``field`` index), uses ``content.__name__`` exclusively

  Represents the local name of the content object.

- interfaces (a ``keyword`` index)

  Represents the set of interfaces possessed by the content object.

- content_type (a ``field`` index)

  Represents the Susbtance D content-type of an object.

- allowed (an ``allowed`` index)

  Represents the set of users granted the ``sdi.view`` permission to each
  content object.

- text (a ``text`` index)

  Represents the text searched for when you use the filter box within the
  folder contents view of the SDI.

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
queries together, but we don't use it above).  Parentheses can be used to
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
doesn't actually add a catalog to your database, but it makes it possible
to add one later.

Here's an example catalog factory:

.. code-block:: python

   from substanced.catalog import (
       catalog_factory,
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
the root object is created for the first time.

.. code-block:: python

    from substanced.root import Root
    from substanced.event import subscribe_created

    @subscribe_created(Root)
    def created(event):
        root = event.object
        service = root['catalogs']
        service.add_catalog('app1', update_indexes=True)

Querying Across Catalogs
------------------------

In many cases, you might only have one custom attribute that you need
indexed, while the ``system`` catalog has everything else you need. You
thus need an efficient way to combine results from two catalogs,
before executing the query:

.. code-block:: python

    system_catalog = find_catalog(somecontext, 'system')
    my_catalog = find_catalog(somecontext, 'my')
    path = system_catalog['path']
    funky = my_catalog['funky']
    # find me all funky objects that exist under /somepath
    q = funky.eq(True) & path.eq('/somepath')
    resultset = q.execute()
    newresultset = resultset.sort(system_catalog['name'])

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

Right now this is a bit painful.  For example:

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

Allowed Index and Security
--------------------------

The Substance D system catalog at
:class:`substanced.catalog.system.SystemCatalogFactory`
contains a number of default indexes, including an ``Allowed`` index.
Its job is to index security information to allow security-aware results
in queries.

In Substance D we index two permissions on each catalogued resource:
``view`` and ``sdi.view``. This allows us to constrain queries to the
system catalog based on whether the principal issuing the request has
either of those permissions on the matching resource.

To set the ACL in a way that helps keep track of all the contracts,
the helper function :func:`substanced.util.set_acl` can be used. For
example, the site root at :class:`substanced.root.Root` finishes with:

.. code-block:: python

    set_acl(
        self,
        [(Allow, get_oid(admins), ALL_PERMISSIONS)],
        registry=registry,
        )

Deferred Indexing and Mode Parameters
-------------------------------------

As a lesson learned from previous cataloging experience,
Substance D natively supports deferred indexing. As an example,
in many systems the text indexing can be done after the change to the
object is committed in the web request's transaction. Doing so has a
number of performance benefits: the user's request processes more
quickly, the work to extract text from a Word file can be performed
later, less chance to have a conflict error, etc.

As such, the
:py:class:`substanced.catalog.system.SystemCatalogFactory`, by default,
has several indexes that aren't updated immediately when a resource is
changed. For example:

.. code-block:: python

    # name is MODE_ATCOMMIT for next-request folder contents consistency
    name = Field()

    text = Text(action_mode=MODE_DEFERRED)
    content_type = Field(action_mode=MODE_DEFERRED)

The ``Field`` index uses the default of `MODE_ATCOMMIT`. The other two
override the default and set `MODE_DEFERRED`.

There are three such catalog "modes" for indexing:

- :py:class:`substanced.interfaces.MODE_IMMEDIATE` means
  indexing action should take place as immediately as possible.

- :py:class:`substanced.interfaces.MODE_ATCOMMIT` means
  indexing action should take place at the successful end of the
  current transaction.

- :py:class:`substanced.interfaces.MODE_DEFERRED` means
  indexing action should be performed by an
  external indexing processor (e.g. ``drain_catalog_indexing``) if one is
  active at the successful end of the current transaction.  If an indexing
  processor is unavailable at the successful end of the current transaction,
  this mode will be taken to imply the same thing as ``MODE_ATCOMMIT``.

Running an Indexer Process
--------------------------

Great, we've now deferred indexing to a later time. What exactly do we
do at that later time?

Indexer processes are easy to write and schedule with ``supervisor``.
Here is an example of a configuration for ``supervisor.conf`` that will
run in indexer process every five seconds::

    [program:indexer]
    command = %(here)s/../bin/sd_drain_indexing %(here)s/production.ini
    redirect_stderr = true
    stdout_logfile = %(here)s/../var/indexing.log
    autostart = true
    startsecs = 5

This calls ``sd_drain_indexing`` which is a console script that
Substance D automatically creates in your ``bin`` directory. Indexing
messages are logged with standard Python logging to the file that you
name. You can view these messages with the ``supervisorctl`` command
``tail indexer``. For example, here is the output from
``sd_drain_indexing`` when changing a simple ``Document`` content type::

    2013-01-07 11:07:38,306 INFO  [substanced.catalog.deferred][MainThread] no actions to execute
    2013-01-07 11:08:38,329 INFO  [substanced.catalog.deferred][MainThread] executing <substanced.catalog.deferred.IndexAction object oid 5886459017869105529 for index u'text' at 0x106e52910>
    2013-01-07 11:08:38,332 INFO  [substanced.catalog.deferred][MainThread] executing <substanced.catalog.deferred.IndexAction object oid 5886459017869105529 for index u'interfaces' at 0x106e52dd0>
    2013-01-07 11:08:38,333 INFO  [substanced.catalog.deferred][MainThread] executing <substanced.catalog.deferred.IndexAction object oid 5886459017869105529 for index u'content_type' at 0x1076e2ed0>
    2013-01-07 11:08:38,334 INFO  [substanced.catalog.deferred][MainThread] committing
    2013-01-07 11:08:38,351 INFO  [substanced.catalog.deferred][MainThread] committed


Overriding Default Modes Manually
---------------------------------

Above we set the default mode used by an index when Substance D indexes
a resource automatically. Perhaps in an evolve script, you'd like to
override the default mode for that index and reindex immediately.

The ``index_resource`` on an index can be passed an ``action_mode``
flag that overrides the configured mode for that index, and instead,
does exactly what you want for only that call. It does not permanently
change the configured default for indexing mode. This applies also to
``reindex_resource`` and ``unindex_resource``. You can also grab the
catalog itself and reindex with a mode that overrides all default modes
on each index.

Caveat on Complexity
--------------------

Substance D's configurable catalog system comes from 15 years of
lessons learned in building larger systems and seeing both the good and
the bad. This is reflected into the idea of multiple catalogs,
each with multiple indexes, which each can have a default mode and a
call-time mode override.

This gets even more fun when the "index later" ability of deferred
indexing is mixed in. And last, the "undo" facility introduces its own
challenges.

Thus, the approach in Substance D is the result of multiple feats of
juggling and refactoring.
