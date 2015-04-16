import unittest
import mock
from pyramid import testing

import colander

class TestPropertySheet(unittest.TestCase):
    def _makeOne(self, context, request):
        from .. import PropertySheet
        return PropertySheet(context, request)

    def test_get(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.schema = [DummySchemaNode('title'),
                       DummySchemaNode('description'),
                       DummySchemaNode('another')]
        context.title = 'title'
        context.description = 'description'
        vals = inst.get()
        self.assertEqual(vals['title'], 'title')
        self.assertEqual(vals['description'], 'description')
        self.assertEqual(vals['another'], colander.null)

    def test_set(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        context.title = 'title'
        context.description = 'description'
        inst.schema = [DummySchemaNode('title'),
                       DummySchemaNode('description')]
        inst.set(dict(title='t', description='d'))
        self.assertEqual(context.title, 't')
        self.assertEqual(context.description, 'd')

    def test_set_schema_missing_value(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        context.title = 'title'
        context.description = 'description'
        inst.schema = [DummySchemaNode('title')]
        inst.set(dict(title='t', description='d'))
        self.assertEqual(context.title, 't')
        self.assertEqual(context.description, 'description')

    def test_set_nochange(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.schema = [DummySchemaNode('title'),
                       DummySchemaNode('description')]
        context.title = 't'
        context.description = 'd'
        inst.set(dict(title='t', description='d'))
        self.assertEqual(context.title, 't')
        self.assertEqual(context.description, 'd')

    def test_set_with_omit_iter(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        context.title = 'title'
        context.description = 'description'
        inst.schema = [DummySchemaNode('title'),
                       DummySchemaNode('description')]
        inst.set(dict(title='t', description='d'), omit=('title',))
        self.assertEqual(context.title, 'title')
        self.assertEqual(context.description, 'd')

    def test_set_with_omit_noniter(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        context.title = 'title'
        context.description = 'description'
        inst.schema = [DummySchemaNode('title'),
                       DummySchemaNode('description')]
        inst.set(dict(title='t', description='d'), omit='title')
        self.assertEqual(context.title, 'title')
        self.assertEqual(context.description, 'd')

    def test_after_set_changed_True(self):
        from substanced.event import ObjectModified
        request = testing.DummyRequest()
        request.registry = DummyRegistry()
        context = testing.DummyResource()
        inst = self._makeOne(context, request)
        inst.after_set(True)
        subscribed = request.registry.subscribed[0]
        self.assertEqual(subscribed[1], None)
        self.assertEqual(subscribed[0][0].__class__, ObjectModified)
        self.assertEqual(subscribed[0][1], context)

    def test_after_set_changed_False(self):
        request = testing.DummyRequest()
        request.registry = DummyRegistry()
        context = testing.DummyResource()
        inst = self._makeOne(context, request)
        inst.after_set(False)
        subscribed = request.registry.subscribed
        self.assertEqual(len(subscribed), 0)
        
class Test_is_propertied(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, resource, request):
        from .. import is_propertied
        return is_propertied(resource, request)

    def test_some(self):
        resource = Dummy()
        request = testing.DummyRequest()
        request.registry = DummyRegistry()
        request.registry.content = DummyContent(['sheet one', 'sheet two'])
        self.assertTrue(self._callFUT(resource, request))

    @mock.patch('substanced.property.get_domain')
    def test_None(self, mock_domain):
        mock_domain.all = lambda *arg: []
        resource = Dummy()
        request = testing.DummyRequest()
        request.registry = DummyRegistry()
        request.registry.content = DummyContent(None)
        result = self._callFUT(resource, request)
        self.assertFalse(result)

class Test_PropertiedPredicate(unittest.TestCase):
    def _makeOne(self, val, config):
        from .. import _PropertiedPredicate
        return _PropertiedPredicate(val, config)

    def test_text(self):
        config = Dummy()
        config.registry = Dummy()
        inst = self._makeOne(True, config)
        self.assertEqual(inst.text(), 'propertied = True')

    def test_phash(self):
        config = Dummy()
        config.registry = Dummy()
        inst = self._makeOne(True, config)
        self.assertEqual(inst.phash(), 'propertied = True')

    def test__call__(self):
        config = Dummy()
        request = testing.DummyRequest()
        request.registry = config.registry = Dummy()
        inst = self._makeOne(True, config)
        def is_propertied(context, request):
            self.assertEqual(context, None)
            self.assertEqual(request.registry, config.registry)
            return True
        inst.is_propertied = is_propertied
        self.assertEqual(inst(None, request), True)

class Test_get_domain(unittest.TestCase):
    def _makeRegistry(self, domain):
        registry = Dummy()
        registry.queryUtility = lambda self, *arg, **kw: domain
        def regUt(self, *args, **kw):
            registry.domainargs = (args, kw)
        registry.registerUtility = regUt
        return registry

    def _callFUT(self, registry):
        from substanced.property import get_domain
        return get_domain(registry)

    def test_domain_is_None(self):
        reg = self._makeRegistry(None)
        result = self._callFUT(reg)
        self.assertEqual(result.__class__.__name__, 'PredicateDomain')
        self.assertTrue(reg.domainargs)

    def test_domain_is_not_None(self):
        domain = object()
        reg = self._makeRegistry(domain)
        result = self._callFUT(reg)
        self.assertEqual(result, domain)

class Test_add_propertysheet(unittest.TestCase):
    def _callFUT(self, config, name, propsheet, iface=None, **predicates):
        from substanced.property import add_propertysheet
        return add_propertysheet(config, name, propsheet, iface, **predicates)

    @mock.patch('substanced.property.get_domain')
    def test_iface_is_None(self, mock_get_domain):
        from zope.interface import Interface
        domain = mock.Mock()
        cands = []
        domain.add_candidate = lambda *arg, **kw: cands.append((arg, kw))
        config = DummyConfig()
        config.registry = None
        propsheet = mock.Mock()
        mock_get_domain.return_value = domain
        result = self._callFUT(config, 'name', propsheet)
        self.assertEqual(result, propsheet)
        self.assertEqual(config.action_discrim, None)
        intr = config.action_kw['introspectables'][0]
        self.assertEqual(intr['propsheet'], propsheet)
        self.assertEqual(intr['interfaces'], Interface)
        config.action_callable()
        self.assertEqual(cands[0][0], (propsheet, Interface, Interface))
        self.assertEqual(cands[0][1], {'name':'name'})

    @mock.patch('substanced.property.get_domain')
    def test_iface_is_not_None(self, mock_get_domain):
        from zope.interface import Interface
        class IFoo(Interface): pass
        domain = mock.Mock()
        cands = []
        domain.add_candidate = lambda *arg, **kw: cands.append((arg, kw))
        config = DummyConfig()
        config.registry = None
        propsheet = mock.Mock()
        mock_get_domain.return_value = domain
        result = self._callFUT(config, 'name', propsheet, iface=IFoo)
        self.assertEqual(result, propsheet)
        self.assertEqual(config.action_discrim, None)
        intr = config.action_kw['introspectables'][0]
        self.assertEqual(intr['propsheet'], propsheet)
        self.assertEqual(intr['interfaces'], IFoo)
        config.action_callable()
        self.assertEqual(cands[0][0], (propsheet, IFoo, Interface))
        self.assertEqual(cands[0][1], {'name':'name'})

class Test_add_propertysheet_predicate(unittest.TestCase):
    def _callFUT(self, config, name, factory, before=None, after=None):
        from substanced.property import add_propertysheet_predicate
        return add_propertysheet_predicate(
            config, name, factory, before=before, after=after
            )

    @mock.patch('substanced.property.get_domain')
    def test_it(self, mock_get_domain):
        domain = mock.Mock()
        preds = []
        domain.add_predicate = lambda *arg, **kw: preds.append((arg, kw))
        mock_get_domain.return_value = domain
        config = DummyConfig()
        config.registry = None
        self._callFUT(config, 'name', 'factory', 'before', 'after')
        self.assertEqual(len(preds), 1)
        pred = preds[0]
        self.assertEqual(pred[0], ('name', 'factory'))
        self.assertEqual(pred[1], {'after':'after', 'before':'before'})

class Dummy(object):
    pass

class DummyConfig(object):
    _ainfo = None
    def maybe_dotted(self, val):
        return val

    def introspectable(self, *arg, **kw):
        self.intrargs = (arg, kw)
        return {}

    def action(self, action_discrim, action_callable, **action_kw):
        self.action_discrim = action_discrim
        self.action_callable = action_callable
        self.action_kw = action_kw

    def object_description(self, ob):
        return str(ob)

class DummyRegistry(object):
    def __init__(self):
        self.subscribed = []
    
    def subscribers(self, *args):
        self.subscribed.append(args)
        
class DummyContent(object):
    def __init__(self, result=None):
        self.result = result
        
    def metadata(self, *arg, **kw):
        return self.result

class DummySchemaNode(object):
    def __init__(self, name):
        self.name = name
