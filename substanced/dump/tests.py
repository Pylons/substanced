import unittest
from pyramid import testing

class Test_set_yaml(unittest.TestCase):
    def _callFUT(self, registry):
        from . import set_yaml
        return set_yaml(registry)

    def test_loader_and_dumper_set(self):
        registry = DummyRegistry(None)
        self._callFUT(registry)
        self.assertEqual(registry['yaml_loader'].__name__, 'SLoader')
        self.assertEqual(registry['yaml_dumper'].__name__, 'SDumper')

    def test_iface_representer(self):
        registry = DummyRegistry(None)
        self._callFUT(registry)
        import StringIO
        io = StringIO.StringIO()
        import yaml
        yaml.dump(DummyInterface, io, Dumper=registry['yaml_dumper'])
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
        result = yaml.load(io, Loader=registry['yaml_loader'])
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

    def test__make_dump_context(self):
        inst = self._makeOne()
        c = inst._make_dump_context('dir', 'reg', 'dumpers', True, False)
        self.assertEqual(c.__class__.__name__, '_ResourceDumpContext')

    def test__make_load_context(self):
        inst = self._makeOne()
        c = inst._make_load_context('dir', 'reg', 'dumpers', True, False)
        self.assertEqual(c.__class__.__name__, '_ResourceLoadContext')

    def test_dump_no_subresources(self):
        inst = self._makeOne()
        resource = testing.DummyResource()
        context = DummyResourceDumpContext()
        inst._make_dump_context = lambda *arg, **kw: context
        inst.dump(resource, 'directory', subresources=False)
        self.assertEqual(context.dumped, resource)

    def test_dump_with_subresources_resource_is_not_folder(self):
        inst = self._makeOne()
        resource = testing.DummyResource()
        resource['a'] = testing.DummyResource()
        context = DummyResourceDumpContext()
        inst._make_dump_context = lambda *arg, **kw: context
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
        inst._make_dump_context = lambda *arg, **kw: context
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
        inst._make_dump_context = lambda *arg, **kw: context
        inst.dump(resource, 'directory', subresources=True)
        self.assertEqual(context.dumped, resource)

    def test_load_no_subresources(self):
        inst = self._makeOne()
        resource = testing.DummyResource()
        context = DummyResourceDumpContext(resource)
        inst._make_load_context = lambda *arg, **kw: context
        result = inst.load('directory', subresources=False)
        self.assertEqual(result, resource)

    def test_load_with_subresources(self):
        inst = self._makeOne()
        inst.ospath = DummyOSPath()
        inst.oslistdir = DummyOSListdir(['a'])
        resource = testing.DummyResource()
        context = DummyResourceDumpContext(resource)
        inst._make_load_context = lambda *arg, **kw: context
        result = inst.load('directory', subresources=True)
        self.assertEqual(result, resource)

    def test_load_loader_callbacks(self):
        inst = self._makeOne()
        resource = testing.DummyResource()
        def cb(rsrc):
            self.assertEqual(rsrc, resource)
        self.config.registry['loader_callbacks'] = [cb]
        context = DummyResourceDumpContext(resource)
        inst._make_load_context = lambda *arg, **kw: context
        result = inst.load('directory', subresources=False)
        self.assertEqual(result, resource)

