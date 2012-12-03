import inspect
import logging
import transaction
import venusian

import BTrees

from zope.interface import (
    implementer,
    Interface,
    providedBy,
    )

from pyramid.traversal import resource_path
from pyramid.threadlocal import get_current_registry
from pyramid.util import object_description

from ..interfaces import (
    ICatalog,
    ICatalogFactory,
    IIndexView,
    )

from ..content import (
    content,
    service,
    )
from ..folder import Folder
from ..objectmap import find_objectmap

from .factories import (
    IndexFactory,
    CatalogFactory,
    Text,
    Field,
    Keyword,
    Facet,
    Allowed,
    Path,
    )

Text = Text # API
Field = Field # API
Keyword = Keyword # API
Facet = Facet # API
Allowed = Allowed # API
Path = Path # API

logger = logging.getLogger(__name__) # API

_marker = object()

def _assertint(docid):
    if not isinstance(docid, (int, long)):
        raise ValueError('%r is not an integer value; document ids must be '
                         'integers' % docid)

def catalog_buttons(context, request, default_buttons):
    """ Show a reindex button before default buttons in the folder contents
    view of a catalog"""
    buttons = [
        {'type':'single',
         'buttons':
         [
             {'id':'reindex',
              'name':'form.reindex',
              'class':'btn-primary',
              'value':'reindex',
              'text':'Reindex'}
             ]
         }
        ] + default_buttons
    return buttons

@content(
    'Catalog',
    icon='icon-search',
    service_name='catalog',
    buttons=catalog_buttons,
    )
@implementer(ICatalog)
class Catalog(Folder):
    
    family = BTrees.family64
    transaction = transaction
    
    def __init__(self, family=None):
        Folder.__init__(self)
        if family is not None:
            self.family = family
        self.reset()

    def __sdi_addable__(self, context, introspectable):
        # The only kinds of objects addable to a Catalog are indexes, so we
        # return True only if the introspectable represents a content type
        # registered with the is_index metadata flag.
        meta = introspectable['meta']
        return meta.get('is_index', False)

    def reset(self):
        """ Clear all indexes in this catalog and clear self.objectids. """
        for index in self.values():
            index.reset()
        self.objectids = self.family.IF.TreeSet()

    def index_doc(self, docid, obj):
        """Register the document represented by ``obj`` in indexes of
        this catalog using objectid ``docid``."""
        _assertint(docid)
        for index in self.values():
            index.index_doc(docid, obj)
        self.objectids.insert(docid)

    def unindex_doc(self, docid):
        """Unregister the document represented by docid from indexes of
        this catalog."""
        _assertint(docid)
        for index in self.values():
            index.unindex_doc(docid)
        try:
            self.objectids.remove(docid)
        except KeyError:
            pass

    def reindex_doc(self, docid, obj):
        """ Reindex the document referenced by docid using the object
        passed in as ``obj`` (typically just does the equivalent of
        ``unindex_doc``, then ``index_doc``, but specialized indexes
        can override the method that this API calls to do less work. """
        _assertint(docid)
        for index in self.values():
            index.reindex_doc(docid, obj)
        if not docid in self.objectids:
            self.objectids.insert(docid)

    def reindex(self, dry_run=False, commit_interval=200, indexes=None, 
                path_re=None, output=None, registry=None):

        """\
        Reindex all objects in the catalog using the existing set of
        indexes. 

        If ``dry_run`` is ``True``, do no actual work but send what would be
        changed to the logger.

        ``commit_interval`` controls the number of objects indexed between
        each call to ``transaction.commit()`` (to control memory
        consumption).

        ``indexes``, if not ``None``, should be a list of index names that
        should be reindexed.  If ``indexes`` is ``None``, all indexes are
        reindexed.

        ``path_re``, if it is not ``None`` should be a regular expression
        object that will be matched against each object's path.  If the
        regular expression matches, the object will be reindexed, if it does
        not, it won't.

        ``output``, if passed should be one of ``None``, ``False`` or a
        function.  If it is a function, the function should accept a single
        message argument that will be used to record the actions taken during
        the reindex.  If ``False`` is passed, no output is done.  If ``None``
        is passed (the default), the output will wind up in the
        ``substanced.catalog`` Python logger output at ``info`` level.

        ``registry``, if passed, should be a Pyramid registry.  If one is not
        passed, the ``get_current_registry()`` function will be used to
        look up the current registry.  This function needs the registry in
        order to access content catalog views.
        """
        if output is None: # pragma: no cover
            output = logger.info

        if registry is None:
            registry = get_current_registry()

        def commit_or_abort():
            if dry_run:
                output and output('*** aborting ***')
                self.transaction.abort()
            else:
                output and output('*** committing ***')
                self.transaction.commit()

        name = self.__name__

        if indexes is not None:
            output and output('%s reindexing only indexes %s' % (
                name, str(indexes)
                ))

        i = 1
        objectmap = find_objectmap(self)
        for objectid in self.objectids:
            resource = objectmap.object_for(objectid)
            if resource is None:
                path = objectmap.path_for(objectid)
                if path is None:
                    output and output(
                        'error: no path for objectid %s in object map' % 
                        objectid)
                    continue
                upath = u'/'.join(path)
                output and output('error: object at path %s not found' % upath)
                continue
            path = resource_path(resource)
            if path_re is not None and path_re.match(path) is None:
                continue
            output and output('%s reindexing %s' % (name, path))

            if indexes is None:
                self.reindex_doc(objectid, resource)
            else:
                for index in indexes:
                    self[index].reindex_doc(objectid, resource)

            if i % commit_interval == 0: # pragma: no cover
                commit_or_abort()
            i+=1

        if i:
            commit_or_abort()

    def update_indexes(
        self,
        registry=None,
        dry_run=False,
        output=None,
        replace=False,
        reindex=False,
        **reindex_kw
        ):
        """
        Use the candidate indexes registered via ``config.add_catalog_factory``
        to populate this catalog.  Any indexes which are present in the
        candidate indexes, but not present in the catalog will be created.  Any
        indexes which are present in the catalog but not present in the
        candidate indexes will be deleted.

        ``registry``, if passed, should be a Pyramid registry.  If one is not
        passed, the ``get_current_registry()`` function will be used to
        look up the current registry.  This function needs the registry in
        order to access content catalog views.

        If ``dry_run`` is ``True``, don't commit the changes made when this
        function is called, just send what would have been done to the logger.

        ``output``, if passed should be one of ``None``, ``False`` or a
        function.  If it is a function, the function should accept a single
        message argument that will be used to record the actions taken during
        the reindex.  If ``False`` is passed, no output is done.  If ``None``
        is passed (the default), the output will wind up in the
        ``substanced.catalog`` Python logger output at ``info`` level.

        This function does not reindex new indexes added to the catalog
        unless ``reindex=True`` is passed.

        Arguments to this method captured as ``kw`` are passed to
        :meth:`substanced.catalog.Catalog.reindex` if ``reindex`` is True,
        otherwise ``kw`` is ignored.

        If ``replace`` is ``True``, an existing catalog index that is
        not in the ``category`` supplied but which has the same name as a
        candidate index will be replaced.  If ``replace`` is ``False``,
        existing indexes will never be replaced.
        """
        if output is None: # pragma: no cover
            output = logger.info

        if registry is None: # pragma: no cover
            registry = get_current_registry()

        factory = registry.getUtility(
            ICatalogFactory,
            name=self.__name__,
            )

        reindex_kw['registry'] = registry
        reindex_kw['dry_run'] = dry_run

        if replace:
            changed = factory.replace(
                self, reindex=reindex, output=output, **reindex_kw
                )
        else:
            changed = factory.sync(
                self, reindex=reindex, output=output, **reindex_kw
                )

        def commit_or_abort():
            if dry_run:
                output and output('*** aborting ***')
                self.transaction.abort()
            else:
                output and output('*** committing ***')
                self.transaction.commit()

        if changed:
            commit_or_abort()
        else:
            name = self.__name__
            output and output(
                '%s update_indexes: no indexes added or removed' % name
                )

