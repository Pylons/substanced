import BTrees

from zope.interface import implementer

from repoze.catalog.indexes.common import CatalogIndex
from repoze.catalog.interfaces import ICatalogIndex

from pyramid.traversal import resource_path_tuple
from pyramid.compat import url_unquote_text

from ..service import find_service

@implementer(ICatalogIndex)
class PathIndex(CatalogIndex):
    """ Uses the objectmap to apply a query """
    family = BTrees.family32
    include_origin = True
    depth = None

    def __init__(self):
        self._not_indexed = self.family.IF.Set()

    def index_doc(self, docid, obj):
        pass

    def unindex_doc(self, docid):
        pass

    def docids(self):
        return self.__parent__.objectids

    _indexed = docids

    def search(self, path_tuple, depth=None, include_origin=True):
        objectmap = find_service(self.__parent__, 'objectmap')
        return objectmap.pathlookup(path_tuple, depth, include_origin)

    def _parse_path(self, obj_or_path):
        path_tuple = obj_or_path
        if hasattr(obj_or_path, '__parent__'):
            path_tuple = resource_path_tuple(obj_or_path)
        elif isinstance(obj_or_path, basestring):
            tmp = filter(None, url_unquote_text(obj_or_path).split(u'/'))
            path_tuple = (u'',) + tuple(tmp)
        elif not isinstance(obj_or_path, tuple):
            raise ValueError(
                'Must be object, path string, or tuple, not %s' % (
                    obj_or_path,))
        return path_tuple

    def apply(self, obj_path_or_dict):
        if isinstance(obj_path_or_dict, dict):
            path_tuple = self._parse_path(obj_path_or_dict['path'])
            depth = obj_path_or_dict.get('depth', self.depth)
            include_origin = obj_path_or_dict.get(
                'include_origin', self.include_origin)
        else:
            path_tuple = self._parse_path(obj_path_or_dict)
            depth = self.depth
            include_origin = self.include_origin

        rs = self.search(path_tuple, depth, include_origin)

        if rs:
            return rs
        else:
            return self.family.IF.Set()

# API below, do not remove

from repoze.catalog.indexes.field import CatalogFieldIndex
FieldIndex = CatalogFieldIndex
from repoze.catalog.indexes.facet import CatalogFacetIndex
FacetIndex = CatalogFacetIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
KeywordIndex = CatalogKeywordIndex
from repoze.catalog.indexes.text import CatalogTextIndex
TextIndex = CatalogTextIndex

