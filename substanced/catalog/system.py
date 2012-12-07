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
 
    def text(self, default):
        """ Returns a derivation of the name for text indexing.  If name has no
        separator characters in it, the function will return the name
        unchanged.  Otherwise it will return the name plus the derivation of
        splitting the name on the separator characters.  The separator
        characters are: ``, . - _``.  For example, if the name is
        ``foo-bar_baz.pt,foz``, the return value will be ``foo-bar_baz.pt,foz
        foo bar baz pt foz``.  This allows for the most common lookups of
        partial index values in the filter box."""
        name = self.name(default)
        if name is default:
            return default
        if not hasattr(name, 'split'):
            return name
        val = name
        for char in (',', '-', '_', '.'):
            val = ' '.join([x.strip() for x in val.split(char)])
        if val != name:
            return name + ' ' + val
        return name

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
