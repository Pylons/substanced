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

def get_batchinfo(seq, request, url=None, default_size=15):
    """
    Given a sequence named ``seq``, and a Pyramid request, return a
    dictionary with the following elements:

    ``batch``

      A list representing a slice of ``seq``.  It will contain the number of
      elements in ``request.params['batch_size']`` (or ``default_size`` if
      such a key does not exist in request.params).  The slice will begin at
      ``request.params['batch_num']`` or zero if such a key does not exist in
      ``request.params``.

    ``required``
    
      ``True`` if either ``next_url`` or ``prev_url`` are ``True`` (meaning
      batching is required).

    ``size``

      The value obtained from ``request.params['batch_size']`` (or
      ``default_size`` if no ``batch_size`` parameter exists in
      ``request.params``).

    ``num``

      The value obtained from ``request.params['batch_num']`` (or ``0`` if no
      ``batch_num`` parameter exists in ``request.params``).

    ``start``

      This is the *item number* at which the current batch starts.  For
      example, if it's batch number 2 of a set of batches of size 5, this
      number would be 10 (it's indexed at one).

    ``end``

      This is the *item number* at which the current batch ends.  For
      example, if it's batch number 2 of a set of batches of size 5, this
      number would be 15 (it's indexed at one).

    ``last``

      This is the *batch number* of the last batch based on the
      ``batch_size`` and the length of ``seq``.
        
    ``first_url``

      The URL of the first batch.  This will be a URL with ``batch_num`` and
      ``batch_size`` in its query string.  The base URL will be taken from
      the ``url`` value passed to this function.  If a ``url`` value is not
      passed to this function, the URL will be taken from ``request.url``.
      This value will be ``None`` if the current ``batch_num`` is 0.
    
    ``prev_url``

      The URL of the previous batch.  This will be a URL with ``batch_num``
      and ``batch_size`` in its query string.  The base URL will be taken
      from the ``url`` value passed to this function.  If a ``url`` value is
      not passed to this function, the URL will be taken from
      ``request.url``.  This value will be ``None`` if there is no previous
      batch.

    ``next_url``

      The URL of the next batch.  This will be a URL with ``batch_num`` and
      ``batch_size`` in its query string.  The base URL will be taken from
      the ``url`` value passed to this function.  If a ``url`` value is not
      passed to this function, the URL will be taken from ``request.url``.
      This value will be ``None`` if there is no next batch.
        
    ``last_url``

      The URL of the next batch.  This will be a URL with ``batch_num`` and
      ``batch_size`` in its query string.  The base URL will be taken from
      the ``url`` value passed to this function.  If a ``url`` value is not
      passed to this function, the URL will be taken from ``request.url``.
      This value will be ``None`` if there is no next batch.

    The ``seq`` passed must define ``__len__`` and ``__slice__`` methods.
    
    """
    if url is None:
        url = request.url
        
    num = int(request.params.get('batch_num', 0))
    size = int(request.params.get('batch_size', default_size))

    if size:
        start = num * size
        end = start + size
        batch = seq[start:end]
        last = int(math.ceil(len(seq) / float(size)) - 1)
    else:
        start = 0
        end = 0
        batch = seq
        last = 0
        
    first_url = None
    prev_url = None
    next_url = None
    last_url = None
    
    if num:
        first_url = merge_url_qs(url, batch_size=size, batch_num=0)
    if start >= size:
        prev_url = merge_url_qs(url, batch_size=size, batch_num=num-1)
    if len(seq) > end:
        next_url = merge_url_qs(url, batch_size=size, batch_num=num+1)
    if size and (num < last):
        last_url = merge_url_qs(url, batch_size=size, batch_num=last)
    
    return dict(
        batch=batch,
        required=prev_url or next_url,
        size=size,
        num=num,
        first_url=first_url,
        prev_url=prev_url,
        next_url=next_url,
        last_url=last_url,
        start=start,
        end=end,
        last=last
        )

