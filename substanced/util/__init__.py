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
    """ Walks over nodes in a folder recursively. Yields deepest nodes first."""
    def visit(node):
        if IFolder.providedBy(node):
            for child in node.values():
                for result in visit(child):
                    yield result
        yield node
    return visit(startnode)

def oid_of(obj, default=_marker):
    """ Return the object identifer of ``obj``.  If ``obj`` has no object
    identifier, raise an AttributeError exception unless ``default`` was
    passed a value; if ``default`` was passed a value, return the default in
    that case."""
    try:
        return obj.__objectid__
    except AttributeError:
        if default is _marker:
            raise
        return default

def dotted_name(g):
    """ Return the Python dotted name of a globally defined Python object. """
    return '%s.%s' % (g.__module__, g.__name__)
