from pyramid.location import lineage

from ..util import (
    get_interfaces,
    )

from .factories import (
    Field,
    Keyword,
    Path,
    Allowed,
    Text,
    )

from . import catalog_factory

class SystemIndexViews(object):
    def __init__(self, resource):
        self.resource = resource

    def interfaces(self, default):
        """ Return a set of all interfaces implemented by the object, including
        inherited interfaces (but no classes).
        """
        return get_interfaces(self.resource, classes=False)

    def containment(self, default):
        """ Return a set of all interfaces implemented by the object *and its
        containment ancestors*, including inherited interfaces.  This does
        not index classes."""
        ifaces = set()
        for ancestor in lineage(self.resource):
            ifaces.update(get_interfaces(ancestor, classes=False))
        return ifaces

    def name(self, default):
        """ Returns the ``__name__`` of the object or ``default`` if the object
        has no ``__name__``."""
        name = getattr(self.resource, '__name__', default)
        if name is None: # deal with name = None at root
            return default
        return name

    text = name # use __name__ but allow overriding

@catalog_factory('system')
class SystemCatalogFactory(object):
    """ The default set of Substance D system indexes.

    - path (a PathIndex)

      Represents the path of the content object.

    - name (a FieldIndex)

      Represents the local name of the content object.

    - interfaces (a KeywordIndex)

      Represents the set of interfaces possessed by the content object.

    - containment (a KeywordIndex)

      Represents the set of interfaces and classes which are possessed by
      parents of the content object (inclusive of itself)

    - allowed (an AllowedIndex)

      Represents the set of principals allowed to take some permission against
      a content object.

    """
    path = Path()
    name = Field()
    interfaces = Keyword()
    containment = Keyword()
    allowed = Allowed()
    text = Text()

def includeme(config): # pragma: no cover
    for name in ('interfaces', 'containment', 'name', 'text'):
        config.add_indexview(
            SystemIndexViews,
            catalog_name='system',
            index_name=name,
            attr=name
            )
