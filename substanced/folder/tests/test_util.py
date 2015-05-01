
import unittest

from pyramid import testing

class Test_slugify_in_context(unittest.TestCase):
    def _callFUT(self, context, name, remove_extension=True):
        from substanced.folder.util import slugify_in_context
        return slugify_in_context(context, name,
                                  remove_extension=remove_extension)

    def test_replace_nonword_characters(self):
        context = []
        self.assertEqual(
            self._callFUT(context, 'abcABC123'),
            'abcabc123'
            )
        self.assertEqual(
            self._callFUT(context, 'a.b,c d=e_f)g\th', remove_extension=False),
            'a-b-c-d-e_f-g-h'
            )
        self.assertEqual(
            self._callFUT(context, 'a&b&c d=e_f)g\th'),
            'a-b-c-d-e_f-g-h'
            )

    def test_uniquness_without_extension(self):
        context = {
            'bar': True,
            'boo': True,
            'boo-1': True,
            'boo-2': True,
            }
        self.assertEqual(
            self._callFUT(context, 'foo.txt'),
            'foo'
            )
        self.assertEqual(
            self._callFUT(context, 'bar.txt'),
            'bar-1'
            )
        self.assertEqual(
            self._callFUT(context, 'boo.txt'),
            'boo-3'
            )

    def test_uniquness_with_extension(self):
        context = {
            'bar-txt': True,
            'boo-pdf': True,
            'boo-pdf-1': True,
            'boo-pdf-2': True,
        }
        self.assertEqual(
            self._callFUT(context, 'foo.txt', remove_extension=False),
            'foo-txt'
            )
        self.assertEqual(
            self._callFUT(context, 'bar.txt', remove_extension=False),
            'bar-txt-1'
            )
        self.assertEqual(
            self._callFUT(context, 'boo.pdf', remove_extension=False),
            'boo-pdf-3'
            )


class Test_content_type_addable(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def call_it(self, context, request, content_type):
        from ..util import content_type_addable
        return content_type_addable(context, request, content_type)

    def test_true_if_sdi_addable_is_none(self):
        config = self.config
        config.include('substanced.content')
        config.add_content_type('Some Type', object)
        context = testing.DummyResource(__sdi_addable__=None)
        request = testing.DummyRequest()
        self.assertTrue(self.call_it(context, request, 'Some Type'))

    def test_with_callable_sdi_addable(self):
        config = self.config
        config.include('substanced.content')
        config.add_content_type('Type1', object, addable=True)
        config.add_content_type('Type2', object, addable=False)

        def addable(context, intr):
            meta = intr['meta']
            return meta.get('addable', False)

        context = testing.DummyResource(__sdi_addable__=addable)
        request = testing.DummyRequest()
        self.assertTrue(self.call_it(context, request, 'Type1'))
        self.assertFalse(self.call_it(context, request, 'Type2'))

    def test_with_sequence_sdi_addable(self):
        config = self.config
        config.include('substanced.content')
        config.add_content_type('Type1', object)
        config.add_content_type('Type2', object)

        context = testing.DummyResource(__sdi_addable__=('Type1',))
        request = testing.DummyRequest()
        self.assertTrue(self.call_it(context, request, 'Type1'))
        self.assertFalse(self.call_it(context, request, 'Type2'))

    def test_false_if_content_type_unknown(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        self.assertFalse(self.call_it(context, request, 'Unknown'))
