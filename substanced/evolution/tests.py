import unittest
from pyramid import testing

class Test_add_evolution_package(unittest.TestCase):
    def _callFUT(self, config, package_name):
        from . import add_evolution_package
        return add_evolution_package(config, package_name)

    def test_it(self):
        from repoze.evolution import ZODBEvolutionManager
        from repoze.evolution import IEvolutionManager
        config = testing.DummyResource()
        L = []
        def registerUtility(*arg, **kw):
            L.append((arg, kw))
        registry = testing.DummyResource(registerUtility=registerUtility)
        config.registry = registry
        self._callFUT(config, 'package')
        self.assertEqual(L, [((ZODBEvolutionManager, IEvolutionManager), 
                              {'name': 'package'})])
        
        
