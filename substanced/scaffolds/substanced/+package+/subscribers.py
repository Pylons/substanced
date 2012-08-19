from pyramid.events import subscriber

from substanced.event import RootCreated
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

@subscriber(RootCreated)
def root_created(event):
    catalog = Catalog()
    catalog['name'] = FieldIndex('__name__')
    catalog['title'] = FieldIndex(get_title)
    catalog['interfaces'] = KeywordIndex(get_interfaces)
    catalog['texts'] = TextIndex(get_textrepr)
    catalog['path'] = PathIndex()
    event.object.add_service('catalog', catalog)
        
