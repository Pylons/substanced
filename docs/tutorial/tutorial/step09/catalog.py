from substanced.catalog.indexes import (
    FieldIndex,
    TextIndex,
    KeywordIndex,
    )

from substanced.catalog.discriminators import (
    get_textrepr,
    get_title,
    get_interfaces,
    )

def includeme(config):
    config.add_catalog_index('name', FieldIndex('__name__'))
    config.add_catalog_index('title', FieldIndex(get_title))
    config.add_catalog_index('interfaces', KeywordIndex(get_interfaces))
    config.add_catalog_index('texts', TextIndex(get_textrepr))

