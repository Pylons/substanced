from pyramid.traversal import resource_path

import datetime
from zope.interface import providedBy
from zope.interface.declarations import Declaration

from pyramid.location import lineage
from pyramid.security import principals_allowed_by_permission

from ..interfaces import ICatalogable
from ..util import coarse_datetime_repr

def get_acl(object, default):
    return getattr(object, '__acl__', default)

def get_title(object, default):
    title = getattr(object, 'title', '')
    if isinstance(title, basestring):
        # lowercase for alphabetic sorting
        title = title.lower()
    return title

def get_name(object, default):
    return getattr(object, '__name__', default)

def get_interfaces(object, default):
    # we unwind all derived and immediate interfaces using spec.flattened()
    # (providedBy would just give us the immediate interfaces)
    provided_by = list(providedBy(object))
    spec = Declaration(provided_by)
    ifaces = list(spec.flattened())
    return ifaces

def get_containment(object, defaults):
    ifaces = set()
    for ancestor in lineage(object):
        ifaces.update(get_interfaces(ancestor, ()))
    return ifaces

def get_path(object, default):
    return resource_path(object)

class FlexibleTextIndexData(object):

    weighted_attrs_cleaners = (('title', None),
                               ('description', None),
                               ('text', None),)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        parts = []
        for attr, cleaner in self.weighted_attrs_cleaners:
            if callable(attr):
                value = attr(self.context)
            else:
                value = getattr(self.context, attr, None)
            if value is not None:
                if cleaner is not None:
                    value = cleaner(value)
                parts.append(value)
        # Want to remove empty attributes from the front of the list, but
        # leave empty attributes at the tail in order to preserve weight.
        while parts and not parts[0]:
            del parts[0]
        return tuple(parts)


def _get_texts(object, default):
    adapter = FlexibleTextIndexData(object)
    texts = adapter()
    if not texts:
        return default
    return texts

def get_textrepr(object, default):
    """ Used for standard repoze.catalog text index. """
    if not ICatalogable.providedBy(object):
        return default
    texts = _get_texts(object, default)
    if texts is default:
        return default
    if isinstance(texts, basestring):
        return texts
    if len(texts) == 1:
        return texts[0]
    parts = [texts[0]] * 10
    parts.extend(texts[1:])
    return ' '.join(parts)
    
def _get_date_or_datetime(object, attr, default):
    d = getattr(object, attr, None)
    if (isinstance(d, datetime.datetime) or
        isinstance(d, datetime.date)):
        return coarse_datetime_repr(d)
    return default

def get_creation_date(object, default):
    return _get_date_or_datetime(object, 'created', default)

def get_modified_date(object, default):
    return _get_date_or_datetime(object, 'modified', default)

def get_creator(object, default):
    creator = getattr(object, 'creator', None)
    if creator is None:
        return default
    return creator

def get_allowed_to_view(object, default):
    principals = principals_allowed_by_permission(object, 'view')
    if not principals:
        # An empty value tells the catalog to match anything, whereas when
        # there are no principals with permission to view we want for there
        # to be no matches.
        principals = [object(),]
    return principals
