from pyramid.traversal import resource_path

import datetime
from zope.interface import providedBy
from zope.interface.declarations import Declaration

from pyramid.location import lineage
from pyramid.security import principals_allowed_by_permission

from ..util import coarse_datetime_repr

def get_title(object, default):
    title = getattr(object, 'title', '')
    if isinstance(title, basestring):
        # lowercase for alphabetic sorting
        title = title.lower()
    return title

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

def get_textrepr(object, default):
    """ Weighted value for text index """
    texts = getattr(object, 'texts', None)
    if texts is None:
        return default
    if isinstance(texts, basestring):
        texts = [texts]
    texts = list(texts)
    while texts and not texts[0]:
        # Want to remove empty attributes from the front of the list, but
        # leave empty attributes at the tail in order to preserve weight.
        del texts[0]
    if len(texts) == 1:
        return texts[0]
    parts = [texts[0]] * 10
    parts.extend(texts[1:])
    return ' '.join(parts)
    
def _get_date_or_datetime(object, attr, default):
    d = getattr(object, attr, None)
    if isinstance(d, datetime.datetime) or isinstance(d, datetime.date):
        return coarse_datetime_repr(d)
    return default

def get_creation_date(object, default):
    return _get_date_or_datetime(object, 'created', default)

def get_modified_date(object, default):
    return _get_date_or_datetime(object, 'modified', default)

class NoWay(object):
    pass

def get_allowed_to_view(obj, default):
    principals = principals_allowed_by_permission(object, 'view')
    if not principals:
        # An empty value tells the catalog to match anything, whereas when
        # there are no principals with permission to view we want for there
        # to be no matches.
        principals = [NoWay()]
    return principals
