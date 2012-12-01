import BTrees
from zope.interface import Interface
from pyramid.threadlocal import get_current_registry
from pyramid.compat import is_nonstr_iter
import venusian

from ..folder import Folder
from ..util import get_dotted_name

from .indexes import (
    TextIndex,
    FieldIndex,
    KeywordIndex,
    FacetIndex,
    AllowedIndex,
    PathIndex,
    )

from . import Catalog

_marker = object()

class ICatalogViewFactory(Interface):
    pass
    
class IndexDiscriminator(object):
    get_current_registry = staticmethod(get_current_registry) # for testing
    
    def __init__(self, catalog_name, index_name):
        self.catalog_name = catalog_name
        self.index_name = index_name

    def __call__(self, resource, default):
        registry = self.get_current_registry() # XXX lame
        catalog_view = registry.queryAdapter(
            resource,
            ICatalogViewFactory,
            name=self.catalog_name,
            default=None,
            )
        if catalog_view is not None:
            meth = getattr(catalog_view, self.index_name, _marker)
            if meth is not _marker:
                return meth(default)
            return default

class IndexFactory(object):
    def __init__(self, **kw):
        self.kw = kw

    def __call__(self, catalog_name, index_name):
        kw = self.kw
        kw['discriminator'] = IndexDiscriminator(catalog_name, index_name)
        index = self.index_type(**self.kw)
        index.__factory_hash__ = hash(self)
        return index

    def hashvalues(self):
        values = {}
        values.update(self.kw)
        values['class'] = get_dotted_name(self.__class__)
        family = values.get('family', None)
        if family is not None:
            if family == BTrees.family64:
                family = 'family64'
            elif family == BTrees.family32:
                family = 'family32'
            else:
                raise ValueError(family)
            values['family'] = family
        return values

    def __hash__(self):
        values = tuple(sorted(self.hashvalues().items()))
        return hash(values)

class Text(IndexFactory):
    index_type = TextIndex

    def hashvalues(self):
        values = IndexFactory.hashitems(self)
        for name in ('lexicon', 'index'):
            attr = values.get(name, None)
            if attr is not None:
                clsname = attr.__class__.__name__
                values[name] = clsname
        return values

class Field(IndexFactory):
    index_type = FieldIndex
    
class Keyword(IndexFactory):
    index_type = KeywordIndex

class Facet(IndexFactory):
    index_type = FacetIndex

    def hashvalues(self):
        values = IndexFactory.hashitems(self)
        facets = values.get('facets', ())
        values['facets'] = tuple(sorted([(x,y) for x, y in facets]))
        return values.items()

class Allowed(IndexFactory):
    index_type = AllowedIndex

    def hashvalues(self):
        values = IndexFactory.hashitems(self)
        permissions = values.get('permissions', None)
        if not is_nonstr_iter(permissions):
            permissions = (permissions,)
        values['permissions'] = tuple(sorted(permissions))
        return values

class Path(IndexFactory):
    index_type = PathIndex

class CatalogsService(Folder):
    pass # XXX not really just a folder

class CatalogFactory(object):
    def __init__(self, name, **index_factories):
        self.name = name
        self.index_factories = index_factories

    def _get_catalog(self, folder):
        if not 'catalogs' in folder:
            folder['catalogs'] = CatalogsService()

        catalogs = folder['catalogs']

        if not self.name in catalogs:
            catalogs[self.name] = Catalog()

        catalog = catalogs[self.name]
        return catalog

    def _remove_stale(self, catalog):
        for index_name, index in catalog.items():
            if not index_name in self.index_factories:
                del catalog[index_name]

    def replace(self, folder, reindex=False):
        catalog = self._get_catalog(folder)

        for index_name, index_factory in self.index_factories.items():
            catalog[index_name] = index_factory(self.name, index_name)

        self._remove_stale(catalog)

        if reindex:
            catalog.reindex()

    def sync(self, folder, reindex=False):
        catalog = self._get_catalog(folder)

        to_reindex = []

        for index_name, index_factory in self.index_factories.items():
            if not index_name in catalog:
                index = catalog[index_name] = index_factory(
                    self.name, index_name
                    )

            index = catalog[index_name]

            if index.__factory_hash__ != hash(index_factory):
                catalog.replace(
                    index_name,
                    index_factory(
                        self.name, index_name
                        )
                    )
                to_reindex.append(index_name)

        self._remove_stale(catalog)

        if reindex:
            catalog.reindex(indexes=to_reindex)

class catalog_factory(object):
    depth = 1
    venusian = venusian # for testing injection

    def __init__(self, name):
        self.name = name

    def __call__(self, cls):
        index_factories = {}
        for name in dir(cls):
            value = getattr(cls, name, None)
            if isinstance(value, IndexFactory):
                index_factories[name] = value
                
        factory = CatalogFactory(self.name, index_factories)

        extra = {}

        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            config.add_catalog_factory(self.name, factory, **extra)

        info = self.venusian.attach(factory, callback, category='substanced')

        extra['_info'] = info.codeinfo # fbo "action_method"
        extra['_depth'] = self.depth

        return factory

class ICatalogFactory(Interface):
    pass

def add_catalog_factory(config, name, factory):
    def add_catalog_factory():
        config.registry.registerUtility(factory, ICatalogFactory, name)

    discriminator = ('sd-catalog-factory', name)
    intr = config.introspectable(
        'sd catalog factories',
        discriminator,
        name,
        'sd catalog factory'
        )
    intr['name'] = name
    intr['factory'] = factory
    config.action(
        discriminator, 
        callable=add_catalog_factory,
        introspectables=(intr,)
        )
    

@catalog_factory('kuiu')
class KUIUCatalog(object):
    texts = Text()
    title = Field()
    order_date = Field()
    warehoused = Field()
    billing_text = Text()
    shipping_text = Text()
    processing_status = Field()
    billing_status = Field()
    amount = Field()
    ship_date = Field()
    skus = Keyword()
    email = Field()
    customer_type = Field()
    
