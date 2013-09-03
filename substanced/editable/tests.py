import unittest

class TestFileEditable(unittest.TestCase):

    def _getTargetClass(self):
        from . import FileEditable
        return FileEditable

    def _makeOne(self, context=None, request=None):
        if context is None:
            context = object()
        if request is None:
            request = object()
        return self._getTargetClass()(context, request)

    def test_class_conforms_to_IEditable(self):
        from zope.interface.verify import verifyClass
        from . import IEditable
        verifyClass(IEditable, self._getTargetClass())

    def test_instance_conforms_to_IEditable(self):
        from zope.interface.verify import verifyObject
        from . import IEditable
        verifyObject(IEditable, self._makeOne())

    def test_get_context_has_mimetype(self):
        from pyramid.testing import DummyRequest
        from pyramid.testing import DummyResource
        context = DummyResource()
        context.mimetype = 'application/foo'
        blob = DummyResource()
        here = __file__
        def committed():
            return here
        blob.committed = committed
        context.blob = blob
        request = DummyRequest()
        inst = self._makeOne(context, request)
        iterable, mimetype = inst.get()
        self.assertEqual(mimetype, 'application/foo')
        self.assertEqual(type(next(iterable)), bytes)

    def test_get_context_has_no_mimetype(self):
        from pyramid.testing import DummyRequest
        from pyramid.testing import DummyResource
        context = DummyResource()
        context.mimetype = None
        blob = DummyResource()
        here = __file__
        def committed():
            return here
        blob.committed = committed
        context.blob = blob
        request = DummyRequest()
        inst = self._makeOne(context, request)
        iterable, mimetype = inst.get()
        self.assertEqual(mimetype, 'application/octet-stream')
        self.assertEqual(type(next(iterable)), bytes)

    def test_put(self):
        from pyramid.testing import DummyRequest
        from pyramid.testing import DummyResource
        context = DummyResource()
        fp = 'fp'
        def upload(_fp):
            self.assertEqual(_fp, fp)
        context.upload = upload
        request = DummyRequest()
        inst = self._makeOne(context, request)
        inst.put(fp)

class TestTextEditable(unittest.TestCase):

    def _getTargetClass(self):
        from . import TextEditable
        return TextEditable

    def _makeOne(self, context=None, request=None):
        if context is None:
            context = object()
        if request is None:
            request = object()
        return self._getTargetClass()(context, request)

    def test_class_conforms_to_IEditable(self):
        from zope.interface.verify import verifyClass
        from . import IEditable
        verifyClass(IEditable, self._getTargetClass())

    def test_instance_conforms_to_IEditable(self):
        from zope.interface.verify import verifyObject
        from . import IEditable
        verifyObject(IEditable, self._makeOne())

    def test_get_w_rst(self):
        from pyramid.testing import DummyRequest
        from pyramid.testing import DummyResource
        from pyramid.testing import testConfig
        from zope.interface import Interface
        from . import ISource
        context = DummyResource()
        request = DummyRequest()
        adapter = self._makeOne(context, request)
        with testConfig() as config:
            config.registry.registerAdapter(
                DummySource,
                (Interface, Interface),
                ISource,
                )
            body_iter, mimetype = adapter.get()
        chunks = list(body_iter)
        self.assertEqual(chunks[0], b'Subject: spelunking')
        self.assertEqual(chunks[1], b'=====')
        self.assertEqual(chunks[2], b'TITLE')
        self.assertEqual(chunks[3], b'=====')
        self.assertEqual(chunks[4], b'')
        self.assertEqual(chunks[5], b'BODY')
        self.assertEqual(mimetype, 'text/x-rst; charset=utf8')

    def test_get_w_html(self):
        from pyramid.testing import DummyRequest
        from pyramid.testing import DummyResource
        from pyramid.testing import testConfig
        from zope.interface import Interface
        from . import ISource
        context = DummyResource()
        request = DummyRequest()
        def _source_factory(context, reqeuest):
            source = DummySource(context, request)
            source._as_html = True
            return source
        adapter = self._makeOne(context, request)
        with testConfig() as config:
            config.registry.registerAdapter(
                _source_factory,
                (Interface, Interface),
                ISource,
                )
            body_iter, mimetype = adapter.get()
        chunks = list(body_iter)
        self.assertEqual(chunks[0], b'<html>')
        self.assertEqual(chunks[1], b'<head>')
        self.assertEqual(chunks[2], b'<title>TITLE</title>')
        self.assertEqual(chunks[3],
                         b'<meta type="Subject" value="spelunking" />')
        self.assertEqual(chunks[4], b'</head>')
        self.assertEqual(chunks[5], b'<body>')
        self.assertEqual(chunks[6], b'BODY')
        self.assertEqual(chunks[7], b'</body>')
        self.assertEqual(chunks[8], b'</html>')
        self.assertEqual(mimetype, 'text/html; charset=utf8')

    def test_put_w_rst(self):
        from io import BytesIO
        from pyramid.testing import DummyRequest
        from pyramid.testing import DummyResource
        from pyramid.testing import testConfig
        from zope.interface import Interface
        from . import ISource
        REST = BytesIO(b'\n'.join([b'Subject: spelunking',
                                   b'=====',
                                   b'TITLE',
                                   b'=====',
                                   b'',
                                   b'BODY']))
        context = DummyResource()
        request = DummyRequest()
        adapter = self._makeOne(context, request)
        with testConfig() as config:
            config.registry.registerAdapter(
                DummySource,
                (Interface, Interface),
                ISource,
                )
            adapter.put(REST)
        self.assertEqual(context.title, 'TITLE')
        self.assertEqual(context.meta, [('Subject', 'spelunking')])
        self.assertEqual(context.body, 'BODY')
        self.assertEqual(context.is_html, False)

    def test_put_w_html(self):
        from io import BytesIO
        from pyramid.testing import DummyRequest
        from pyramid.testing import DummyResource
        from pyramid.testing import testConfig
        from zope.interface import Interface
        from . import ISource
        context = DummyResource()
        request = DummyRequest()
        adapter = self._makeOne(context, request)
        REST = BytesIO(b'\n'.join([b'<html>',
                                   b'<head>',
                                   b'<title>TITLE</title>',
                                   b'<meta type="Subject" '
                                        b'value="spelunking" />',
                                   b'</head>',
                                   b'<body>',
                                   b'BODY',
                                   b'<a href="#">Link</a>',
                                   b'TAIL',
                                   b'</body>',
                                   b'</html>',
                                  ]))
        with testConfig() as config:
            config.registry.registerAdapter(
                DummySource,
                (Interface, Interface),
                ISource,
                )
            adapter.put(REST)
        self.assertEqual(context.title, 'TITLE')
        self.assertEqual(context.meta, [('Subject', 'spelunking')])
        self.assertEqual(context.body, 'BODY\n<a href="#">Link</a>\nTAIL')
        self.assertEqual(context.is_html, True)

