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

from ..content import service
from ..folder import Folder
from ..objectmap import find_objectmap

from .factories import (
    IndexFactory,
    CatalogFactory,
    )

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

@service(
    'Catalog',
    icon='icon-search',
    service_name='catalog',
    add_view='add_catalog_service',
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

        if indexes is not None:
            output and output('reindexing only indexes %s' % str(indexes))

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
            output and output('reindexing %s' % path)

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

        factory = registry.getUtility(ICatalogFactory, name=self.__name__)

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
            output and output('update_indexes: no indexes added or removed')

class IndexViewMapper(object):
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
                result = getattr(view, attr)(result, default)
            return result
        return _function_view

class catalog_factory(object):
    venusian = venusian # for testing injection

    def __init__(self, name):
        self.name = name

    def __call__(self, cls):
        index_factories = {}
        for name in dir(cls):
            value = getattr(cls, name, None)
            if isinstance(value, IndexFactory):
                index_factories[name] = value
                
        factory = CatalogFactory(self.name, index_factories)

        extra = {}

        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            config.add_catalog_factory(self.name, factory, **extra)

        info = self.venusian.attach(factory, callback, category='substanced')

        extra['_info'] = info.codeinfo # fbo "action_method"

        return factory

class CatalogsService(Folder):
    pass # XXX not really just a folder

def make_catalog(folder, name):
    if not 'catalogs' in folder:
        folder.add_service('catalogs', CatalogsService())
    catalogs = folder['catalogs']
    catalogs[name] = Catalog()
    catalog = catalogs[name]
    return catalog

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

def add_catalog_factory(config, name, factory):

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
    config.action(
        discriminator, 
        callable=register,
        introspectables=(intr,)
        )

def add_indexview(
    config,
    view,
    catalog_name,
    index_name,
    context=None,
    attr=None
    ):

    if context is None:
        context = Interface

    composite_name = '%s|%s' % (catalog_name, index_name)

    def register():
        mapper = IndexViewMapper(attr=attr)
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
    
    config.action(
        discriminator, 
        callable=register,
        introspectables=(intr,)
        )
    

def includeme(config): # pragma: no cover
    config.add_view_predicate('catalogable', _CatalogablePredicate)
    config.add_directive('add_catalog_factory', add_catalog_factory)
    config.add_directive('add_indexview', add_indexview)
    config.include('.system')
    config.add_permission('view') # for allowed index .allows() default value
