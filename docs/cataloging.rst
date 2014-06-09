Cataloging
==========

Substance D provides application content indexing and querying via a *catalog*.
A catalog is an object named ``catalog`` which lives in a service named
``catalogs`` within your application's resource tree.  A catalog has a number
of indexes, each of which keeps a certain kind of information about your
content.

The Default Catalog
-------------------

A default catalog named ``system`` is installed into the root folder's
``catalogs`` subfolder when you start Substance D. This ``system`` catalog
contains a default set of indexes:

- path (a ``path`` index)

  Represents the path of the content object.

- name (a ``field`` index), uses ``content.__name__`` exclusively

  Represents the local name of the content object.

- interfaces (a ``keyword`` index)

  Represents the set of interfaces possessed by the content object.

- content_type (a ``field`` index)

  Represents the Substance D content-type of an object.

- allowed (an ``allowed`` index)

  An index which can be used to filter resultsets using principals and
  permissions.

- text (a ``text`` index)

  Represents the text searched for when you use the filter box within the
  folder contents view of the SDI.

Adding a Catalog
----------------

The ``system`` catalog won't have enough information to form all the queries you
need.  You'll have to add a catalog via code related to your application. The first
step is adding a catalog factory.

A catalog factory is a collection of index descriptions.  Creating a catalog factory
doesn't actually add a catalog to your database, but it makes it possible
to add one later.

Here's an example catalog factory named ``mycatalog``:

.. code-block:: python

   from substanced.catalog import (
       catalog_factory,
       Text,
       Field,
       )

   @catalog_factory('mycatalog')
   class MyCatalogFactory(object):
       freaky = Text()
       funky = Field()

In order to activate a ``@catalog_factory`` decorator, it must be *scanned* using the
Pyramid ``config.scan()`` machinery. This will allow you to use
:meth:`substanced.catalog.CatalogsService.add_catalog` to add a catalog with that
factory's name:

.. code-block:: python

   # in a module named blog.__init__

   from pyramid.config import Configurator

   def main(global_config, **settings):
       config = Configurator()
       config.include('substanced')
       config.scan('blog.catalogs')
       # .. and so on ...

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
        service.add_catalog('mycatalog', update_indexes=True)

Object Indexing
---------------

Once a new catalog has been added to the database, each time a new
*catalogable* object is added to the site, its attributes will be indexed by
each catalog in its lineage that "cares about" the object.  The object will
always be indexed in the "system" catalog.  To make sure it's cataloged in
custom catalogs, you'll need to do some work.  To index the object in a custom
application index, you will need to create an *index view* for your content
using :class:`substanced.catalog.indexview`, and **scan** the resulting index
view using :meth:`pyramid.config.Configurator.scan`:

For example:

.. code-block:: python

   from substanced.catalog import indexview

   class MyCatalogViews(object):
       def __init__(self, resource):
           self.resource = resource

       @indexview(catalog_name='mycatalog')
       def freaky(self, default):
           return getattr(self.resource, 'freaky', default)

An index view class should be a class that accepts a single argument,
(conventionally named ``resource``), in its constructor, and which has one or
more methods named after potential index names.  When it comes time for the
system to index your content, Substance D will create an instance of your
indexview class, and it will then call one or more of its methods; it will call
methods on the indexview object matching the ``attr`` passed in to
``add_indexview``.  The ``default`` value passed in should be returned if the
method is unable to compute a value for the content object.

Once this is done, whenever an object is added to the system, a value (the
result of the ``freaky(default)`` method of the catalog view) will be indexed in the
``freaky`` field index.

You can attach multiple index views to the same index view class:

.. code-block:: python

   from substanced.catalog import indexview

   class MyCatalogViews(object):
       def __init__(self, resource):
           self.resource = resource

       @indexview(catalog_name='mycatalog')
       def freaky(self, default):
           return getattr(self.resource, 'freaky', default)

       @indexview(catalog_name='mycatalog')
       def funky(self, default):
           return getattr(self.resource, 'funky', default)

You can use the "index_name" parameter to ``indexview`` to tell the system that
the index name is not the same as the method name in the index view:

.. code-block:: python

   from substanced.catalog import indexview

   class MyCatalogViews(object):
       def __init__(self, resource):
           self.resource = resource

       @indexview(catalog_name='mycatalog')
       def freaky(self, default):
           return getattr(self.resource, 'freaky', default)

       @indexview(catalog_name='mycatalog', index_name='funky')
       def notfunky(self, default):
           return getattr(self.resource, 'funky', default)

You can use the ``context`` parameter to ``indexview`` to tell the system that
this particular index view should only be executed when the class of the
resource (or any of its interfaces) matches the value of the context:

