import unittest
from pyramid import testing
import colander

class Test_name_validator(unittest.TestCase):
    def _callFUT(self, node, kw):
        from ..views import name_validator
        return name_validator(node, kw)

    def _makeKw(self, exc=None):
        request = testing.DummyRequest()
        request.context = DummyFolder(exc)
        return dict(request=request)

    def test_it_exception(self):
        exc = KeyError('wrong')
        kw = self._makeKw(exc)
        node = object()
        v = self._callFUT(node, kw)
        self.assertRaises(colander.Invalid, v, node, 'abc')

    def test_it_no_exception(self):
        kw = self._makeKw()
        node = object()
        v = self._callFUT(node, kw)
        result = v(node, 'abc')
        self.assertEqual(result, None)

class TestAddFolderView(unittest.TestCase):
    def _makeOne(self, request):
        from ..views import AddFolderView
        return AddFolderView(request)

    def _makeRequest(self, resource):
        request = testing.DummyRequest()
        request.registry.content = DummyContent(resource)
        request.mgmt_path = lambda *arg: 'http://example.com'
        request.context = testing.DummyResource()
        return request

    def test_add_success(self):
        resource = testing.DummyResource()
        request = self._makeRequest(resource)
        inst = self._makeOne(request)
        resp = inst.add_success({'name':'name'})
        self.assertEqual(request.context['name'], resource)
        self.assertEqual(resp.location, 'http://example.com')

class Test_folder_contents(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, context, request):
        from ..views import folder_contents
        return folder_contents(context, request)

    def _makeRequest(self):
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        request.registry.content = DummyContent()
        return request
    
    def test_no_permissions(self):
        self.config.testing_securitypolicy(permissive=False)
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        result = self._callFUT(context, request)
        batchinfo = result['batchinfo']
        batch = batchinfo['batch']
        self.assertEqual(len(batch), 1)
        item = batch[0]
        self.assertEqual(item['url'], '/manage')
        self.assertFalse(item['viewable'])
        self.assertFalse(item['deletable'])
        self.assertEqual(item['icon'], 'icon')
        self.assertEqual(item['name'], 'a')

    def test_all_permissions(self):
        self.config.testing_securitypolicy(permissive=True)
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        result = self._callFUT(context, request)
        batchinfo = result['batchinfo']
        batch = batchinfo['batch']
        self.assertEqual(len(batch), 1)
        item = batch[0]
        self.assertEqual(item['url'], '/manage')
        self.assertTrue(item['viewable'])
        self.assertTrue(item['deletable'])
        self.assertEqual(item['icon'], 'icon')
        self.assertEqual(item['name'], 'a')

    def test_all_permissions_services_name(self):
        self.config.testing_securitypolicy(permissive=True)
        context = testing.DummyResource()
        context['__services__'] = testing.DummyResource()
        request = self._makeRequest()
        result = self._callFUT(context, request)
        batchinfo = result['batchinfo']
        batch = batchinfo['batch']
        self.assertEqual(len(batch), 1)
        item = batch[0]
        self.assertEqual(item['url'], '/manage')
        self.assertTrue(item['viewable'])
        self.assertFalse(item['deletable'])
        self.assertEqual(item['icon'], 'icon')
        self.assertEqual(item['name'], '__services__')

class Test_delete_folder_contents(unittest.TestCase):
    def _callFUT(self, context, request):
        from ..views import delete_folder_contents
        return delete_folder_contents(context, request)

    def _makeRequest(self):
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        request.registry.content = DummyContent()
        request.params['csrf_token'] = request.session.get_csrf_token()
        request.flash_undo = request.session.flash
        return request

    def test_none_deleted(self):
        context = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost()
        result = self._callFUT(context, request)
        self.assertEqual(request.session['_f_'], ['No items deleted'])
        self.assertEqual(result.location, '/manage')

    def test_one_deleted(self):
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('a',))
        result = self._callFUT(context, request)
        self.assertEqual(request.session['_f_'], ['Deleted 1 item'])
        self.assertEqual(result.location, '/manage')
        self.assertFalse('a' in context)

    def test_multiple_deleted(self):
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        context['b'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('a', 'b'))
        result = self._callFUT(context, request)
        self.assertEqual(request.session['_f_'], ['Deleted 2 items'])
        self.assertEqual(result.location, '/manage')
        self.assertFalse('a' in context)
        self.assertFalse('b' in context)

    def test_undeletable_item(self):
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('a', 'b'))
        result = self._callFUT(context, request)
        self.assertEqual(request.session['_f_'], ['Deleted 1 item'])
        self.assertEqual(result.location, '/manage')
        self.assertFalse('a' in context)
        
class DummyPost(dict):
    def __init__(self, result=()):
        self.result = result
        
    def getall(self, name):
        return self.result

class DummyFolder(object):
    def __init__(self, exc=None):
        self.exc = exc

    def check_name(self, name):
        if self.exc:
            raise self.exc
        return name

class DummyContent(object):
    def __init__(self, resource=None):
        self.resource = resource

    def create(self, iface, *arg, **kw):
        return self.resource

    def metadata(self, v, default=None):
        return default
    
        
        