@service(
    'Catalogs',
    service_name='catalogs',
    icon='icon-search',
    )
class CatalogsService(Folder):

    Catalog = Catalog # for tests

    def add_catalog(self, name, update_indexes=False):
        """ Create and add a catalog named ``name`` to this catalogs service.
        Return the newly created catalog object.  If a catalog named ``name``
        already exists in this catalogs service, an exception will be raised.

        Example usage in a root created subscriber::

          @subscribe_created(content_type='Root')
          def created(event):
              root = event.object
              service = root['catalogs']
              catalog = service.add_catalog('app1')
              catalog.update_indexes(
                  replace=True, reindex=True, registry=event.registry
                  )

        If ``update_indexes`` is True, indexes in the named catalog factory
        will be added to the newly created catalog.
        """
        catalog = self[name] = self.Catalog()
        catalog.__sdi_deletable__ = False
        if update_indexes:
            catalog.update_indexes(replace=True, reindex=True)
        return catalog

class _IndexViewMapper(object):
    def __init__(self, attr=None):
        self.attr = attr

    def __call__(self, view):
        if inspect.isclass(view):
            view = self.map_method(view)
        else:
            view = self.map_function(view)
        return view

    def map_method(self, view):
        # it's an unbound class method
        attr = self.attr
        def _method_view(resource, default):
            inst = view(resource)
            if attr is None:
                result = inst(default)
            else:
                result = getattr(inst, attr)(default)
            return result
        return _method_view

    def map_function(self, view):
        # its a function or an instance method
        attr = self.attr
        def _function_view(resource, default):
            if attr is None:
                result = view(resource, default)
            else:
                result = getattr(view, attr)(resource, default)
            return result
        return _function_view

class catalog_factory(object):
    """ Decorator for a class which acts as a template for index
    creation.::

      from substanced.catalog import Text

      @catalog_factory('myapp')
      class MyAppIndexes(object):
          text = Text()
          title = Field()

    When scanned, this catalog factory will be added to the registry as
    if :func:`substanced.catalog.add_catalog_factory` were called like::

        config.add_catalog_factory('myapp', MyAppIndexes)

    """
    venusian = venusian # for testing injection

    def __init__(self, name):
        self.name = name

    def __call__(self, cls):
        extra = {}

        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            config.add_catalog_factory(self.name, cls, **extra)

        info = self.venusian.attach(cls, callback, category='substanced')
        extra['_info'] = info.codeinfo # fbo "action_method"

        return cls

