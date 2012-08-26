from substanced.root import Root
from substanced.event import subscribe_created
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

@subscribe_created(Root)
def root_created(event):
    catalog = Catalog()
    catalog['name'] = FieldIndex('__name__')
    catalog['title'] = FieldIndex(get_title)
    catalog['interfaces'] = KeywordIndex(get_interfaces)
    catalog['texts'] = TextIndex(get_textrepr)
    catalog['path'] = PathIndex()
    event.object.add_service('catalog', catalog)
        
