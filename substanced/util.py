import calendar

def coarse_datetime_repr(date):
    """Convert a datetime to an integer with 100 second granularity.

    The granularity reduces the number of index entries in the
    catalog.
    """
    timetime = calendar.timegm(date.timetuple())
    return int(timetime) // 100