def is_catalogable(resource, registry=None):
    if registry is None:
        registry = get_current_registry()
    iface = providedBy(resource)
    return bool(registry.adapters.lookupAll((iface,), IIndexView))

class _CatalogablePredicate(object):
    is_catalogable = staticmethod(is_catalogable) # for testing
    
    def __init__(self, val, config):
        self.val = bool(val)
        self.registry = config.registry

    def text(self):
        return 'catalogable = %s' % self.val

    phash = text

    def __call__(self, context, request):
        return self.is_catalogable(context, self.registry) == self.val

def add_catalog_factory(config, name, cls):
    """
    Directive which adds a named catalog factory to the configuration state.
    The ``cls`` argument should be a class that has named index factory
    instances as attributes.  The ``name`` argument should be a string.
    """

    index_factories = {}

    for cname in dir(cls):
        value = getattr(cls, cname, None)
        if isinstance(value, IndexFactory):
            index_factories[cname] = value

    factory = CatalogFactory(name, index_factories)

    def register():
        config.registry.registerUtility(factory, ICatalogFactory, name=name)

    discriminator = ('sd-catalog-factory', name)
    intr = config.introspectable(
        'sd catalog factories',
        discriminator,
        name,
        'sd catalog factory'
        )
    intr['name'] = name
    intr['factory'] = factory
    intr['cls'] = cls

    config.action(discriminator, callable=register, introspectables=(intr,))

def add_indexview(
    config,
    view,
    catalog_name,
    index_name,
    context=None,
    attr=None
    ):
    """ Directive which adds an index view to the configuration state state.
    The ``view`` argument should be function that is an indeview function, or
    or a class with a ``__call__`` method that acts as an indexview method.
    For example::

        def title(resource, default):
            return getattr(resource, 'title', default)

        config.add_indexview(title, catalog_name='myapp', index_name='title')

    Or, a class::

        def IndexViews(object):
            def __init__(self, resource):
                self.resource = resource

            def __call__(self, default):
                return getattr(self.resource, 'title', default)

        config.add_indexview(
            IndexViews, catalog_name='myapp', index_name='title'
            )

    If an ``attr`` arg is supplied to ``add_indexview``, you can use a
    different attribute of the class instad of ``__call__``::

        def IndexViews(object):
            def __init__(self, resource):
                self.resource = resource

            def title(self, default):
                return getattr(self.resource, 'title', default)

            def name(self, default):
                return getattr(self.resource, 'name', default)

        config.add_indexview(
            IndexViews, catalog_name='myapp', index_name='title', attr='title'
            )
        config.add_indexview(
            IndexViews, catalog_name='myapp', index_name='name', attr='name'
            )

    In this way you can use the same class to represent a bunch of different
    index views.  Eventually there will be a decorator that you'll be able to
    place on such a class that will allow you to scan the class
    without making these imperative ``add_indexview`` calls, but right now
    there is not.

    An index view will be looked up by the cataloging machinery when it wants
    to insert value into a particular catalog type's index.  The
    ``catalog_name`` you use specify which catalog name this indeview is good
    for; it should match the string passed to ``add_catalog_factory`` as a
    ``name``.  The ``index_name`` argument should match an index name used
    within such a catalog.

    Index view lookups work a bit like Pyramid view lookups: you can use the
    ``context`` argument to pass an interface or class which should be used to
    register the index view; such an index view will only be used when the
    resource being indexed has that class or interface.  Eventually we'll
    provide a way to add predicates other than ``context`` too.

    """

    if context is None:
        context = Interface

    composite_name = '%s|%s' % (catalog_name, index_name)

    def register():
        mapper = _IndexViewMapper(attr=attr)
        mapped_view = mapper(view)
        intr['derived_callable'] = mapped_view
        config.registry.registerAdapter(
            mapped_view,
            (context,),
            IIndexView,
            name=composite_name,
            )

    if inspect.isclass(view) and attr:
        view_desc = 'method %r of %s' % (attr, object_description(view))
    else:
        view_desc = object_description(view)

    discriminator = ('sd-index-view', catalog_name, index_name, context)
    intr = config.introspectable(
        'sd index views',
        discriminator,
        view_desc,
        'sd index view'
        )
    intr['catalog_name'] = catalog_name
    intr['index_name'] = index_name
    intr['name'] = composite_name
    intr['callable'] = view
    intr['attr'] = attr
    
    config.action(discriminator, callable=register, introspectables=(intr,))
    

def includeme(config): # pragma: no cover
    config.add_view_predicate('catalogable', _CatalogablePredicate)
    config.add_directive('add_catalog_factory', add_catalog_factory)
    config.add_directive('add_indexview', add_indexview)
    config.include('.system')
    config.add_permission('view') # for allowed index .allows() default value
