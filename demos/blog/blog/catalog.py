from substanced.event import subscribe_created
from substanced.catalog import (
    catalog_factory,
    indexview,
    indexview_defaults,
    Field,
    )
from substanced.root import Root

from .resources import (
    BlogEntry,
    Comment,
    )

@catalog_factory('blog')
class BlogCatalogFactory(object):
    pubdate = Field()

@subscribe_created(Root)
def created(event):
    root = event.object
    catalogs = root['catalogs']
    catalogs.add_catalog('blog', update_indexes=True)


@indexview_defaults(catalog_name='blog')
class BlogCatalogViews(object):
    def __init__(self, resource):
        self.resource = resource

    @indexview(context=BlogEntry)
    @indexview(context=Comment)
    def pubdate(self, default):
        return getattr(self.resource, 'pubdate', default)

