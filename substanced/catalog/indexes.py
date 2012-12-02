import re

import BTrees
from persistent import Persistent

from zope.interface import implementer

import hypatia.query
import hypatia.interfaces
import hypatia.field
import hypatia.facet
import hypatia.keyword
import hypatia.text
import hypatia.util

from pyramid.compat import (
    url_unquote_text,
    is_nonstr_iter,
    )
from pyramid.settings import asbool
from pyramid.security import effective_principals
from pyramid.traversal import resource_path_tuple
from pyramid.interfaces import IRequest

from ..content import content
from ..objectmap import find_objectmap

from .discriminators import dummy_discriminator

PATH_WITH_OPTIONS = re.compile(r'\[(.+?)\](.+?)$')

_marker = object()

class ResolvingIndex(object):
    def resultset_from_query(self, query, names=None, resolver=None):
        if resolver is None:
            objectmap = find_objectmap(self)
            resolver = objectmap.object_for
        docids = query._apply(names)
        numdocs = len(docids)
        return hypatia.util.ResultSet(docids, numdocs, resolver)

@content(
    'Path Index',
    icon='icon-search',
    is_index=True,
    )
@implementer(hypatia.interfaces.IIndex)
class PathIndex(ResolvingIndex, hypatia.util.BaseIndexMixin, Persistent):
    """ Uses the objectmap to apply a query to retrieve object identifiers at
    or under a path"""
    family = BTrees.family64
    include_origin = True
    depth = None

    def __init__(self, discriminator=None, family=None):
        if family is not None:
            self.family = family
        self.reset()

    def document_repr(self, docid, default=None):
        objectmap = find_objectmap(self.__parent__)
        path = objectmap.path_for(docid)
        if path is None:
            return default
        return path

    def reset(self):
        self._not_indexed = self.family.IF.Set()

    def index_doc(self, docid, obj):
        pass

    def unindex_doc(self, docid):
        pass

    def reindex_doc(self, docid, obj):
        pass

    def docids(self):
        return self.__parent__.objectids

    indexed = docids

    def not_indexed(self):
        return self._not_indexed

    def search(self, path_tuple, depth=None, include_origin=True):
        objectmap = find_objectmap(self.__parent__)
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
        # /foo -> stuff under /foo with default depth and include_origin
        # [depth=2]/foo -> stuff under /foo with depth 2 and default i_o
        # [include_origin=false]/foo -> stuff under /foo without include_origin
        # [depth=2,include_origin=false]/foo -> combination of all options
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

    def eq(self, path, depth=None, include_origin=None):
        val = {'path':path}
        if depth is not None:
            val['depth'] = depth
        if include_origin is not None:
            val['include_origin'] = include_origin
        return hypatia.query.Eq(self, val)

@content(
    'Field Index',
    icon='icon-search',
    is_index=True,
    )
class FieldIndex(ResolvingIndex, hypatia.field.FieldIndex):
    def __init__(self, discriminator=None, family=None):
        if discriminator is None:
            discriminator = dummy_discriminator
        hypatia.field.FieldIndex.__init__(self, discriminator, family=family)

@content(
    'Keyword Index',
    icon='icon-search',
    is_index=True,
    )
class KeywordIndex(ResolvingIndex, hypatia.keyword.KeywordIndex):
    def __init__(self, discriminator=None, family=None):
        if discriminator is None:
            discriminator = dummy_discriminator
        hypatia.keyword.KeywordIndex.__init__(
            self, discriminator, family=family
            )

@content(
    'Text Index',
    icon='icon-search',
    is_index=True,
    )
class TextIndex(ResolvingIndex, hypatia.text.TextIndex):
    def __init__(
        self,
        discriminator=None,
        lexicon=None,
        index=None,
        family=None
        ):
        if discriminator is None:
            discriminator = dummy_discriminator
        hypatia.text.TextIndex.__init__(
            self, discriminator, lexicon=lexicon, index=index, family=family,
            )

@content(
    'Facet Index',
    icon='icon-search',
    is_index=True,
    )
class FacetIndex(ResolvingIndex, hypatia.facet.FacetIndex):
    def __init__(self, discriminator=None, facets=None, family=None):
        if discriminator is None:
            discriminator = dummy_discriminator
        if facets is None:
            facets = []
        hypatia.facet.FacetIndex.__init__(
            self, discriminator, facets=facets, family=family
            )

@content(
    'Allowed Index',
    icon='icon-search',
    is_index=True,
    )
class AllowedIndex(KeywordIndex):
    def __init__(self, discriminator=None, family=None):
        if discriminator is None:
            discriminator = dummy_discriminator
        KeywordIndex.__init__(self, discriminator, family=family)

    def allows(self, principals, permission='view'):
        """ ``principals`` may either be 1) a sequence of principal
        indentifiers, 2) a single principal identifier, or 3) a Pyramid
        request, which indicates that all the effective principals implied by
        the request are used."""
        if IRequest.providedBy(principals):
            principals = effective_principals(principals)
        elif not is_nonstr_iter(principals):
            principals = (principals,)
        values = [(principal, permission) for principal in principals]
        return hypatia.query.Any(self, values)
