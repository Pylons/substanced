import colander
import deform.widget
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
from ..schema import Schema
from ..property import PropertySheet

from .discriminators import dummy_discriminator
from . import queue

PATH_WITH_OPTIONS = re.compile(r'\[(.+?)\](.+?)$')

_marker = object()

class ResolvingIndex(object):

    _p_action_tm = None
    action_mode = None

    def seen(self, docid):
        return docid in self.docids()

    def resultset_from_query(self, query, names=None, resolver=None):
        # XXX we should probably flush pending atcommit actions before
        # executing the query; we can't just flush *this* index's actions,
        # we have to flush actions for all indexes in all catalogs related
        # to this query.
        if resolver is None:
            objectmap = find_objectmap(self)
            resolver = objectmap.object_for
        docids = query._apply(names)
        numdocs = len(docids)
        return hypatia.util.ResultSet(docids, numdocs, resolver)

    def get_action_tm(self):
        action_tm = self._p_action_tm
        if action_tm is None:
            action_tm = self._p_action_tm = queue.IndexActionTM(self)
            action_tm.register()
        return action_tm

    def clear_action_tm(self):
        self._p_action_tm = None

    def add_action(self, action):
        action_tm = self.get_action_tm()
        action_tm.add(action)

    def index_content(self, docid, obj, action_mode=None):
        if action_mode is None:
            action_mode = self.action_mode
        if action_mode in (None, queue.MODE_IMMEDIATE):
            self.index_doc(docid, obj)
        else:
            action = queue.AddAction(self, action_mode, docid, obj)
            self.add_action(action)

    def reindex_content(self, docid, obj, action_mode=None):
        if action_mode is None:
            action_mode = self.action_mode
        if action_mode in (None, queue.MODE_IMMEDIATE):
            self.reindex_doc(docid, obj)
        else:
            action = queue.ChangeAction(self, action_mode, docid, obj)
            self.add_action(action)

    def unindex_content(self, docid, action_mode=None):
        if action_mode is None:
            action_mode = self.action_mode
        if action_mode in (None, queue.MODE_IMMEDIATE):
            self.unindex_doc(docid)
        else:
            action = queue.RemoveAction(self, action_mode, docid)
            self.add_action(action)

    def __repr__(self):
        klass = self.__class__
        classname = '%s.%s' % (klass.__module__, klass.__name__)
        return '<%s object %r at %#x>' % (classname,
                                          self.__name__,
                                          id(self))

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

class IndexSchema(Schema):
    """ The property schema for :class:`substanced.principal.Group`
    objects."""
    action_mode = colander.SchemaNode(
        colander.String(),
        missing=colander.null,
        widget=deform.widget.RadioChoiceWidget(
            values=(
                ('', 'Default'),
                ('MODE_IMMEDIATE', 'Immediate'),
                ('MODE_ATCOMMIT', 'Defer Until Commit'),
                ('MODE_DEFERRED', 'Defer Until Action Processing'),
                )
            )
        )

class IndexPropertySheet(PropertySheet):
    schema = IndexSchema()

    def set(self, values):
        action_mode = values['action_mode']
        if not action_mode:
            action_mode = None
        else:
            action_mode = getattr(queue, action_mode)
        self.context.action_mode = action_mode

    def get(self):
        action_mode = self.context.action_mode
        if action_mode is None:
            action_mode = ''
        else:
            action_mode = action_mode.__name__
        return {'action_mode':action_mode}

@content(
    'Field Index',
    icon='icon-search',
    is_index=True,
    propertysheets = ( ('', IndexPropertySheet), ),
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
    propertysheets = ( ('', IndexPropertySheet), ),
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
    propertysheets = ( ('', IndexPropertySheet), ),
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
    propertysheets = ( ('', IndexPropertySheet), ),
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
    propertysheets = ( ('', IndexPropertySheet), ),
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

