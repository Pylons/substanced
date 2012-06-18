import re

import BTrees

from zope.interface import implementer

from hypatia.common import CatalogIndex
from hypatia.interfaces import ICatalogIndex

from pyramid.traversal import resource_path_tuple
from pyramid.compat import url_unquote_text
from pyramid.settings import asbool

from ..service import find_service

# /foo -> stuff under /foo without depth or include_origin
# [depth=2]/foo -> stuff under /foo with depth 2
# [include_origin=false]/foo -> stuff under /foo without include_origin
# [depth=2]/foo -> stuff under /foo with depth 2
# [depth=2,include_origin=false]/foo -> combination of all options

PATH_WITH_OPTIONS = re.compile(r'\[(.+?)\](.+?)$')

@implementer(ICatalogIndex)
class PathIndex(CatalogIndex):
    """ Uses the objectmap to apply a query to retrieve object identifiers at
    or under a path"""
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

    def _parse_optionstr(self, optionstr):
        D = {}
        options = [ x.strip() for x in optionstr.split(',') ]
        for option in options:
            if '=' in option:
                name, val = [ x.strip() for x in option.split('=') ]
            else:
                name = option
                val = True
            D[name] = val
        return D
            
    def _parse_path_str(self, path_str):
        if path_str.startswith('[') and ']' in path_str:
            optionstr, path = PATH_WITH_OPTIONS.match(
                path_str).groups()
            optiondict = self._parse_optionstr(optionstr)
            depth = optiondict.get('depth', None)
            include_origin =  optiondict.get('include_origin', None)
            if depth is None:
                depth = self.depth
            else:
                depth = int(depth)
            if include_origin is None:
                include_origin = self.include_origin
            else:
                include_origin = asbool(include_origin)
        else:
            path = path_str
            depth = self.depth
            include_origin = self.include_origin
            
        if not path.startswith('/'):
            raise ValueError('Path must start with a slash')
        
        tmp = filter(None, url_unquote_text(path).split(u'/'))
        path_tuple = (u'',) + tuple(tmp)
        return path_tuple, depth, include_origin

    def _parse_path(self, obj_or_path):
        depth = self.depth
        include_origin = self.include_origin
        path_tuple = obj_or_path
        if hasattr(obj_or_path, '__parent__'):
            path_tuple = resource_path_tuple(obj_or_path)
        elif isinstance(obj_or_path, basestring):
            path_tuple, depth, include_origin = self._parse_path_str(
                obj_or_path)
        elif not isinstance(obj_or_path, tuple):
            raise ValueError(
                'Must be object, path string, or tuple, not %s' % (
                    obj_or_path,))
        return path_tuple, depth, include_origin

    def apply(self, obj_path_or_dict):
        if isinstance(obj_path_or_dict, dict):
            path_tuple, depth, include_origin = self._parse_path(
                obj_path_or_dict['path'])
            depth = obj_path_or_dict.get('depth', depth)
            include_origin = obj_path_or_dict.get('include_origin',
                                                  include_origin)
        else:
            path_tuple, depth, include_origin = self._parse_path(
                obj_path_or_dict)

        rs = self.search(path_tuple, depth, include_origin)

        if rs:
            return rs
        else:
            return self.family.IF.Set()

    applyEq = apply

# API below, do not remove

from hypatia.field import FieldIndex
from hypatia.facet import FacetIndex
from hypatia.keyword import KeywordIndex
from hypatia.text import TextIndex

# pyflakes:
FieldIndex = FieldIndex
FacetIndex = FacetIndex
KeywordIndex = KeywordIndex
TextIndex = TextIndex

