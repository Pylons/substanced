import unittest

from pyramid import testing

class TestIndexingView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from  ..indexing import IndexingView
        return IndexingView(context, request)

    def test_show(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        context.__oid__ = 1
        context.__services__ = ('catalog',)
        catalog = DummyCatalog()
        context['catalog'] = catalog
        inst = self._makeOne(context, request)
        result = inst.show()
        self.assertEqual(
            result,
            {'catalogs':[(catalog, [{'index':catalog.index, 'value':'repr'}])]}
            )

    def test_reindex(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        def fwu(message, status):
            self.assertEqual(message, 'Object reindexed')
            self.assertEqual(status, 'success')
        token = request.session.new_csrf_token()
        request.POST['csrf_token'] = token
        request.flash_with_undo = fwu
        request.sdiapi = DummySDIAPI()
        context.__oid__ = 1
        context.__services__ = ('catalog',)
        catalog = DummyCatalog()
        context['catalog'] = catalog
        inst = self._makeOne(context, request)
        def vf(ctx, reg):
            self.assertEqual(ctx, context)
            self.assertEqual(reg, request.registry)
            return 'vf'
        inst.catalog_view_factory_for = vf
        result = inst.reindex()
        self.assertEqual(result.__class__.__name__, 'HTTPFound')
        self.assertEqual(catalog.oid, 1)
        self.assertEqual(catalog.wrapper.content, context)
        self.assertEqual(catalog.wrapper.view_factory, 'vf')

class DummyIndex(object):
    def document_repr(self, oid, default=None):
        return 'repr'

class DummyCatalog(object):
    def __init__(self):
        self.index = DummyIndex()

    def values(self):
        return (self.index,)

    def reindex_doc(self, oid, wrapper):
        self.oid = oid
        self.wrapper = wrapper

class DummySDIAPI(object):
    def mgmt_url(self, *arg, **kw):
        return 'http://mgmt_url'
