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

from ..interfaces import (
    MODE_DEFERRED,
    MODE_IMMEDIATE,
    )

class SystemIndexViews(object):
    def __init__(self, resource):
        self.resource = resource

    def interfaces(self, default):
        """ Return a set of all interfaces implemented by the object, including
        inherited interfaces (but no classes).
        """
        return get_interfaces(self.resource, classes=False)

    def name(self, default):
        """ Returns the ``__name__`` of the object or ``default`` if the object
        has no ``__name__``."""
        name = getattr(self.resource, '__name__', default)
        if name is None: # deal with name = None at root
            return default
        return name
 
    def name_text(self, default):
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

    - allowed (an AllowedIndex)

      Represents the set of principals with the ``sdi.view`` or ``view``
      permission against a content object.

    - name_text (a TextIndex)

      Indexes text used for the Substance D folder contents filter box.

    """
    path = Path()
    name = Field(action_mode=MODE_IMMEDIATE)
    interfaces = Keyword(action_mode=MODE_DEFERRED)
    allowed = Allowed(
        permissions=('sdi.view', 'view'),
        action_mode=MODE_IMMEDIATE
        )
    name_text = Text(action_mode=MODE_DEFERRED)

def includeme(config): # pragma: no cover
    for name in ('interfaces', 'name', 'name_text'):
        config.add_indexview(
            SystemIndexViews,
            catalog_name='system',
            index_name=name,
            attr=name
            )
