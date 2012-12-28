import unittest
from pyramid import testing

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
        registry['_sd_dumpers'] = [(1, f, None, None)]
        result = self._callFUT(registry)
        self.assertEqual(result, ['dumpers'])
        self.assertEqual(registry.ordered, [(1, f)])

class Test_DumpAndLoad(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self):
        from . import _DumpAndLoad
        return _DumpAndLoad()

    def test__make_context(self):
        inst = self._makeOne()
        c = inst._make_context('dir', 'reg', 'dumpers', True, False)
        self.assertEqual(c.__class__.__name__, 'ResourceDumpContext')

    def test_dump_no_subresources(self):
        inst = self._makeOne()
        resource = testing.DummyResource()
        context = DummyResourceDumpContext()
        inst._make_context = lambda *arg, **kw: context
        inst.dump(resource, 'directory', subresources=False)
        self.assertEqual(context.dumped, resource)

    def test_dump_with_subresources_resource_is_not_folder(self):
        inst = self._makeOne()
        resource = testing.DummyResource()
        resource['a'] = testing.DummyResource()
        context = DummyResourceDumpContext()
        inst._make_context = lambda *arg, **kw: context
        inst.dump(resource, 'directory', subresources=True)
        self.assertEqual(context.dumped, resource)

    def test_dump_with_subresources_resource_is_folder(self):
        from zope.interface import directlyProvides
        from substanced.interfaces import IFolder
        inst = self._makeOne()
        resource = testing.DummyResource()
        directlyProvides(resource, IFolder)
        resource['a'] = testing.DummyResource()
        context = DummyResourceDumpContext()
        inst._make_context = lambda *arg, **kw: context
        inst.dump(resource, 'directory', subresources=True)
        self.assertEqual(context.dumped, resource['a'])

    def test_dump_callbacks(self):
        from zope.interface import directlyProvides
        from substanced.interfaces import IFolder
        self.config.registry
        inst = self._makeOne()
        def callback(rsrc):
            self.assertEqual(rsrc, resource)
        self.config.registry['dumper_callbacks'] = [callback]
        resource = testing.DummyResource()
        directlyProvides(resource, IFolder)
        context = DummyResourceDumpContext()
        inst._make_context = lambda *arg, **kw: context
        inst.dump(resource, 'directory', subresources=True)
        self.assertEqual(context.dumped, resource)

    def test_load_no_subresources(self):
        inst = self._makeOne()
        resource = testing.DummyResource()
        context = DummyResourceDumpContext(resource)
        inst._make_context = lambda *arg, **kw: context
        result = inst.load('directory', subresources=False)
        self.assertEqual(result, resource)

    def test_load_with_subresources(self):
        inst = self._makeOne()
        inst.ospath = DummyOSPath()
        inst.oslistdir = DummyOSListdir(['a'])
        resource = testing.DummyResource()
        context = DummyResourceDumpContext(resource)
        inst._make_context = lambda *arg, **kw: context
        result = inst.load('directory', subresources=True)
        self.assertEqual(result, resource)

    def test_load_loader_callbacks(self):
        inst = self._makeOne()
        resource = testing.DummyResource()
        def cb(rsrc):
            self.assertEqual(rsrc, resource)
        self.config.registry['loader_callbacks'] = [cb]
        context = DummyResourceDumpContext(resource)
        inst._make_context = lambda *arg, **kw: context
        result = inst.load('directory', subresources=False)
        self.assertEqual(result, resource)

from zope.interface import Interface

class DummyResourceDumpContext(object):
    def __init__(self, result=None):
        self.result = result

    def dump(self, resource):
        self.dumped = resource

    def load(self, parent):
        return self.result
        
class DummyInterface(Interface):
    pass
        
class DummyRegistry(dict):
    def __init__(self, result):
        self.result = result
        dict.__init__(self)

    def queryUtility(self, iface, default=None):
        return self.result

    def registerUtility(self, ordered, iface):
        self.ordered = ordered

class DummyOSPath(object):
    def join(self, directory, other):
        return other

    def exists(self, dir):
        return True

    def abspath(self, path):
        return path

    def normpath(self, path):
        return path

    def isdir(self, dir):
        return True

class DummyOSListdir(object):
    def __init__(self, results):
        self.results = results

    def __call__(self, dir):
        if self.results:
            return self.results.pop(0)
        return []