.. code-block:: python

   from substanced.catalog import indexview

   class MyCatalogViews(object):
       def __init__(self, resource):
           self.resource = resource

       @indexview(catalog_name='mycatalog', context=FreakyContent)
       def freaky(self, default):
           return getattr(self.resource, 'freaky', default)

       @indexview(catalog_name='mycatalog', index_name='funky')
       def notfunky(self, default):
           return getattr(self.resource, 'funky', default)

You can use the ``indexview_defaults`` class decorator to save typing in each
``indexview`` declaration.  Keyword argument names supplied to
``indexview_defaults`` will be used if the ``indexview`` does not supply the
same keyword:

.. code-block:: python

   from substanced.catalog import (
       indexview,
       indexview_defaults,
       )

   @indexview_defaults(catalog_name='mycatalog')
   class MyCatalogViews(object):
       def __init__(self, resource):
           self.resource = resource

       @indexview()
       def freaky(self, default):
           return getattr(self.resource, 'freaky', default)

       @indexview()
       def notfunky(self, default):
           return getattr(self.resource, 'funky', default)

The above configuration is the same as:

.. code-block:: python

   from substanced.catalog import indexview

   class MyCatalogViews(object):
       def __init__(self, resource):
           self.resource = resource

       @indexview(catalog_name='mycatalog')
       def freaky(self, default):
           return getattr(self.resource, 'freaky', default)

       @indexview(catalog_name='mycatalog')
       def notfunky(self, default):
           return getattr(self.resource, 'funky', default)

You can also use the :func:`substanced.catalog.add_indexview` directive to add
index views imperatively, instead of using the ``@indexview`` decorator.

Querying the Catalog
--------------------

You execute a catalog query using APIs of the catalog's indexes.

.. code-block:: python

   from substanced.util import find_catalog

   catalog = find_catalog(resource, 'system')
   name = catalog['name']
   path = catalog['path']
   # find me all the objects that exist under /somepath with the name 'somename'
   q = name.eq('somename') & path.eq('/somepath')
   resultset = q.execute()
   for contentob in resultset:
       print contentob

