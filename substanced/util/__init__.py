import calendar
import itertools
import math
import urlparse

from pyramid.location import lineage
from pyramid.threadlocal import get_current_registry

from ..event import ACLModified
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

def get_oid(resource, default=_marker):
    """ Return the object identifer of ``resource``.  If ``resource`` has no
    object identifier, raise an AttributeError exception unless ``default`` was
    passed a value; if ``default`` was passed a value, return the default in
    that case."""
    try:
        return resource.__oid__
    except AttributeError:
        if default is _marker:
            raise
        return default

oid_of = get_oid

def set_oid(resource, oid):
    resource.__oid__ = oid

def merge_url_qs(url, **kw):
    """ Merge the query string elements of a URL with the ones in ``kw``.
    If any query string element exists in ``url`` that also exists in
    ``kw``, replace it."""
    segments = urlparse.urlsplit(url)
    extra_qs = [ '%s=%s' % (k, v) for (k, v) in 
                 urlparse.parse_qsl(segments.query, keep_blank_values=1) 
                 if k not in kw ]
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

class Batch(object):
    """
    Given a sequence named ``seq``, and a Pyramid request, return an
    object with the following attributes:

    ``items``

      A list representing a slice of ``seq``.  It will contain the number of
      elements in ``request.params['batch_size']`` or the ``default_size``
      number if such a key does not exist in request.params or the key is
      invalid.  The slice will begin at ``request.params['batch_num']`` or
      zero if such a key does not exist in ``request.params`` or the
      ``batch_num`` key could not successfully be converted to a positive
      integer.

    ``size``

      The value obtained from ``request.params['batch_size']`` or
      ``default_size`` if no ``batch_size`` parameter exists in
      ``request.params`` or the ``batch_size`` parameter could not
      successfully be converted to a positive interger.

    ``num``

      The value obtained from ``request.params['batch_num']`` or ``0`` if no
      ``batch_num`` parameter exists in ``request.params`` or if the
      ``batch_num`` parameter could not successfully be converted to a
      positive integer.  Batch numbers are indexed from zero, so batch ``0``
      is the first batch, batch ``1`` the second, and so forth.

    ``length``

      This is length of the current batch.  It is usually equal to ``size``
      but may be different in the very last batch.  For example, if the
      ``seq`` is ``[1,2,3,4]`` and the batch size is ``3``, the first batch's
      ``length`` will be ``3`` because the batch content will be ``[1,2,3]``;
      but the second and final batch's ``length`` will be ``1`` because the
      batch content will be ``[4]``.

    ``last``

      The batch number computed from the sequence length of the last batch
      (indexed from zero).

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

    ``required``
    
      ``True`` if either ``next_url`` or ``prev_url`` are ``True`` (meaning
      batching is required).

    ``multicolumn``

      ``True`` if the current view should be rendered in multiple columns.

    ``toggle_url``

      The URL to be used for the multicolumn/single column toggle button. The
      ``batch_size``, ``batch_num``, and ``multicolumn`` parameters are
      converted to their multicolumn or single column equivalents. If a user
      is viewing items 40-80 in multiple columns, the toggle will switch to
      items 40-50 in a single column. If a user is viewing items 50-60 in a
      single column, the toggle will switch to items 40-80 in multiple columns.

    ``toggle_text``

      The text to display on the multi-column/single column toggle.

    The ``seq`` passed must define ``__len__`` and ``__slice__`` methods.

    ``make_columns``

    A method to split ``items`` into a nested list representing columns.
    
    """
    def __init__(self, seq, request, url=None, default_size=10, toggle_size=40,
                 seqlen=None):
        if url is None:
            url = request.url

        try:
            num = int(request.params.get('batch_num', 0))
        except (TypeError, ValueError):
            num = 0
        if num < 0:
            num = 0

        try:
            size = int(request.params.get('batch_size', default_size))
        except (TypeError, ValueError):
            size = default_size
        if size < 1:
            size = default_size

        multicolumn = request.params.get('multicolumn', '') == 'True'

        # create multicolumn/single column toggle attributes
        if multicolumn:
            toggle_num = size * num / default_size
            toggle_size = default_size
            toggle_text = 'Single column'
        else:
            toggle_num = size * num / toggle_size
            toggle_text = 'Multi-column'

        start = num * size
        end = start + size
        items = list(itertools.islice(seq, start, end))
        length = len(items)
        if seqlen is None:
            # won't work if seq is a generator
            seqlen = len(seq)
        last = int(math.ceil(seqlen / float(size)) - 1)

        first_url = None
        prev_url = None
        next_url = None
        last_url = None
        toggle_url = None

        if num:
            first_url = merge_url_qs(url, batch_size=size, batch_num=0)
        if start >= size:
            prev_url = merge_url_qs(url, batch_size=size, batch_num=num-1)
        if seqlen > end:
            next_url = merge_url_qs(url, batch_size=size, batch_num=num+1)
        if size and (num < last):
            last_url = merge_url_qs(url, batch_size=size, batch_num=last)

        if prev_url or next_url:
            toggle_url = merge_url_qs(
                url,
                batch_size=toggle_size,
                batch_num=toggle_num,
                multicolumn=not multicolumn,
                )

        self.items = items
        self.num = num
        self.size = size
        self.length = length
        self.required = bool(prev_url or next_url)
        self.multicolumn = multicolumn
        self.toggle_url = toggle_url
        self.toggle_text = toggle_text
        self.first_url = first_url
        self.prev_url = prev_url
        self.next_url = next_url
        self.last_url = last_url
        self.last = last

    def make_columns(self, column_size=10, num_columns=4):
        """ Break ``self.items`` into a nested list representing columns."""
        columns = []
        for i in range(num_columns):
            start = i * column_size
            end = start + column_size
            part = self.items[start:end]
            columns.append(part)
        return columns

