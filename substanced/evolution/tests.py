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

    def test_dryrun(self):
        manager = DummyManager(0)
        factory = DummyFactory(manager)
        registry = DummyRegistry([('fred', factory)])
        module = DummyModule(VERSION=1, NAME='fred')
        importer = DummyFactory(module)
        result = self._callFUT(
            registry, None, package='fred', importer=importer
            )
        self.assertEqual(
            result,
            [{'db_version': 0,
              'sw_version': 1,
              'message': 'Not evolving (latest not specified)',
              'new_version': 0,
              'package': 'fred'}]
            )

    def test_latest(self):
        manager = DummyManager(0)
        factory = DummyFactory(manager)
        registry = DummyRegistry([('fred', factory)])
        module = DummyModule(VERSION=1, NAME='fred')
        importer = DummyFactory(module)
        result = self._callFUT(
            registry, None, package='fred', latest=True, importer=importer
            )
        self.assertEqual(
            result,
            [{'db_version': 0,
              'sw_version': 1,
              'message': 'Evolved fred to 0',
              'new_version': 0,
              'package': 'fred'}]
            )

    def test_mark_all_current(self):
        manager = DummyManager(0)
        factory = DummyFactory(manager)
        registry = DummyRegistry([('fred', factory)])
        module = DummyModule(VERSION=1, NAME='fred')
        importer = DummyFactory(module)
        result = self._callFUT(
            registry, None, package='fred', mark_all_current=True,
            importer=importer
            )
        self.assertEqual(
            result,
            [{'db_version': 0,
              'sw_version': 1,
              'message': 'Evolved fred to 1',
              'new_version': 1,
              'package': 'fred'}]
            )
        self.assertEqual(manager.db_version, 1)

    def test_set_db_version_eq_db_version(self):
        manager = DummyManager(1)
        factory = DummyFactory(manager)
        registry = DummyRegistry([('fred', factory)])
        module = DummyModule(VERSION=1, NAME='fred')
        importer = DummyFactory(module)
        result = self._callFUT(
            registry, None, package='fred', set_db_version=1,
            importer=importer
            )
        self.assertEqual(
            result,
            [{'db_version': 1,
              'sw_version': 1,
              'message': 'Nothing to do',
              'new_version': 1,
              'package': 'fred'}]
            )

    def test_set_db_version_gt_db_version(self):
        manager = DummyManager(0)
        factory = DummyFactory(manager)
        registry = DummyRegistry([('fred', factory)])
        module = DummyModule(VERSION=1, NAME='fred')
        importer = DummyFactory(module)
        result = self._callFUT(
            registry, None, package='fred', set_db_version=1,
            importer=importer
            )
        self.assertEqual(
            result,
            [{'db_version': 0,
              'sw_version': 1,
              'message': 'Database version set to 1',
              'new_version': 1,
              'package': 'fred'}]
            )

    def test_substanced_first_sorting_hack(self):
        manager = DummyManager(0)
        factory = DummyFactory(manager)
        registry = DummyRegistry([('fred', factory),
                                  ('substanced.evolution', factory)])
        module = DummyModule(VERSION=1, NAME='fred')
        importer = DummyFactory(module)
        result = self._callFUT(
            registry, None, latest=True, importer=importer
            )
        self.assertEqual(
            result,
            [   # substanced resorted first
                {'db_version': 0,
                 'sw_version': 1,
                 'message': 'Evolved substanced.evolution to 0',
                 'new_version': 0,
                 'package': 'substanced.evolution'},
                {'db_version': 0,
                 'sw_version': 1,
                 'message': 'Evolved fred to 0',
                 'new_version': 0,
                 'package': 'fred'}
                ]
            )

class DummyModule(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)

class DummyRegistry(object):
    def __init__(self, result):
        self.result = result

    def getUtilitiesFor(self, whatever):
        return self.result

class DummyFactory(object):
    def __init__(self, result):
        self.result = result

    def __call__(self, *arg, **kw):
        return self.result

class DummyManager(object):
    def __init__(self, result):
        self.result = result

    def get_db_version(self):
        return self.result

    def get_sw_version(self):
        return self.result

    def _set_db_version(self, version):
        self.db_version = version

    
