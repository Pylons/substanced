import calendar

from ..interfaces import IFolder

_marker = object()

def coarse_datetime_repr(date):
    """Convert a datetime to an integer with 100 second granularity.

    The granularity reduces the number of index entries in the
    catalog.
    """
    timetime = calendar.timegm(date.timetuple())
    return int(timetime) // 100

def postorder(startnode):
    """ Yields deepest nodes first """
    def visit(node):
        if IFolder.providedBy(node):
            for child in node.values():
                for result in visit(child):
                    yield result
        yield node
    return visit(startnode)

def oid_of(obj, default=_marker):
    oid = getattr(obj, '__objectid__', default)
    if oid is _marker:
        if default is _marker:
            raise KeyError('%s has no __objectid__' % (obj,))
        return default
    return oid

