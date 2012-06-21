from substanced.catalog import Catalog

from substanced.catalog.indexes import (
    FieldIndex,
    TextIndex,
    KeywordIndex,
    PathIndex,
    )

from substanced.catalog.discriminators import (
    get_textrepr,
    get_title,
    get_interfaces,
    )

from substanced.site import Site as _Site

class Site(_Site):
    def __init__(self, *arg, **kw):
        _Site.__init__(self, *arg, **kw)
        catalog = Catalog()
        catalog['name'] = FieldIndex('__name__')
        catalog['title'] = FieldIndex(get_title)
        catalog['interfaces'] = KeywordIndex(get_interfaces)
        catalog['texts'] = TextIndex(get_textrepr)
        catalog['path'] = PathIndex()
        self.add_service('catalog', catalog)
        
