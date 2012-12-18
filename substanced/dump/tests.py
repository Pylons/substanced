import unittest

class Test_set_yaml(unittest.TestCase):
    def _callFUT(self, registry):
        from . import set_yaml
        return set_yaml(registry)

    def test_loader_and_dumper_set(self):
        registry = DummyRegistry()
        self._callFUT(registry)
        self.assertEqual(registry.yaml_loader.__name__, 'SLoader')
        self.assertEqual(registry.yaml_dumper.__name__, 'SDumper')

    def test_iface_represente(self):
        registry = DummyRegistry()
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
        registry = DummyRegistry()
        self._callFUT(registry)
        import StringIO
        io = StringIO.StringIO(
            "!interface 'substanced.dump.tests.DummyInterface'\n"
            )
        import yaml
        result = yaml.load(io, Loader=registry.yaml_loader)
        self.assertEqual(result, DummyInterface)

from zope.interface import Interface
        
class DummyInterface(Interface):
    pass
        
class DummyRegistry(object):
    pass
