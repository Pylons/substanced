from zope.interface import providedBy
from zope.interface.declarations import Declaration

from pyramid.location import lineage
from pyramid.security import principals_allowed_by_permission

_marker = object()

def _get_interfaces(content):
    # we unwind all derived and immediate interfaces using spec.flattened()
    # (providedBy would just give us the immediate interfaces)
    provided_by = list(providedBy(content))
    spec = Declaration(provided_by)
    ifaces = list(spec.flattened()) + [content.__class__]
    return set(ifaces)

def get_interfaces(wrapper, default):
    """ Useful as KeywordIndex discriminator.  Return a set of all interfaces
    implemented by the object, including inherited interfaces and its class.
    """
    content = wrapper.content
    return _get_interfaces(content)

def get_containment(wrapper, defaults):
    """ Useful as KeywordIndex discriminator.  Return a set of all interfaces
    implemented by the object *and its containment ancestors*, including
    inherited interfaces, and their classes."""
    content = wrapper.content
    ifaces = set()
    for ancestor in lineage(content):
        ifaces.update(_get_interfaces(ancestor))
    return ifaces

def get_name(wrapper, default):
    """ Useful as a FieldIndex discriminator.  Returns the ``__name__`` of the 
    object or ``default`` if the object has no ``__name__``."""
    content = wrapper.content
    return getattr(content, '__name__', default)

class NoWay(object):
    pass

class AllowedDiscriminator(object):
    def __init__(self, permission):
        self.permission = permission

    def __call__(self, wrapper, default):
        content = wrapper.content
        principals = principals_allowed_by_permission(content, 'view')
        if not principals:
            # An empty value tells the catalog to match anything, whereas when
            # there are no principals with permission to view we want for there
            # to be no matches.
            principals = [NoWay]
        return principals

class CatalogViewDiscriminator(object):
    """ Used as a discriminator for indexes derived from content catalog view 
    registrations. """
    def __init__(self, method_name):
        """
        ``name`` is the attribute name of the method of the catalog view
        which will return the value for this index.
        """
        self.method_name = method_name

    def __call__(self, wrapper, default):
        if wrapper is True:
            # system indexes only
            return default
        content = wrapper.content
        view_factory = wrapper.view_factory
        method_name = self.method_name
        catalog_view = view_factory(content)
        meth = getattr(catalog_view, method_name, _marker)
        if meth is not _marker:
            return meth(default)
        return default
