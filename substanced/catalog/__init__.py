import logging

import transaction

import venusian

import BTrees

from zope.interface import implementer

from hypatia.catalog import CatalogQuery

from pyramid.traversal import resource_path
from pyramid.threadlocal import get_current_registry
from pyramid.security import effective_principals
from pyramid.interfaces import (
    IAuthorizationPolicy,
    PHASE1_CONFIG,
    )
from pyramid.exceptions import (
    ConfigurationConflictError,
    ConfigurationError,
    )

from ..interfaces import (
    ISearch,
    ICatalog,
    )

from . import indexes as indexes_module

from .discriminators import (
    ContentViewDiscriminator,
    get_name,
    get_interfaces,
    get_containment,
    get_allowed_to_view,
    get_textrepr,
    get_title,
    )

from ..content import (
    service,
    find_service,
    )
from ..folder import Folder
from ..objectmap import find_objectmap
from ..util import oid_of

logger = logging.getLogger(__name__) # API

@service(
    'Catalog',
    icon='icon-search',
    service_name='catalog',
    add_view='add_catalog_service',
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

    def __sd_addable__(self, introspectable):
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

            view_factory = catalog_view_factory_for(resource, registry)
            wrapper = CatalogViewWrapper(resource, view_factory)

            if indexes is None:
                self.reindex_doc(objectid, wrapper)
            else:
                for index in indexes:
                    self[index].reindex_doc(objectid, wrapper)
            if i % commit_interval == 0: # pragma: no cover
                commit_or_abort()
            i+=1
        if i:
            commit_or_abort()

    def update_indexes(
        self,
        dry_run=False,
        registry=None,
        output=None,
        reindex=False,
        **kw
        ):
        """
        Use the candidate indexes registered via ``config.add_index`` to
        populate this catalog.  Any indexes which are present in the
        candidate indexes, but not present in the catalog will be created.
        Any indexes which are present in the catalog but not present in
        the candidate indexes will be deleted.

        If ``dry_run`` is ``True``, don't commit the changes made when this
        function is called, just send what would have been done to the logger.

        ``registry``, if passed, should be a Pyramid registry.  If one is not
        passed, the ``get_current_registry()`` function will be used to
        look up the current registry.  This function needs the registry in
        order to access content catalog views.

        ``output``, if passed should be one of ``None``, ``False`` or a
        function.  If it is a function, the function should accept a single
        message argument that will be used to record the actions taken during
        the reindex.  If ``False`` is passed, no output is done.  If ``None``
        is passed (the default), the output will wind up in the
        ``substanced.catalog`` Python logger output at ``info`` level.

        This function does not reindex new indexes added to the catalog
        unless ``reindex=True`` is passed. Arguments to this method
        captured as ``kw`` are passed to 
        :meth:`substanced.catalog.Catalog.reindex` if ``reindex`` is True,
        otherwise ``kw`` is ignored.
        """
        if output is None: # pragma: no cover
            output = logger.info

        if registry is None:
            registry = get_current_registry()

        indexes = get_candidate_indexes(registry)
        added = []
        removed = []

        # add indexes
        for name, vals in indexes.items():
            if name not in self:
                factory_name = vals['factory_name']
                factory_args = vals['factory_args']
                output and output(
                    'update_indexes: adding %s index named %r' % (
                        name, factory_name)
                    )
                factories = get_index_factories(registry)
                factory = factories[factory_name]
                self[name] = factory(name, **factory_args)
                added.append(name)

        # remove indexes
        for name in self.keys():
            if name not in indexes:
                output and output(
                    'update_indexes: removing %s index named %r' % (
                        name)
                    )
                del self[name]
                removed.append(name)

        def commit_or_abort():
            if dry_run:
                output and output('*** aborting ***')
                self.transaction.abort()
            else:
                output and output('*** committing ***')
                self.transaction.commit()

        if added or removed:
            commit_or_abort()
        else:
            output and output('update_indexes: No indexes added or removed')

        if added and reindex:
            output and output('update_indexes: Reindexing added indexes')
            self.reindex(
                indexes=added,
                registry=registry,
                output=output, 
                dry_run=dry_run,
                **kw
                )
        elif added:
            output and output('update_indexes: Not reindexing added indexes')

class Search(object):
    """ Catalog query helper """

    CatalogQuery = CatalogQuery
    
    family = BTrees.family64
    
    def __init__(self, context, permission_checker=None, family=None):
        self.context = context
        self.permission_checker = permission_checker
        self.catalog = find_service(self.context, 'catalog')
        self.objectmap = find_objectmap(self.context)
        if family is not None:
            self.family = family

    def resolver(self, objectid):
        resource = self.objectmap.object_for(objectid)
        if resource is None:
            logger.warn('Resource for objectid %s missing' % (objectid,))
        return resource

    def allowed(self, oids):
        checker = self.permission_checker
        result = self.family.IF.Set()
        resolver = self.resolver
        for oid in oids:
            ob = resolver(oid)
            if ob is None:
                continue
            if checker(ob):
                result.insert(oid)
        return len(result), result

    def query(self, q, **kw):
        num, oids = self.CatalogQuery(
            self.catalog, family=self.family).query(q, **kw)
        if self.permission_checker is not None:
            num, oids = self.allowed(oids)
        return num, oids, self.resolver

    def search(self, **kw):
        num, oids = self.CatalogQuery(
            self.catalog, family=self.family).search(**kw)
        if self.permission_checker:
            num, oids = self.allowed(oids)
        return num, oids, self.resolver

    def sort(self, *arg, **kw):
        num, oids = self.CatalogQuery(
            self.catalog, family=self.family).sort(*arg, **kw)
        if self.permission_checker:
            num, oids = self.allowed(oids)
        return num, oids, self.resolver
    
class _catalog_request_api(object):
    Search = Search
    def __init__(self, request):
        self.request = request
        self.context = request.context

    def _get_permission_checker(self, kw):
        permitted = kw.pop('permitted', None)
        if permitted is not None:
            authz_policy = self.request.registry.queryUtility(
                IAuthorizationPolicy)
            if authz_policy is None:
                return None
            if hasattr(permitted, '__iter__'):
                principals, permission = permitted
            else:
                principals = effective_principals(self.request)
                permission =  permitted
            def permitted(ob):
                return authz_policy.permits(ob, principals, permission)
        return permitted

class query_catalog(_catalog_request_api):
    def __call__(self, *arg, **kw):
        checker = self._get_permission_checker(kw)
        return self.Search(self.context, checker).query(*arg, **kw)

class search_catalog(_catalog_request_api):
    def __call__(self, **kw):
        checker = self._get_permission_checker(kw)
        return self.Search(self.context, checker).search(**kw)

def _assertint(docid):
    if not isinstance(docid, (int, long)):
        raise ValueError('%r is not an integer value; document ids must be '
                         'integers' % docid)

def is_catalogable(resource, registry=None):
    return bool(catalog_view_factory_for(resource, registry))

class GenericViewFactory(object):
    def __init__(self, content):
        self.content = content

def catalog_view_factory_for(resource, registry=None):
    if registry is None:
        registry = get_current_registry()
    value = registry.content.metadata(resource, 'catalog', False)
    if value is True: # bw compat
        value = GenericViewFactory
    return value

class CatalogViewWrapper(object):
    def __init__(self, content, view_factory):
        self.content = content
        self.view_factory = view_factory

class CatalogablePredicate(object):
    is_catalogable = staticmethod(is_catalogable) # for testing
    
    def __init__(self, val, config):
        self.val = bool(val)
        self.registry = config.registry

    def text(self):
        return 'catalogable = %s' % self.val

    phash = text

    def __call__(self, context, request):
        return self.is_catalogable(context, self.registry) == self.val

class indexed(object):
    """ A method decorator which calls 
    :func:`substanced.catalog.add_catalog_index` when scanned, using the
    ``factory_name`` and ``factory_args`` passed, where the index's
    name is the name of the method being wrapped. """

    venusian = venusian # for testing

    def __init__(self, factory_name, **factory_args):
        self.factory_name = factory_name
        self.factory_args = factory_args

    def __call__(self, wrapped):
        index_name = wrapped.__name__

        factory_args = self.factory_args.copy()

        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            factory_args['_info'] = info.codeinfo # FBO action_method
            config.add_catalog_index(
                index_name,
                self.factory_name,
                **factory_args
                )

        info = self.venusian.attach(wrapped, callback, category='substanced')

        return wrapped        

def get_index_factories(registry):
    factories = getattr(registry, 'index_factories', None)
    if factories is None:
        factories = {}
        registry.index_factories = factories
    return factories

def get_candidate_indexes(registry):
    indexes = getattr(registry, 'candidate_indexes', None)
    if indexes is None:
        indexes = {}
        registry.candidate_indexes = indexes
    return indexes

def add_catalog_index_factory(config, name, factory):
    def add_index_factory():
        index_factories = get_index_factories(config.registry)
        index_factories[name] = factory

    discriminator = ('sd-catalog-index-factory', name)
    intr = config.introspectable(
        'sd catalog index factories',
        discriminator,
        name,
        'sd catalog index factory'
        )
    intr['name'] = name
    intr['factory'] = factory
    config.action(
        discriminator, 
        callable=add_index_factory,
        order=PHASE1_CONFIG, # must come before add_catalog_index
        introspectables=(intr,)
        )

def add_catalog_index(config, name, factory_name, **factory_args):
    """ Add a candidate catalog index to the Subtance D ConfigurationError
    state.  ``name`` is an index name.  ``factory_name`` is the name of
    an index factory.  The ``factory_name`` must be in the set of factory
    names added via :func:`substanced.catalog.add_index_factory`.
    ``factory_args`` is a set of args to pass to the index factory when
    the index factory is used to construct an index.

    This directive has the potential to be called multiple times with the same 
    or similar arguments during startup.  It copes with index name/type 
    conflicts in the following ways:

    - If two or more callers call this directive with the exact same arguments,
      no conflict will occur.  In this circumstance, calling the function is
      idempotent.

    - If two or more callers call this directive, one with factory args and
      the rest without factory args, the one with factory args will "win", and
      no conflict will occur.  Every call to this function after the first
      call with ``factory_args`` in this circumstance is idempotent.

    - If two or more callers call this directive with a differing 
      ``factory_name``, but the same ``name``, a conflict error will be raised
      at startup.

    - If two or more callers call this directive with the same name and factory
      name, but each with differing ``factory_args``, a conflict error will be
      raised at startup.

    """

    # Sorry, future self, for the hairy code; it's likely I should have
    # stopped and tried to generalize the Pyramid configuration system to
    # handle this form of conflict detection / resolution instead of
    # doing what's below.

    action_info = config.action_info

    def add_index():

        indexes = get_candidate_indexes(config.registry)

        def add_candidate():
            factories = get_index_factories(config.registry)
            if not factory_name in factories:
                raise ConfigurationError(
                    'No index factory named %r' % factory_name
                    )
            indexes[name] = {
                'factory_name':factory_name, 
                'factory_args':factory_args,
                'action_info':action_info,
                }
            # we need to defer the registration of this introspectable to get 
            # the correct action info showing up
            intr = config.introspectable(
                    'sd catalog indexes', name, name, 'sd catalog index'
                    )
            intr['name'] = name
            intr['factory_name'] = factory_name
            intr['factory_args'] = factory_args
            intr.relate(
                'sd catalog index factories', 
                ('sd-catalog-index-factory', factory_name)
                )
            if config.introspector:
                intr.register(config.introspector, action_info)

        if name in indexes:
            # we can use the existing candidate index info if this factory name
            # and factory arg information doesn't conflict with the existing
            # index

            vals = indexes[name]

            if vals['factory_name'] != factory_name:
                # both indexes must name the same factory, or it's a conflict
                fake_discriminator = (
                'conflicting factory name information for index named %r: '
                '%r vs %r' % (
                    name, factory_name, vals['factory_name']
                    )
                )
                raise ConfigurationConflictError(
                    {fake_discriminator: [vals['action_info']]}
                    )

            if vals['factory_args'] and factory_args:
                # if both the existing candidate index and this index specify 
                # factory args, and those args differ, it'll be a conflict; 
                # but if one doesn't specify any args, or both specify the same
                # args, it's not a conflict
                if vals['factory_args'] != factory_args:
                    fake_discriminator = (
                        'conflicting factory argument information for index '
                        'named %r: %r vs. %r' % (
                            name, factory_args, vals['factory_args'],
                            )
                        )
                    raise ConfigurationConflictError(
                        {fake_discriminator: [vals['action_info']]}
                        )

            if factory_args and not vals['factory_args']:
                # prefer this index, overriding the previously registered one,
                # as it has factory args while the previously registered one 
                # does not.
                add_candidate()

        else:
            add_candidate()

    discriminator = None # we handle our own conflict detection/resolution
    config.action(discriminator, callable=add_index)

def _add_discrim(name, kw):
    discriminator = ContentViewDiscriminator(name)
    kw.setdefault('discriminator', discriminator)

def text_index_factory(name, **kw):
    _add_discrim(name, kw)
    return indexes_module.TextIndex(**kw)

def field_index_factory(name, **kw):
    _add_discrim(name, kw)
    return indexes_module.FieldIndex(**kw)

def keyword_index_factory(name, **kw):
    _add_discrim(name, kw)
    return indexes_module.KeywordIndex(**kw)

def path_index_factory(name, **kw):
    return indexes_module.PathIndex(**kw)

def facet_index_factory(name, **kw):
    _add_discrim(name, kw)
    return indexes_module.FacetIndex(**kw)

def includeme(config): # pragma: no cover
    from zope.interface import Interface
    config.registry.registerAdapter(Search, (Interface,), ISearch)
    config.add_request_method(query_catalog, reify=True)
    config.add_request_method(search_catalog, reify=True)
    config.add_view_predicate('catalogable', CatalogablePredicate)
    config.add_directive('add_catalog_index_factory', add_catalog_index_factory)
    config.add_directive('add_catalog_index', add_catalog_index)
    config.add_catalog_index_factory('text', text_index_factory)
    config.add_catalog_index_factory('field', field_index_factory)
    config.add_catalog_index_factory('facet', facet_index_factory)
    config.add_catalog_index_factory('keyword', keyword_index_factory)
    config.add_catalog_index_factory('path', path_index_factory)
    add_default_indexes(config)
    config.scan('.')

def add_default_indexes(config):
    """ Add the default set of Substance D indexes:

    - path (a PathIndex)

      Represents the path of the content object.

    - name (a FieldIndex), uses ``content.__name__`` exclusively

      Represents the local name of the content object.

    - oid (a FieldIndex), uses ``oid_of(content)`` exclusively.

      Represents the object identifier (globally unique) of the content object.

    - interfaces (a KeywordIndex), uses a custom discriminator exclusively.

      Represents the set of interfaces possessed by the content object.

    - containment (a KeywordIndex), uses a custom discriminator exclusively.

      Represents the set of interfaces and classes which are possessed by
      parents of the content object (inclusive of itself)

    - allowed (a KeywordIndex), uses a custom discriminator exclusively.

      Represents the set of principals allowed to view the content (those with
      the ``view`` permission relative to the content).

    - texts (a TextIndex), uses either ``texts`` of the content's catalog
      view or the ``texts`` attribute/method of the content object if 
      a ``texts`` attribute doesn't exist on the catalog view.

      Represents the set of data that should be searchable via fulltext.

    - title (a FieldIndex), uses either ``title`` of the content's catalog
      view or the ``title`` attribute/method of the content object if 
      a ``title`` attribute doesn't exist on the catalog view.

      Represents the title of a content object.

    """

    CVD = ContentViewDiscriminator

    config.add_catalog_index(
        'path', 'path',
        )
    config.add_catalog_index(
        'name', 'field', discriminator=CVD(None, get_name)
        )
    config.add_catalog_index(
        'oid', 'field', discriminator=CVD(None, oid_of)
        )
    config.add_catalog_index(
        'interfaces', 'keyword', discriminator=CVD(None, get_interfaces)
        )
    config.add_catalog_index(
        'containment', 'keyword', discriminator=CVD(None, get_containment)
        )
    config.add_catalog_index(
        'allowed', 'keyword', discriminator=CVD(None, get_allowed_to_view)
        )
    config.add_catalog_index(
        'texts', 'text', discriminator=CVD('texts', get_textrepr)
        )
    config.add_catalog_index(
        'title', 'field', discriminator=CVD('title', get_title)
        )
