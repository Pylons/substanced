import unittest

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
        inst = self._makeOne(lexicon=None, index=None)
        result = inst.hashvalues()
        self.assertEqual(
            result,
            {'index': None,
             'lexicon': None,
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

