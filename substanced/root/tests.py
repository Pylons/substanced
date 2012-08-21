import unittest
from pyramid import testing

class TestRoot(unittest.TestCase):
    def _makeOne(self, request):
        from . import Root
        return Root(request)

    def test_ctor(self):
        request = testing.DummyRequest()
        inst = self._makeOne(request)
        self.assertEqual(list(inst.items()), [])