class Test_register_editable_adapter(unittest.TestCase):

    def setUp(self):
        from pyramid.testing import setUp
        self.config = setUp()

    def tearDown(self):
        from pyramid.testing import tearDown
        tearDown()

    def _callFUT(self, config, adapter, iface):
        from . import register_editable_adapter
        return register_editable_adapter(config, adapter, iface)

    def test_it(self):
        from zope.interface import Interface
        from . import IEditable
        class ITesting(Interface):
            pass
        config = DummyConfigurator(self.config.registry)
        def _editable_factory(context, reqeust): #pragma NO COVER
            pass
        self._callFUT(config, _editable_factory, ITesting)
        self.assertEqual(len(config.actions), 1)
        action = config.actions[0]
        self.assertEqual(action['discriminator'],
                         ('sd-editable-adapter', ITesting))
        self.assertEqual(
            action['introspectables'], (config.intr,)
            )
        callable = action['callable']
        callable()
        wrapper = self.config.registry.adapters.lookup(
            (ITesting, Interface), IEditable)
        self.assertEqual(config.intr['registered'], wrapper)

class Test_register_source_adapter(unittest.TestCase):

    def setUp(self):
        from pyramid.testing import setUp
        self.config = setUp()

    def tearDown(self):
        from pyramid.testing import tearDown
        tearDown()

    def _callFUT(self, config, adapter, iface):
        from . import register_source_adapter
        return register_source_adapter(config, adapter, iface)

    def test_it(self):
        from zope.interface import Interface
        from . import IEditable
        from . import ISource
        from . import TextEditable
        class ITesting(Interface):
            pass
        config = DummyConfigurator(self.config.registry)
        def _source_factory(context, reqeust): #pragma NO COVER
            pass
        self._callFUT(config, _source_factory, ITesting)
        self.assertEqual(len(config.actions), 2)
        action = config.actions[0]
        self.assertEqual(action['discriminator'],
                         ('sd-source-adapter', ITesting))
        self.assertEqual(
            action['introspectables'], (config.intr,)
            )
        callable = action['callable']
        callable()
        wrapper = self.config.registry.adapters.lookup(
            (ITesting, Interface), ISource)
        self.assertEqual(config.intr['registered'], wrapper)

        action = config.actions[1]
        self.assertEqual(action['discriminator'],
                         ('sd-editable-adapter', ITesting))
        self.assertEqual(
            action['introspectables'], (config.intr,)
            )
        callable = action['callable']
        callable()
        wrapper = self.config.registry.adapters.lookup(
            (ITesting, Interface), IEditable)
        self.assertTrue(wrapper is TextEditable)

class DummyIntrospectable(dict):
    pass

class DummyConfigurator(object):
    _ainfo = None
    def __init__(self, registry):
        self.actions = []
        self.intr = DummyIntrospectable()
        self.registry = registry
        self.indexes = []

    def action(self, discriminator, callable, order=None, introspectables=()):
        self.actions.append(
            {
            'discriminator':discriminator,
            'callable':callable,
            'order':order,
            'introspectables':introspectables,
            })

    def introspectable(self, category, discriminator, name, single):
        return self.intr

class DummySource(object):
    _as_html = False
    def __init__(self, context, request):
        self.context = context
        self.request = request
    def renderAsHTML(self):
        return self._as_html
    def title(self):
        return 'TITLE'
    def metadata(self):
        return [('Subject', 'spelunking')]
    def body(self):
        return 'BODY'
    def apply(self, title, meta, body, is_html):
        self.context.title = title
        self.context.meta = meta
        self.context.body = body
        self.context.is_html = is_html
