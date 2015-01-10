
import unittest


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