The calls to ``name.eq()`` and ``path.eq()`` above each return a query object.
Those two queries are ANDed together into a single query via the
``&`` operator between them (there's also the ``|`` character to OR the
queries together, but we don't use it above).  Parentheses can be used to
group query expressions together for the purpose of priority.

Different indexes have different query methods, but most support the ``eq``
method.  Other methods that are often supported by indexes: ``noteq``, ``ge``,
``le``, ``gt``, ``any``, ``notany``, ``all``, ``notall``, ``inrange``,
``notinrange``.  The :class:`~substanced.catalog.indexes.AllowedIndex` supports
an additional :meth:`~substanced.catalog.indexes.AllowedIndex.allows()` method.

Query objects support an ``execute`` method.  This method returns a
:class:`hypatia.util.ResultSet`.  A :class:`hypatia.util.ResultSet` 
can be iterated over; each iteration returns a content object. 
:class:`hypatia.util.ResultSet` also has methods like ``one`` and ``first``, which
return a single content object instead of a set of content objects. A
:class:`hypatia.util.ResultSet` also has a ``sort`` method which accepts an index
object (the sort index) and returns another (sorted) :class:`hypatia.util.ResultSet`.

.. code-block:: python

   catalog = find_catalog(resource, 'system')
   name = catalog['name']
   path = catalog['path']
   # find me all the objects that exist under /somepath with the name 'somename'
   q = name.eq('somename') & path.eq('/somepath')
   resultset = q.execute()
   newresultset = resultset.sort(name)

.. note::
    If you don't call ``sort`` on the :class:`hypatia.util.ResultSet` you get back,
    the results will not be sorted in any particular order.

Querying Across Catalogs
------------------------

In many cases, you might only have one custom attribute that you need
indexed, while the ``system`` catalog has everything else you need. You
thus need an efficient way to combine results from two catalogs,
before executing the query:

.. code-block:: python

    system_catalog = find_catalog(resource, 'system')
    my_catalog = find_catalog(resource, 'mycatalog')
    path = system_catalog['path']
    funky = my_catalog['funky']
    # find me all funky objects that exist under /somepath
    q = funky.eq(True) & path.eq('/somepath')
    resultset = q.execute()
    newresultset = resultset.sort(system_catalog['name'])

Filtering Catalog Results Using the Allowed Index
-------------------------------------------------

The Substance D system catalog at
:class:`substanced.catalog.system.SystemCatalogFactory` contains a number of
default indexes, including an ``allowed`` index.  Its job is to index security
information to allow security-aware results in queries.  This index allows us
to filter queries to the system catalog based on whether the principal issuing
the request has a permission on the matching resource.

For example, the below query will find:

  - all of the subresources inside a folder

  - which is of content type ``News Item``

  - which the current user also possesses the ``view`` permission against

.. code-block:: python

    system_catalog = find_catalog(resource, 'system')
    path = system_catalog['path']
    interfaces = system_catalog['content_type']
    allowed = system_catalog['allowed']
    q = ( path.eq(resource, depth=1, include_origin=False) &
          content_type.eq('News Item') &
          allowed.allows(request, 'view')
        )
    return q

Filtering Catalog Results Using The Objectmap
---------------------------------------------

It is possible to postfilter catalog results using the
:meth:`substanced.objectmap.ObjectMap.allowed` API.  For example:

.. code-block:: python

   def get_allowed_to_view(context, request):

       catalog = find_catalog(context, 'system')
       q = catalog['content_type'].eq('News Item')
       resultset = q.execute()

       objectmap = find_objectmap(context)
       return objectmap.allowed(
                 resultset.oids, request.effective_principals, 'view')

The result of :meth:`~substanced.objectmap.ObjectMap.allowed` is a generator
which returns oids, so the result must be listified if you intend to index into
it, or slice it, or what-have-you.

Setting ACLs
------------

The objectmap keeps track of ACLs in a cache to make catalog security
functionality work.  Note that for the object map's cached version of ACLs to
be correct, you will need to set ACLs in a way that helps keep track of all the
contracts.  For this, the helper function :func:`substanced.util.set_acl` can
be used. For example, the site root at :class:`substanced.root.Root` finishes
with:

.. code-block:: python

    set_acl(
        self,
        [(Allow, get_oid(admins), ALL_PERMISSIONS)],
        registry=registry,
        )

Using ``set_acl`` this way will generate an event that will keep the
objectmap's cache updated.  This will allow the ``allowed`` index to work and
the :meth:`substanced.objectmap.ObjectMap.allowed` method to work.

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
:class:`substanced.catalog.system.SystemCatalogFactory`, by default,
has indexes that aren't updated immediately when a resource is
changed. For example:

.. code-block:: python

    # name is MODE_ATCOMMIT for next-request folder contents consistency
    name = Field()

    text = Text(action_mode=MODE_DEFERRED)
    content_type = Field()

The ``Field`` indexes use the default of `MODE_ATCOMMIT`. The ``Text``
overrides the default and set ``action_mode`` to `MODE_DEFERRED`.

There are three such catalog "modes" for indexing:

- :class:`substanced.interfaces.MODE_IMMEDIATE` means
  indexing action should take place as immediately as possible.

- :class:`substanced.interfaces.MODE_ATCOMMIT` means
  indexing action should take place at the successful end of the
  current transaction.

- :class:`substanced.interfaces.MODE_DEFERRED` means
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

Autosync and Autoreindex
------------------------

If you add ``substanced.catalogs.autosync = true`` within your application's
``.ini`` file, all catalog indexes will be resynchronized with their catalog
factory definitions at application startup time.  Indices which were added to
the catalog factory since the last startup time will be added to each catalog
which uses the index factory.  Likewise, indices which were removed will be
removed from each catalog, and indices which were modified will be modified
according to the catalog factory.  Having this setting in your ``.ini`` file is
like pressing the ``Update indexes`` button on the ``Manage`` tab of each of
your catalogs.  The ``SUBSTANCED_CATALOGS_AUTOSYNC`` environment variable can
also be used to turn this behavior on.  For example ``export
SUBSTANCED_CATALOGS_AUTOSYNC=true``.

If you add ``substanced.catalogs.autoreindex = true`` within your application's
``.ini`` file, all catalogs that were changed as the result of an auto-sync
will automatically be reindexed.  Having this setting in your ``.ini`` file is
like pressing the ``Reindex catalog`` button on the ``Manage`` tab of each
catalog which was changed as the result of hitting ``Update indexes``.  The
``SUBSTANCED_CATALOGS_AUTOREINDEX`` environment variable can also be used to
turn this behavior on.  For example ``export
SUBSTANCED_CATALOGS_AUTOREINDEX=true``.


Forcing Deferral of Indexing
----------------------------

There may be times when you'd like to defer all catalog indexing operations,
such as during a bulk load of data from a script.  Normally, only indexes
marked with ``MODE_DEFERRED`` use deferred indexing, and actions associated
with those indexes are even then only actually deferred if an index processor
is active.

You can force Substance D to defer all catalog indexing using the
``substanced.catalogs.force_deferred`` flag in your application's ``.ini``
file.  When this flag is used, all catalog indexing operations will be added to
the indexer's queue, even those indexes marked as ``MODE_IMMEDIATE`` or
``MODE_ATCOMMIT``.  Deferral will also happen whether or not the indexer is
running, unlike during normal operations.

When you use this flag, you can stop the indexer process, do your bulk load,
and start the indexer again when it's convenient to have all the content
indexing done in the background.

The ``SUBSTANCED_CATALOGS_FORCE_DEFERRED`` environment variable can also be
used to turn this behavior on.  For example ``export
SUBSTANCED_CATALOGS_FORCE_DEFERRED=true``.

