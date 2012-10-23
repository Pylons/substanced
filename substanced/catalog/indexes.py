import re

import BTrees
from persistent import Persistent

from zope.interface import implementer

import colander
import deform
import deform_bootstrap.widget

import hypatia.query
import hypatia.interfaces
import hypatia.field
import hypatia.facet
import hypatia.keyword
import hypatia.text
import hypatia.util

from pyramid.traversal import resource_path_tuple
from pyramid.compat import (
    url_unquote_text,
    is_nonstr_iter,
    )
from pyramid.settings import asbool
from pyramid.security import effective_principals
from pyramid.interfaces import IRequest

from ..content import content
from ..objectmap import find_objectmap
from ..schema import Schema
from ..property import PropertySheet
from ..util import get_all_permissions

from .discriminators import AllowedDiscriminator

PATH_WITH_OPTIONS = re.compile(r'\[(.+?)\](.+?)$')

class ResolvingIndex(object):
    def resultset_from_query(self, query, names=None, resolver=None):
        if resolver is None:
            objectmap = find_objectmap(self)
            resolver = objectmap.object_for
        docids = query._apply(names)
        numdocs = len(docids)
        return hypatia.util.ResultSet(docids, numdocs, resolver)

class IndexSchema(Schema):
    category = colander.SchemaNode(
        colander.String(),
        missing='',
        )

class IndexPropertySheet(PropertySheet):
    schema = IndexSchema()
    
    def get(self):
        context = self.context
        props = {}
        props['category'] = context.sd_category
        return props

    def set(self, struct):
        context = self.context
        context.sd_category = struct['category']

@content(
    'Path Index',
    icon='icon-search',
    add_view='add_path_index',
    is_index=True,
    propertysheets = (
        ('', IndexPropertySheet),
        )
    )
@implementer(hypatia.interfaces.IIndex)
class PathIndex(ResolvingIndex, hypatia.util.BaseIndexMixin, Persistent):
    """ Uses the objectmap to apply a query to retrieve object identifiers at
    or under a path"""
    family = BTrees.family64
    include_origin = True
    depth = None

    def __init__(self, family=None):
        if family is not None:
            self.family = family
        self.reset()

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
    add_view='add_field_index',
    is_index=True,
    propertysheets = (
        ('', IndexPropertySheet),
        )
    )
class FieldIndex(ResolvingIndex, hypatia.field.FieldIndex):
    pass

@content(
    'Keyword Index',
    icon='icon-search',
    add_view='add_keyword_index',
    is_index=True,
    propertysheets = (
        ('', IndexPropertySheet),
        )
    )
class KeywordIndex(ResolvingIndex, hypatia.keyword.KeywordIndex):
    pass

@content(
    'Text Index',
    icon='icon-search',
    add_view='add_text_index',
    is_index=True,
    propertysheets = (
        ('', IndexPropertySheet),
        )
    )
class TextIndex(ResolvingIndex, hypatia.text.TextIndex):
    pass

class Facets(colander.SequenceSchema):
    facet = colander.SchemaNode(
        colander.String(),
        )

class FacetIndexSchema(IndexSchema):
    facets = Facets(
        missing=(),
        title = 'Facets (any change will cause a reindex)',
        )

class FacetIndexPropertySheet(PropertySheet):
    schema = FacetIndexSchema()
    
    def get(self):
        context = self.context
        props = {}
        props['category'] = context.sd_category
        props['facets'] = context.facets
        return props

    def set(self, struct):
        context = self.context
        context.sd_category = struct['category']
        facets = tuple(struct['facets'])
        if facets != context.facets:
            context.facets = facets
            name = self.context.__name__
            registry = self.request.registry
            self.context.__parent__.reindex(indexes=(name,), registry=registry)

@content(
    'Facet Index',
    icon='icon-search',
    add_view='add_facet_index',
    is_index=True,
    propertysheets = (
        ('', FacetIndexPropertySheet),
        )
    )
class FacetIndex(ResolvingIndex, hypatia.facet.FacetIndex):
    pass

class PermissionsSchemaNode(colander.SchemaNode):
    def schema_type(self): 
        return deform.Set(allow_empty=True)

    def _get_all_permissions(self, registry): # pragma: no cover (testing)
        return get_all_permissions(registry)

    @property
    def widget(self):
        request = self.bindings['request']
        permissions = self._get_all_permissions(request.registry)
        values = [(p, p) for p in permissions]
        return deform_bootstrap.widget.ChosenMultipleWidget(values=values)

    def validator(self, node, value):
        request = self.bindings['request']
        registry = request.registry
        permissions = self._get_all_permissions(registry)
        for perm in value:
            if not perm in permissions:
                raise colander.Invalid(
                    node, 'Unknown permission %s' % value, value
                    )


class AllowedIndexSchema(IndexSchema):
    permissions = PermissionsSchemaNode(
        missing=(),
        title='Permissions (any change will cause a reindex)',
        )

class AllowedIndexPropertySheet(PropertySheet):
    schema = AllowedIndexSchema()
    
    def get(self):
        context = self.context
        props = {}
        props['category'] = context.sd_category
        props['permissions'] = tuple(context.discriminator.permissions or ())
        return props

    def set(self, struct):
        context = self.context
        context.sd_category = struct['category']
        permissions = tuple(sorted(struct['permissions']))
        if not permissions:
            permissions = None
        if permissions != context.discriminator.permissions:
            context.discriminator = AllowedDiscriminator(permissions)
            name = self.context.__name__
            registry = self.request.registry
            self.context.__parent__.reindex(indexes=(name,), registry=registry)

@content(
    'Allowed Index',
    icon='icon-search',
    add_view='add_allowed_index',
    is_index=True,
    propertysheets = (
        ('', AllowedIndexPropertySheet),
        )
    )
class AllowedIndex(ResolvingIndex, hypatia.keyword.KeywordIndex):
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

