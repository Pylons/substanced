# import unittest

# class Test_text_index_factory(unittest.TestCase):
#     def _callFUT(self, name, category, **kw):
#         from .. import text_index_factory
#         return text_index_factory(name, category, **kw)

#     def test_it(self):
#         result = self._callFUT('name', 'category')
#         self.assertEqual(result.__class__.__name__, 'TextIndex')
#         self.assertEqual(result.sd_category, 'category')
#         self.assertEqual(result.discriminator.method_name, 'name')

#     def test_it_with_discrim(self):
#         result = self._callFUT('name', 'category', discriminator='abc')
#         self.assertEqual(result.__class__.__name__, 'TextIndex')
#         self.assertEqual(result.sd_category, 'category')
#         self.assertEqual(result.discriminator, 'abc')

# class Test_field_index_factory(unittest.TestCase):
#     def _callFUT(self, name, category, **kw):
#         from .. import field_index_factory
#         return field_index_factory(name, category, **kw)

#     def test_it(self):
#         result = self._callFUT('name', 'category')
#         self.assertEqual(result.__class__.__name__, 'FieldIndex')
#         self.assertEqual(result.sd_category, 'category')
#         self.assertEqual(result.discriminator.method_name, 'name')

#     def test_it_with_discrim(self):
#         result = self._callFUT('name', 'category', discriminator='abc')
#         self.assertEqual(result.__class__.__name__, 'FieldIndex')
#         self.assertEqual(result.sd_category, 'category')
#         self.assertEqual(result.discriminator, 'abc')

# class Test_keyword_index_factory(unittest.TestCase):
#     def _callFUT(self, name, category, **kw):
#         from .. import keyword_index_factory
#         return keyword_index_factory(name, category, **kw)

#     def test_it(self):
#         result = self._callFUT('name', 'category')
#         self.assertEqual(result.__class__.__name__, 'KeywordIndex')
#         self.assertEqual(result.sd_category, 'category')
#         self.assertEqual(result.discriminator.method_name, 'name')

#     def test_it_with_discrim(self):
#         result = self._callFUT('name', 'category', discriminator='abc')
#         self.assertEqual(result.__class__.__name__, 'KeywordIndex')
#         self.assertEqual(result.sd_category, 'category')
#         self.assertEqual(result.discriminator, 'abc')

# class Test_facet_index_factory(unittest.TestCase):
#     def _callFUT(self, name, category, **kw):
#         from .. import facet_index_factory
#         return facet_index_factory(name, category, **kw)

#     def test_it(self):
#         result = self._callFUT('name', 'category', facets=['abc'])
#         self.assertEqual(result.__class__.__name__, 'FacetIndex')
#         self.assertEqual(result.sd_category, 'category')
#         self.assertEqual(result.discriminator.method_name, 'name')

#     def test_it_with_discrim(self):
#         result = self._callFUT('name', 'category', discriminator='abc',
#             facets=['abc'])
#         self.assertEqual(result.__class__.__name__, 'FacetIndex')
#         self.assertEqual(result.sd_category, 'category')
#         self.assertEqual(result.discriminator, 'abc')

# class Test_allowed_index_factory(unittest.TestCase):
#     def _callFUT(self, name, category, **kw):
#         from .. import allowed_index_factory
#         return allowed_index_factory(name, category, **kw)

#     def test_it(self):
#         result = self._callFUT('name', 'category')
#         self.assertEqual(result.__class__.__name__, 'AllowedIndex')
#         self.assertEqual(result.sd_category, 'category')
#         self.assertEqual(result.discriminator.method_name, 'name')

#     def test_it_with_discrim(self):
#         result = self._callFUT('name', 'category', discriminator='abc')
#         self.assertEqual(result.__class__.__name__, 'AllowedIndex')
#         self.assertEqual(result.sd_category, 'category')
#         self.assertEqual(result.discriminator, 'abc')

# class Test_path_index_factory(unittest.TestCase):
#     def _callFUT(self, name, category, **kw):
#         from .. import path_index_factory
#         return path_index_factory(name, category, **kw)

#     def test_it(self):
#         result = self._callFUT('name', 'category')
#         self.assertEqual(result.__class__.__name__, 'PathIndex')
#         self.assertEqual(result.sd_category, 'category')

