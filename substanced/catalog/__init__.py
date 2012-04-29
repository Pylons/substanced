import logging

import transaction

import BTrees

from repoze.catalog.catalog import Catalog as _Catalog

from pyramid.threadlocal import get_current_registry
from pyramid.traversal import resource_path
from pyramid.security import effective_principals
from pyramid.interfaces import IAuthorizationPolicy

from ..interfaces import (
    ISearch,
    ICatalog,
    )

from ..content import content
from ..service import find_service
from ..folder import Folder

logger = logging.getLogger(__name__) # API

@content(
    ICatalog,
    name='Catalog',
    icon='icon-search'
    )
class Catalog(Folder, _Catalog):
    family = BTrees.family32
    transaction = transaction
    def __init__(self, family=None):
        Folder.__init__(self)
        _Catalog.__init__(self, family)
        self.objectids = self.family.IF.TreeSet()

    def clear(self):
        """ Clear all indexes in this catalog. """
        _Catalog.clear(self)
        self.objectids = self.family.IF.TreeSet()

    def index_doc(self, docid, obj):
        """Register the document represented by ``obj`` in indexes of
        this catalog using objectid ``docid``."""
        _Catalog.index_doc(self, docid, obj)
        self.objectids.insert(docid)

    def unindex_doc(self, docid):
        """Unregister the document represented by docid from indexes of
        this catalog."""
        _Catalog.unindex_doc(self, docid)
        try:
            self.objectids.remove(docid)
        except KeyError:
            pass

    def reindex_doc(self, docid, obj):
        """ Reindex the document referenced by docid using the object
        passed in as ``obj`` (typically just does the equivalent of
        ``unindex_doc``, then ``index_doc``, but specialized indexes
        can override the method that this API calls to do less work. """
        _Catalog.reindex_doc(self, docid, obj)
        if not docid in self.objectids:
            self.objectids.insert(docid)

    def reindex(self, dry_run=False, commit_interval=200, indexes=None, 
                path_re=None, output=None):

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
        """
        if output is None: # pragma: no cover
            output = logger.info

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
        objectmap = find_service(self, 'objectmap')
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

    def refresh(self, registry=None, output=None):
        """\
        Refresh the set of persistent indexes by comparing them against the
        indexes added via ``config.add_catalog_index``.  Add any indexes that
        haven't yet been added from that list, and remove any that no longer
        exist in that list.

        ``registry`` should be a Pyramid registry object.  If it is not
        passed, we attempt to obtain the current threadlocal Pyramid
        registry.

        ``output``, if passed should be one of ``None``, ``False`` or a
        function.  If it is a function, the function should accept a single
        message argument that will be used to record the actions taken during
        the reindex.  If ``False`` is passed, no output is done.  If ``None``
        is passed (the default), the output will wind up in the
        ``substanced.catalog`` Python logger output at ``info`` level.
        """
        if output is None: # pragma: no cover
            output = logger.info
            
        output and output('refreshing indexes')

        if registry is None:
            registry = get_current_registry()

        indexes = getattr(registry, '_substanced_indexes', {})
        
        # add mentioned indexes
        for name, index in indexes.items():
            if not name in self:
                self[name] = index
                output and output('added %s index' % (name,))

        # remove unmentioned indexes
        todel = set()
        for name in self:
            if not name in indexes:
                todel.add(name)
        for name in todel:
            del self[name]
            output and output('removed %s index' % (name,))

        output and output('refreshed')

class Search(object):
    """ Catalog query helper """
    family = BTrees.family32
    def __init__(self, context, permission_checker=None):
        self.context = context
        self.permission_checker = permission_checker
        self.catalog = find_service(self.context, 'catalog')
        self.objectmap = find_service(self.context, 'objectmap')

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
        num, oids = self.catalog.query(q, **kw)
        if self.permission_checker is not None:
            num, oids = self.allowed(oids)
        return num, oids, self.resolver

    def search(self, **kw):
        num, oids = self.catalog.search(**kw)
        if self.permission_checker:
            num, oids = self.allowed(oids)
        return num, oids, self.resolver
    
def _add_catalog_index(config, name, index): # pragma: no cover
    def register():
        indexes = getattr(config.registry, '_substanced_indexes', {})
        indexes[name] = index
        config.registry._substanced_indexes = indexes
    config.action(('catalog-index', name), callable=register)

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

def includeme(config): # pragma: no cover
    from zope.interface import Interface
    config.registry.registerAdapter(Search, (Interface,), ISearch)
    config.add_directive('add_catalog_index', _add_catalog_index)
    config.set_request_property(query_catalog, reify=True)
    config.set_request_property(search_catalog, reify=True)
    config.scan('.')
    
