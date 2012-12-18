import unittest

class Test_set_yaml(unittest.TestCase):
    def _callFUT(self, registry):
        from . import set_yaml
        return set_yaml(registry)

    def test_loader_and_dumper_set(self):
        registry = DummyRegistry(None)
        self._callFUT(registry)
        self.assertEqual(registry.yaml_loader.__name__, 'SLoader')
        self.assertEqual(registry.yaml_dumper.__name__, 'SDumper')

    def test_iface_represente(self):
        registry = DummyRegistry(None)
        self._callFUT(registry)
        import StringIO
        io = StringIO.StringIO()
        import yaml
        yaml.dump(DummyInterface, io, Dumper=registry.yaml_dumper)
        self.assertEqual(
            io.getvalue(),
            "!interface 'substanced.dump.tests.DummyInterface'\n"
            )

    def test_iface_constructor(self):
        registry = DummyRegistry(None)
        self._callFUT(registry)
        import StringIO
        io = StringIO.StringIO(
            "!interface 'substanced.dump.tests.DummyInterface'\n"
            )
        import yaml
        result = yaml.load(io, Loader=registry.yaml_loader)
        self.assertEqual(result, DummyInterface)

class Test_get_dumpers(unittest.TestCase):
    def _callFUT(self, registry):
        from . import get_dumpers
        return get_dumpers(registry)

    def test_ordered_is_not_None(self):
        def f(n, reg):
            self.assertEqual(n, 1)
            self.assertEqual(reg, registry)
            return 'dumpers'
        registry = DummyRegistry([(1, f)])
        result = self._callFUT(registry)
        self.assertEqual(result, ['dumpers'])

    def test_ordered_is_None(self):
        def f(n, reg):
            self.assertEqual(n, 1)
            self.assertEqual(reg, registry)
            return 'dumpers'
        registry = DummyRegistry(None)
        registry._sd_dumpers = [(1, f, None, None)]
        result = self._callFUT(registry)
        self.assertEqual(result, ['dumpers'])
        self.assertEqual(registry.ordered, [(1, f)])

from zope.interface import Interface
        
class DummyInterface(Interface):
    pass
        
class DummyRegistry(object):
    def __init__(self, result):
        self.result = result

    def queryUtility(self, iface, default=None):
        return self.result

    def registerUtility(self, ordered, iface):
        self.ordered = ordered
    