class Test_FileOperations(unittest.TestCase):
    def _makeOne(self):
        from . import _FileOperations
        return _FileOperations()

    def test__makedirs(self):
        import os, tempfile, shutil
        inst = self._makeOne()
        try:
            td = tempfile.mkdtemp()
            dn = os.path.join(td, 'foo')
            inst._makedirs(dn)
            self.assertTrue(os.path.isdir(dn))
        finally:
            shutil.rmtree(td)

    def test__open(self):
        import os
        foo = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'fixture', 'foo.txt'
            )
        inst = self._makeOne()
        with inst._open(foo, 'rb') as fp:
            self.assertEqual(fp.read(), 'Foo.\n')
            
    def test__exists(self):
        import os
        foo = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'fixture', 'foo.txt'
            )
        inst = self._makeOne()
        self.assertTrue(inst._exists(foo))

    def test__get_fullpath_makedirs_true(self):
        import os
        inst = self._makeOne()
        prefix = os.path.dirname(os.path.abspath(__file__))
        def makedirs(dn):
            self.assertEqual(os.path.normpath(dn), os.path.normpath(prefix))
        inst._exists = lambda *arg: False
        inst._makedirs = makedirs
        inst.directory = os.path.join(prefix)
        result = inst._get_fullpath('bar', makedirs=True)
        self.assertEqual(result, os.path.join(prefix, 'bar'))

    def test__get_fullpath_makedirs_false(self):
        import os
        inst = self._makeOne()
        prefix = os.path.dirname(os.path.abspath(__file__))
        inst.directory = os.path.join(prefix)
        result = inst._get_fullpath('bar', makedirs=False)
        self.assertEqual(result, os.path.join(prefix, 'bar'))

    def test_openfile_w(self):
        inst = self._makeOne()
        def _get_fullpath(fn, makedirs):
            self.assertEqual(fn, 'a')
            self.assertEqual(makedirs, True)
            return fn
        inst._get_fullpath = _get_fullpath
        def _open(path, mode):
            self.assertEqual(path, 'a')
            self.assertEqual(mode, 'w')
            return 'fp'
        inst._open = _open
        self.assertEqual(inst.openfile_w('a'), 'fp')

    def test_openfile_r(self):
        inst = self._makeOne()
        def _get_fullpath(fn, makedirs=False):
            self.assertEqual(fn, 'a')
            self.assertEqual(makedirs, False)
            return fn
        inst._get_fullpath = _get_fullpath
        def _open(path, mode):
            self.assertEqual(path, 'a')
            self.assertEqual(mode, 'r')
            return 'fp'
        inst._open = _open
        self.assertEqual(inst.openfile_r('a'), 'fp')

    def test_exists(self):
        inst = self._makeOne()
        def _get_fullpath(fn, makedirs=False):
            self.assertEqual(fn, 'a')
            self.assertEqual(makedirs, False)
            return fn
        inst._get_fullpath = _get_fullpath
        def _exists(path):
            self.assertEqual(path, 'a')
            return True
        inst._exists = _exists
        self.assertEqual(inst.exists('a'), True)

class Test_YAMLOperations(unittest.TestCase):
    def _makeOne(self):
        from . import _YAMLOperations
        return _YAMLOperations()

    def test_load_yaml(self):
        import contextlib
        inst = self._makeOne()
        import StringIO
        io = StringIO.StringIO('foo 1')
        @contextlib.contextmanager
        def openfile(fn):
            self.assertEqual(fn, 'fn')
            yield io
        inst.openfile_r = openfile
        from yaml.loader import Loader
        inst.registry = {'yaml_loader':Loader}
        result = inst.load_yaml('fn')
        self.assertEqual(result, 'foo 1')

    def test_dump_yaml(self):
        import contextlib
        inst = self._makeOne()
        import StringIO
        io = StringIO.StringIO()
        @contextlib.contextmanager
        def openfile(fn):
            self.assertEqual(fn, 'fn')
            yield io
        inst.openfile_w = openfile
        from yaml.dumper import Dumper
        inst.registry = {'yaml_dumper':Dumper}
        result = inst.dump_yaml('abc', 'fn')
        self.assertEqual(result, None)
        self.assertEqual(io.getvalue(), 'abc\n...\n')

class Test_ResourceContext(unittest.TestCase):
    def _makeOne(self):
        from . import _ResourceContext
        return _ResourceContext()

    def test_resolve_dotted_name(self):
        import substanced.dump.tests
        inst = self._makeOne()
        result = inst.resolve_dotted_name('substanced.dump.tests')
        self.assertEqual(result, substanced.dump.tests)

    def test_get_dotted_name(self):
        import substanced.dump.tests
        inst = self._makeOne()
        result = inst.get_dotted_name(substanced.dump.tests)
        self.assertEqual(result, 'substanced.dump.tests')

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
