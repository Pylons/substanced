import calendar

from pyramid.traversal import find_resource

def resource_or_none(resource, path):
    try:
        return find_resource(resource, path)
    except KeyError:
        return None

def coarse_datetime_repr(date):
    """Convert a datetime to an integer with 100 second granularity.

    The granularity reduces the number of index entries in the
    catalog.
    """
    timetime = calendar.timegm(date.timetuple())
    return int(timetime) // 100

