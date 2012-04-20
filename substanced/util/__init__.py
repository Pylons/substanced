import calendar
import math
import urlparse

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

def merge_url_qs(url, **kw):
    """ Merge the query string elements of a URL with the ones in **kw """
    segments = urlparse.urlsplit(url)
    extra_qs = [ '%s=%s' % (k, v) for (k, v) in 
                 urlparse.parse_qsl(segments.query, keep_blank_values=1) 
                 if k not in ('batch_size', 'batch_num')]
    qs = ''
    for k, v in sorted(kw.items()):
        qs += '%s=%s&' % (k, v)
    if extra_qs:
        qs += '&'.join(extra_qs)
    else:
        qs = qs[:-1]
    return urlparse.urlunsplit(
        (segments.scheme, segments.netloc, segments.path, qs, segments.fragment)
        )

def get_batchinfo(sequence, request, url=None, default_size=15):
    if url is None:
        url = request.url
        
    num = int(request.params.get('batch_num', 0))
    size = int(request.params.get('batch_size', default_size))

    if size:
        start = num * size
        end = start + size
        batch = sequence[start:end]
        last = int(math.ceil(len(sequence) / float(size)) - 1)
    else:
        start = 0
        end = 0
        batch = sequence
        last = 0
        
    first_url = None
    prev_url = None
    next_url = None
    last_url = None
    
    if num:
        first_url = merge_url_qs(url, batch_size=size, batch_num=0)
    if start >= size:
        prev_url = merge_url_qs(url, batch_size=size, batch_num=num-1)
    if len(sequence) > end:
        next_url = merge_url_qs(url, batch_size=size, batch_num=num+1)
    if size and (num < last):
        last_url = merge_url_qs(url, batch_size=size, batch_num=last)
    
    first_off = prev_off = next_off = last_off = ''
    
    if first_url is None:
        first_off = 'off'
    if prev_url is None:
        prev_off = 'off'
    if next_url is None:
        next_off = 'off'
    if last_url is None:
        last_off = 'off'
        
    return dict(batch=batch,
                required=prev_url or next_url,
                size=size,
                num=num,
                first_url=first_url,
                prev_url=prev_url,
                next_url=next_url,
                last_url=last_url,
                first_off=first_off,
                prev_off=prev_off,
                next_off=next_off,
                last_off=last_off,
                start=start,
                end=end,
                last=last)

