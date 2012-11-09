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
        

class TestConflictingFlags(unittest.TestCase):
    def _makeOne(self, flag1, flag2):
        from . import ConflictingFlags
        return ConflictingFlags(flag1, flag2)

    def test___repr__(self):
        inst = self._makeOne('f1', 'f2')
        self.assertEqual(
            repr(inst),
            'Conflicting flags: f1 cannot be used when f2 is used'
            )
    
class TestNoSuchPackage(unittest.TestCase):
    def _makeOne(self, pkg_name):
        from . import NoSuchPackage
        return NoSuchPackage(pkg_name)

    def test___repr__(self):
        inst = self._makeOne('p1')
        self.assertEqual(
            repr(inst),
            'No such package named p1'
            )
        
class TestNoPackageSpecificed(unittest.TestCase):
    def _makeOne(self, arg):
        from . import NoPackageSpecified
        return NoPackageSpecified(arg)

    def test___repr__(self):
        inst = self._makeOne('p1')
        self.assertEqual(
            repr(inst),
            'No package specified: p1'
            )

class Test_importer(unittest.TestCase):
    def _callFUT(self, pkg_name):
        from . import importer
        return importer(pkg_name)

    def test_it(self):
        import substanced
        self.assertEqual(self._callFUT('substanced'), substanced)
    
class Test_evolve_packages(unittest.TestCase):
    def _callFUT(self, registry, root, **kw):
        from . import evolve_packages
        return evolve_packages(registry, root, **kw)

    def test_conflicting_flags_latest(self):
        from . import ConflictingFlags
        self.assertRaises(
            ConflictingFlags,
            self._callFUT, None, None, latest=True, set_db_version=1
            )
        
    def test_conflicting_flags_mark_all_current(self):
        from . import ConflictingFlags
        self.assertRaises(
            ConflictingFlags,
            self._callFUT, None, None, mark_all_current=True, set_db_version=1
            )

    def test_set_db_version_without_package(self):
        from . import NoPackageSpecified
        self.assertRaises(
            NoPackageSpecified,
            self._callFUT, None, None, set_db_version=1
            )

    def test_no_such_package_registered(self):
        from . import NoSuchPackage
        registry = DummyRegistry(result=())
        self.assertRaises(
            NoSuchPackage,
            self._callFUT, registry, None, package='fred',
            )
        
class DummyRegistry(object):
    def __init__(self, result):
        self.result = result

    def getUtilitiesFor(self, whatever):
        return self.result