def chunks(stream, chunk_size=10000):
    """ Return a generator that will iterate over a stream (a filelike
    object) ``chunk_size`` bytes at a time."""
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        yield chunk

def acquire(resource, name, default=None):
    for node in lineage(resource):
        result = getattr(node, name, _marker)
        if result is not _marker:
            return result
    return default

def get_all_permissions(registry):
    # we cache the set of all permissions, because it's a bit of an expensive
    # lookup
    permissions = getattr(registry, '_all_pyramid_permissions', None)

    if permissions is None:
        intrs = registry.introspector.get_category('permissions')
        if intrs is None:
            intrs = []
        permissions = [ intr['introspectable']['value'] for intr in intrs ]
        registry._all_pyramid_permissions = permissions

    return permissions

def renamer():
    """ Returns a property.  The getter of the property returns the
    ``__name__`` attribute of the instance on which it's defined.  The setter
    of the property calls ``rename()`` on the ``__parent__`` of the instance on
    which it's defined if the new value doesn't match the existing ``__name__``
    of the instance (this will cause ``__name__`` to be reset if the parent is
    a normal Substance D folder ).  Sample usage::

      class SomeContentType(Persistent):
          name = renamer()
    """
    def _get(self):
        return getattr(self, '__name__', None)

    def _set(self, newname):
        oldname = _get(self)
        if newname != oldname:
            parent = getattr(self, '__parent__', None)
            if parent is not None:
                parent.rename(oldname, newname)

    return property(_get, _set)

def set_acl(resource, new_acl, registry=None):
    """Change the ACL on resource to ``new_acl``, which may be a valid ACL or
    ``None``.  If ``new_acl`` is ``None``, any existing non-``None``
    ``__acl__`` attribute of the resource will be removed (via ``del
    resource.__acl__``).  Otherwise, if the resource's ``__acl__`` and the
    ``new_acl`` differ, set the resource's ``__acl__`` to ``new_acl`` via
    setattr.

    If the new ACL and the object's original ACL differ, send a
    :class:`substanced.event.ACLModified` event with the
    new ACL and the original ACL (the ``__acl__`` attribute of the resource, or
    ``None`` if it doesn't have one) as arguments to the event.

    This function will return ``True`` if a mutation to the resource's __acl__
    was performed, and ``False`` otherwise.

    If ``registry`` is passed, it should be a Pyramid registry; if it is not
    passed, this function will use the current threadlocal registry to send the
    event.
    """
    old_acl = getattr(resource, '__acl__', None)
    if new_acl == old_acl:
        return False
    if new_acl is None:
        del resource.__acl__
    else:
        resource.__acl__ = new_acl
    event = ACLModified(resource, old_acl, new_acl)
    if registry is None:
        registry = get_current_registry()
    registry.subscribers((event, resource), None)
    return True

change_acl = set_acl # bw compat

def get_acl(resource, default=None):
    """ Return the ACL of the object or the default if the object has no ACL."""
    return getattr(resource, '__acl__', default)

def get_created(resource):
    """ Return a datetime object (in UTC, but represented as a naive datetime)
    that represents the creation time of the resource.  If the resource has no
    creation time, the return value will be ``None``."""
    return getattr(resource, '__created__', None)

def set_created(resource, created):
    """ Set the creation date/time of the resource.  It must be a datetime
    object (which should be without a timezeone (aka 'naive'), representing the
    UTC date and time."""
    resource.__created__ = created

def dotted_name(g):
    """ Return the dotted name of a global object. """
    name = g.__name__
    module = g.__module__
    return '.'.join((module, name))

