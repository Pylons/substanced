import unittest
from pyramid import testing

class TestIndexFactory(unittest.TestCase):
    def _makeOne(self, **kw):
        from ..factories import IndexFactory
        inst = IndexFactory(**kw)
        def index_type(discriminator, **kw):
            return inst.idx
        inst.index_type = index_type
        inst.idx = testing.DummyResource()
        return inst

    def test_ctor(self):
        inst = self._makeOne(a=1)
        self.assertEqual(inst.kw, {'a':1})

    def test_call_and_hash(self):
        inst = self._makeOne(a=1)
        index = inst('catalog', 'index')
        self.assertEqual(index, inst.idx)
        self.assertEqual(index.__factory_hash__, hash(inst))

    def test_hashvalues_family32(self):
        import BTrees
        inst = self._makeOne(a=1, family=BTrees.family32)
        values = inst.hashvalues()
        self.assertEqual(
            values,
            {'a':1,
             'family':'family32',
             'class':'substanced.catalog.factories.IndexFactory'}
            )

    def test_hashvalues_family64(self):
        import BTrees
        inst = self._makeOne(a=1, family=BTrees.family64)
        values = inst.hashvalues()
        self.assertEqual(
            values,
            {'a':1,
             'family':'family64',
             'class':'substanced.catalog.factories.IndexFactory'}
            )

    def test_hashvalues_family_unknown(self):
        inst = self._makeOne(a=1, family=True)
        self.assertRaises(ValueError, inst.hashvalues)

class TestText(unittest.TestCase):
    def _makeOne(self, **kw):
        from ..factories import Text
        return Text(**kw)

    def test_call(self):
        inst = self._makeOne()
        result = inst('catalog', 'index')
        self.assertEqual(result.__class__.__name__, 'TextIndex')
        self.assertEqual(
            result.discriminator.__class__.__name__,
            'IndexViewDiscriminator'
            )
        self.assertTrue(hasattr(result, '__factory_hash__'))

    def test_hashvalues(self):
        inst = self._makeOne()
        result = inst.hashvalues()
        self.assertEqual(
            result,
            {'class': 'substanced.catalog.factories.Text'}
            )

    def test_hashvalues_with_lexicon_and_index(self):
        dummy = testing.DummyResource()
        inst = self._makeOne(lexicon=dummy, index=dummy)
        result = inst.hashvalues()
        self.assertEqual(
            result,
            {'index': 'DummyResource',
             'lexicon': 'DummyResource',
             'class': 'substanced.catalog.factories.Text'}
            )

        
class TestField(unittest.TestCase):
    def _makeOne(self, **kw):
        from ..factories import Field
        return Field(**kw)

    def test_call(self):
        inst = self._makeOne()
        result = inst('catalog', 'index')
        self.assertEqual(result.__class__.__name__, 'FieldIndex')
        self.assertEqual(
            result.discriminator.__class__.__name__,
            'IndexViewDiscriminator'
            )
        self.assertTrue(hasattr(result, '__factory_hash__'))

    def test_hashvalues(self):
        inst = self._makeOne()
        result = inst.hashvalues()
        self.assertEqual(
            result,
            {'class': 'substanced.catalog.factories.Field'}
            )

class TestKeyword(unittest.TestCase):
    def _makeOne(self, **kw):
        from ..factories import Keyword
        return Keyword(**kw)

    def test_call(self):
        inst = self._makeOne()
        result = inst('catalog', 'index')
        self.assertEqual(result.__class__.__name__, 'KeywordIndex')
        self.assertEqual(
            result.discriminator.__class__.__name__,
            'IndexViewDiscriminator'
            )
        self.assertTrue(hasattr(result, '__factory_hash__'))

    def test_hashvalues(self):
        inst = self._makeOne()
        result = inst.hashvalues()
        self.assertEqual(
            result,
            {'class': 'substanced.catalog.factories.Keyword'}
            )

class TestFacet(unittest.TestCase):
    def _makeOne(self, **kw):
        from ..factories import Facet
        return Facet(**kw)

    def test_call(self):
        inst = self._makeOne(facets=[(1,2)])
        result = inst('catalog', 'index')
        self.assertEqual(result.__class__.__name__, 'FacetIndex')
        self.assertEqual(
            result.discriminator.__class__.__name__,
            'IndexViewDiscriminator'
            )
        self.assertTrue(hasattr(result, '__factory_hash__'))

    def test_hashvalues(self):
        inst = self._makeOne(facets=[(1,2)])
        result = inst.hashvalues()
        self.assertEqual(
            result,
            {'class': 'substanced.catalog.factories.Facet',
             'facets':((1,2),)}
            )

class TestPath(unittest.TestCase):
    def _makeOne(self, **kw):
        from ..factories import Path
        return Path(**kw)

    def test_call(self):
        inst = self._makeOne()
        result = inst('catalog', 'index')
        self.assertEqual(result.__class__.__name__, 'PathIndex')
        self.assertTrue(hasattr(result, '__factory_hash__'))

    def test_hashvalues(self):
        inst = self._makeOne()
        result = inst.hashvalues()
        self.assertEqual(
            result,
            {'class': 'substanced.catalog.factories.Path'}
            )

class TestAllowed(unittest.TestCase):
    def _makeOne(self, **kw):
        from ..factories import Allowed
        return Allowed(**kw)

    def test_call(self):
        inst = self._makeOne(permissions=['a',])
        result = inst('catalog', 'index')
        self.assertEqual(result.__class__.__name__, 'AllowedIndex')
        self.assertTrue(hasattr(result, '__factory_hash__'))
        self.assertEqual(result.discriminator.permissions, set(['a']))

    def test_hashvalues_noniter_permissions(self):
        inst = self._makeOne(permissions='a')
        result = inst.hashvalues()
        self.assertEqual(
            result,
            {'class': 'substanced.catalog.factories.Allowed',
             'permissions': ('a',)}
            )
        
    def test_hashvalues_iter_permissions(self):
        inst = self._makeOne(permissions=['b', 'a'])
        result = inst.hashvalues()
        self.assertEqual(
            result,
            {'class': 'substanced.catalog.factories.Allowed',
             'permissions': ('a','b')}
            )
        
