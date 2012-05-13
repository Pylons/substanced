import unittest
from pyramid import testing

class Test_macros(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self):
        from ..helpers import macros
        return macros()

    def test_it(self):
        val = self._callFUT()
        self.assertTrue('master' in val)
