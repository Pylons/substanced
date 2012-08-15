import unittest

from pyramid import testing

from zope.interface import Interface

class IDummy(Interface):
    pass

class Test_FolderEventSubscriber(unittest.TestCase):
    
    event = IDummy

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, obj=None, container=None):
        from . import _FolderEventSubscriber
        class Subscriber(_FolderEventSubscriber):
            event = self.event
        return Subscriber(obj=obj, container=container)

    def test_register_object_only(self):
        class IFoo(Interface): pass
        class IBar(Interface): pass
        dec = self._makeOne(IFoo)
        def foo(event): pass
        config = DummyConfigurator()
        scanner = Dummy()
        scanner.config = config
        dec.register(scanner, None, foo)
        self.assertEqual(len(config.subscribed), 1)
        subscriber = config.subscribed[0]
        self.assertEqual(subscriber['wrapped'].wrapped, foo)
        self.assertEqual(subscriber['ifaces'],
                         [self.event, IFoo, Interface])

    def test_register_container_only(self):
        class IFoo(Interface): pass
        dec = self._makeOne(container=IFoo)
        def foo(event): pass
        config = DummyConfigurator()
        scanner = Dummy()
        scanner.config = config
        dec.register(scanner, None, foo)
        self.assertEqual(len(config.subscribed), 1)
        subscriber = config.subscribed[0]
        self.assertEqual(subscriber['wrapped'].wrapped, foo)
        self.assertEqual(subscriber['ifaces'],
                         [self.event, Interface, IFoo])

    def test_register_object_and_container(self):
        class IFoo(Interface): pass
        class IBar(Interface): pass
        dec = self._makeOne(obj=IFoo, container=IBar)
        def foo(event): pass
        config = DummyConfigurator()
        scanner = Dummy()
        scanner.config = config
        dec.register(scanner, None, foo)
        self.assertEqual(len(config.subscribed), 1)
        subscriber = config.subscribed[0]
        self.assertEqual(subscriber['wrapped'].wrapped, foo)
        self.assertEqual(subscriber['ifaces'],
                         [self.event, IFoo, IBar])

    def test_register_neither_object_nor_container(self):
        class IFoo(Interface): pass
        class IBar(Interface): pass
        dec = self._makeOne()
        def foo(event): pass
        config = DummyConfigurator()
        scanner = Dummy()
        scanner.config = config
        dec.register(scanner, None, foo)
        self.assertEqual(len(config.subscribed), 1)
        subscriber = config.subscribed[0]
        self.assertEqual(subscriber['wrapped'].wrapped, foo)
        self.assertEqual(subscriber['ifaces'],
                         [self.event, Interface, Interface])

    def test_register_wrapper(self):
        class IFoo(Interface): pass
        class IBar(Interface): pass
        dec = self._makeOne(IFoo)
        def foo(event):
            return 'abc'
        config = DummyConfigurator()
        scanner = Dummy()
        scanner.config = config
        dec.register(scanner, None, foo)
        subscriber = config.subscribed[0]
        wrapper = subscriber['wrapped']
        self.assertEqual(wrapper.wrapped, foo)
        event = Dummy()
        self.assertEqual(wrapper(event, None, None), 'abc')
        self.assertEqual(event.registry, scanner.config.registry)

    def test___call__(self):
        dec = self._makeOne()
        dummy_venusian = DummyVenusian()
        dec.venusian = dummy_venusian
        def foo(): pass
        dec(foo)
        self.assertEqual(dummy_venusian.attached,
                         [(foo, dec.register, 'substanced')])

class Dummy:
    pass
        
registry = Dummy()
class DummyConfigurator(object):
    def __init__(self):
        self.subscribed = []
        self.registry = registry

    def add_subscriber(self, wrapped, ifaces):
        self.subscribed.append({'wrapped':wrapped, 'ifaces':ifaces})

class DummyRegistry(object):
    pass
        
class DummyVenusian(object):
    def __init__(self):
        self.attached = []

    def attach(self, wrapped, fn, category=None):
        self.attached.append((wrapped, fn, category))

