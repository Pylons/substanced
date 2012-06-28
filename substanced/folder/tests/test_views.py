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

class Test_rename_duplicated_resource(unittest.TestCase):
    def test_rename_first(self):
        from ..views import rename_duplicated_resource
        context = testing.DummyResource()
        new_name = rename_duplicated_resource(context, 'foobar')
        self.assertEqual(new_name, 'foobar')

    def test_rename_second(self):
        from ..views import rename_duplicated_resource
        context = testing.DummyResource()
        context['foobar'] = testing.DummyResource()
        new_name = rename_duplicated_resource(context, 'foobar')
        self.assertEqual(new_name, 'foobar-1')

    def test_rename_twentyfirst(self):
        from ..views import rename_duplicated_resource
        context = testing.DummyResource()
        context['foobar-21'] = testing.DummyResource()
        new_name = rename_duplicated_resource(context, 'foobar-21')
        self.assertEqual(new_name, 'foobar-22')

    def test_rename_multiple_dashes(self):
        from ..views import rename_duplicated_resource
        context = testing.DummyResource()
        context['foo-bar'] = testing.DummyResource()
        new_name = rename_duplicated_resource(context, 'foo-bar')
        self.assertEqual(new_name, 'foo-bar-1')

    def test_rename_take_fisrt_available(self):
        from ..views import rename_duplicated_resource
        context = testing.DummyResource()
        context['foobar'] = testing.DummyResource()
        context['foobar-1'] = testing.DummyResource()
        context['foobar-2'] = testing.DummyResource()
        context['foobar-4'] = testing.DummyResource()
        new_name = rename_duplicated_resource(context, 'foobar')
        self.assertEqual(new_name, 'foobar-3')

class TestAddFolderView(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..views import AddFolderView
        return AddFolderView(context, request)

    def _makeRequest(self, resource):
        request = testing.DummyRequest()
        request.registry.content = DummyContent(resource)
        request.mgmt_path = lambda *arg: 'http://example.com'
        return request

    def test_add_success(self):
        resource = testing.DummyResource()
        request = self._makeRequest(resource)
        context = testing.DummyResource()
        inst = self._makeOne(context, request)
        resp = inst.add_success({'name': 'name'})
        self.assertEqual(context['name'], resource)
        self.assertEqual(resp.location, 'http://example.com')

class TestFolderContentsViews(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..views import FolderContentsViews
        return FolderContentsViews(context, request)

    def _makeRequest(self):
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        request.registry.content = DummyContent()
        request.flash_with_undo = request.session.flash
        return request

    def test_show_no_permissions(self):
        self.config.testing_securitypolicy(permissive=False)
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        inst = self._makeOne(context, request)
        inst.get_add_views = lambda *arg: ()
        result = inst.show()
        batch = result['batch']
        self.assertEqual(len(batch.items), 1)
        item = batch.items[0]
        self.assertEqual(item['url'], '/manage')
        self.assertFalse(item['viewable'])
        self.assertFalse(item['modifiable'])
        self.assertEqual(item['icon'], 'icon')
        self.assertEqual(item['name'], 'a')

    def test_show_all_permissions(self):
        self.config.testing_securitypolicy(permissive=True)
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        inst = self._makeOne(context, request)
        inst.get_add_views = lambda *arg: ()
        result = inst.show()
        batch = result['batch']
        self.assertEqual(len(batch.items), 1)
        item = batch.items[0]
        self.assertEqual(item['url'], '/manage')
        self.assertTrue(item['viewable'])
        self.assertTrue(item['modifiable'])
        self.assertEqual(item['icon'], 'icon')
        self.assertEqual(item['name'], 'a')

    def test_show_all_permissions_services_name(self):
        self.config.testing_securitypolicy(permissive=True)
        context = testing.DummyResource()
        context['__services__'] = testing.DummyResource()
        request = self._makeRequest()
        inst = self._makeOne(context, request)
        inst.get_add_views = lambda *arg: ()
        result = inst.show()
        batch = result['batch']
        self.assertEqual(len(batch.items), 1)
        item = batch.items[0]
        self.assertEqual(item['url'], '/manage')
        self.assertTrue(item['viewable'])
        self.assertFalse(item['modifiable'])
        self.assertEqual(item['icon'], 'icon')
        self.assertEqual(item['name'], '__services__')

    def test_delete_none_deleted(self):
        context = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost()
        inst = self._makeOne(context, request)
        result = inst.delete()
        self.assertEqual(request.session['_f_'], ['No items deleted'])
        self.assertEqual(result.location, '/manage')

    def test_delete_one_deleted(self):
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('a',))
        inst = self._makeOne(context, request)
        result = inst.delete()
        self.assertEqual(request.session['_f_'], ['Deleted 1 item'])
        self.assertEqual(result.location, '/manage')
        self.assertFalse('a' in context)

    def test_delete_multiple_deleted(self):
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        context['b'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('a', 'b'))
        inst = self._makeOne(context, request)
        result = inst.delete()
        self.assertEqual(request.session['_f_'], ['Deleted 2 items'])
        self.assertEqual(result.location, '/manage')
        self.assertFalse('a' in context)
        self.assertFalse('b' in context)

    def test_delete_undeletable_item(self):
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('a', 'b'))
        inst = self._makeOne(context, request)
        result = inst.delete()
        self.assertEqual(request.session['_f_'], ['Deleted 1 item'])
        self.assertEqual(result.location, '/manage')
        self.assertFalse('a' in context)

    def test_duplicate_multiple(self):
        from .. import Folder
        context = Folder()
        context['a'] = DummyExportableResource()
        context['b'] = DummyExportableResource()
        context['c'] = DummyExportableResource()
        request = self._makeRequest()
        request.POST = DummyPost(('a', 'b'))
        inst = self._makeOne(context, request)
        result = inst.duplicate()
        self.assertEqual(request.session['_f_'], ['Duplicated 2 items'])
        self.assertEqual(result.location, '/manage')
        self.assertTrue('a' in context)
        self.assertTrue('a-1' in context)
        self.assertTrue('b' in context)
        self.assertTrue('b-1' in context)
        self.assertTrue('c' in context)

    def test_duplicate_none(self):
        from .. import Folder
        context = Folder()
        context['a'] = DummyExportableResource()
        request = self._makeRequest()
        request.POST = DummyPost()
        inst = self._makeOne(context, request)
        result = inst.duplicate()
        self.assertEqual(request.session['_f_'], ['No items duplicated'])
        self.assertEqual(result.location, '/manage')
        self.assertTrue('a' in context)
        self.assertFalse('a-1' in context)

    def test_duplicate_one(self):
        from .. import Folder
        context = Folder()
        context['a'] = DummyExportableResource()
        context['b'] = DummyExportableResource()
        request = self._makeRequest()
        request.POST = DummyPost(('a',))
        inst = self._makeOne(context, request)
        result = inst.duplicate()
        self.assertEqual(request.session['_f_'], ['Duplicated 1 item'])
        self.assertEqual(result.location, '/manage')
        self.assertTrue('a' in context)
        self.assertTrue('a-1' in context)
        self.assertTrue('b' in context)
        self.assertFalse('b-1' in context)

    def test_duplicate_chain(self):
        from .. import Folder
        context = Folder()
        context['a'] = DummyExportableResource()
        context['b'] = DummyExportableResource()
        request = self._makeRequest()
        request.POST = DummyPost(('a',))
        inst = self._makeOne(context, request)
        inst.duplicate()
        result = inst.duplicate()
        self.assertEqual(request.session['_f_'], ['Duplicated 1 item', 'Duplicated 1 item'])
        self.assertEqual(result.location, '/manage')
        self.assertTrue('a' in context)
        self.assertTrue('a-1' in context)
        self.assertTrue('a-2' in context)
        self.assertTrue('b' in context)
        self.assertFalse('b-1' in context)

    def test_duplicate_double(self):
        from .. import Folder
        context = Folder()
        context['a'] = DummyExportableResource()
        context['a-1'] = DummyExportableResource()
        context['b'] = DummyExportableResource()
        request = self._makeRequest()
        request.POST = DummyPost(('a-1',))
        inst = self._makeOne(context, request)
        result = inst.duplicate()
        self.assertEqual(request.session['_f_'], ['Duplicated 1 item'])
        self.assertEqual(result.location, '/manage')
        self.assertTrue('a' in context)
        self.assertTrue('a-1' in context)
        self.assertTrue('a-2' in context)
        self.assertTrue('b' in context)
        self.assertFalse('b-1' in context)

    def test_duplicate_subfolder(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = DummyExportableResource()
        context['foobar']['a'] = DummyExportableResource()
        context['foobar']['b'] = DummyExportableResource()
        request = self._makeRequest()
        request.POST = DummyPost(('foobar',))
        inst = self._makeOne(context, request)
        result = inst.duplicate()
        self.assertEqual(request.session['_f_'], ['Duplicated 1 item'])
        self.assertEqual(result.location, '/manage')
        self.assertTrue('foobar' in context)
        self.assertTrue('foobar-1' in context)
        self.assertEqual(context['foobar-1'].keys(), ['a', 'b'])

    def test_rename_one(self):
        context = testing.DummyResource()
        context['foobar'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('foobar',))
        inst = self._makeOne(context, request)
        result = inst.rename()
        self.assertEqual(result, {'torename': [context['foobar']]})

    def test_rename_multiple(self):
        context = testing.DummyResource()
        context['foobar'] = testing.DummyResource()
        context['foobar2'] = testing.DummyResource()
        context['foobar3'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('foobar', 'foobar3'))
        inst = self._makeOne(context, request)
        result = inst.rename()
        self.assertEqual(result, {'torename': [context['foobar'], context['foobar3']]})

    def test_rename_none(self):
        context = testing.DummyResource()
        context['foobar'] = testing.DummyResource()
        context['foobar2'] = testing.DummyResource()
        context['foobar3'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost()
        inst = self._makeOne(context, request)
        result = inst.rename()
        self.assertEqual(request.session['_f_'], ['No items renamed'])
        self.assertEqual(result.location, '/manage')

    def test_rename_finish_success(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('foobar',), {'foobar': 'foobar2',
                                               'form.rename_finish': 'rename_finish'})
        inst = self._makeOne(context, request)
        result = inst.rename_finish()
        self.assertTrue('foobar2' in context)
        self.assertEqual(request.session['_f_'], ['Renamed 1 item'])

    def test_rename_finish_success_multiple(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = testing.DummyResource()
        context['foobar1'] = testing.DummyResource()
        context['foobar2'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('foobar',), {'foobar': 'foobar0',
                                               'foobar1': 'foobar11',
                                               'form.rename_finish': 'rename_finish'})
        inst = self._makeOne(context, request)
        result = inst.rename_finish()
        self.assertTrue('foobar2' in context)
        self.assertEqual(request.session['_f_'], ['Renamed 1 item'])

    def test_rename_finish_cancel(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = testing.DummyResource()
        context['foobar1'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('foobar',), {'foobar': 'foobar0',
                                               'form.rename_finish': 'cancel'})
        inst = self._makeOne(context, request)
        result = inst.rename_finish()
        self.assertTrue('foobar' in context)
        self.assertTrue('foobar1' in context)
        self.assertEqual(request.session['_f_'], ['No items renamed'])

    def test_rename_finish_already_exists(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = testing.DummyResource()
        context['foobar1'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('foobar',), {'foobar': 'foobar0',
                                               'foobar1': 'foobar0',
                                               'form.rename_finish': 'rename_finish'})
        inst = self._makeOne(context, request)
        result = inst.rename_finish()
        self.assertFalse('foobar0' in context)

    def test_copy_one(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = testing.DummyResource()
        context['foobar'].__objectid__ = 123
        context['foobar1'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('foobar',))
        inst = self._makeOne(context, request)
        result = inst.copy()
        self.assertEqual(request.session['_f_info'], ['Choose where to copy the items:'])
        self.assertEqual(request.session['tocopy'], [123])

    def test_copy_none(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost()
        inst = self._makeOne(context, request)
        result = inst.copy()
        self.assertEqual(request.session['_f_'], ['No items to copy'])
        self.assertFalse('tocopy' in request.session)

    def test_copy_multi(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = testing.DummyResource()
        context['foobar'].__objectid__ = 123
        context['foobar1'] = testing.DummyResource()
        context['foobar1'].__objectid__ = 456
        request = self._makeRequest()
        request.POST = DummyPost(('foobar','foobar1'))
        inst = self._makeOne(context, request)
        result = inst.copy()
        self.assertEqual(request.session['_f_info'], ['Choose where to copy the items:'])
        self.assertEqual(request.session['tocopy'], [123,456])

    def test_copy_finish_cancel(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = testing.DummyResource()
        context['foobar1'] = testing.DummyResource()
        request = self._makeRequest()
        request.session['tocopy'] = [123]
        request.POST = DummyPost(('foobar',), {'foobar': 'foobar0',
                                               'form.copy_finish': 'cancel'})
        inst = self._makeOne(context, request)
        result = inst.copy_finish()
        self.assertEqual(request.session['_f_'], ['No items copied'])

    def test_copy_finish_one(self):
        from .. import Folder
        context = Folder()
        context['target'] = DummyFolder()
        context['foobar'] = DummyExportableResource()
        context['foobar1'] = testing.DummyResource()
        request = self._makeRequest()
        request.session['tocopy'] = [123]
        request.POST = DummyPost(result2={'form.copy_finish': 'copy_finish'})
        context['target'].oid_store = {123: context['foobar']}
        inst = self._makeOne(context['target'], request)
        result = inst.copy_finish()
        self.assertEqual(request.session['_f_'], ['Copied 1 item'])
        self.assertEqual(context['target'].added[0][1].__name__, context['foobar'].__name__)

    def test_copy_finish_multi(self):
        from .. import Folder
        context = Folder()
        context['target'] = DummyFolder()
        context['foobar'] = DummyExportableResource()
        context['foobar1'] = DummyExportableResource()
        context['foobar2'] = testing.DummyResource()
        request = self._makeRequest()
        request.session['tocopy'] = [123,456]
        request.POST = DummyPost(result2={'form.copy_finish': 'copy_finish'})
        context['target'].oid_store = {123: context['foobar'], 456: context['foobar1']}
        inst = self._makeOne(context['target'], request)
        result = inst.copy_finish()
        self.assertEqual(request.session['_f_'], ['Copied 2 items'])
        self.assertEqual(context['target'].added[0][1].__name__, context['foobar'].__name__)
        self.assertEqual(context['target'].added[1][1].__name__, context['foobar1'].__name__)

    def test_copy_finish_already_exists(self):
        from .. import Folder
        context = Folder()
        context['target'] = DummyFolder()
        context['target']['foobar'] = testing.DummyResource()
        context['foobar'] = DummyExportableResource()
        context['foobar1'] = testing.DummyResource()
        request = self._makeRequest()
        request.session['tocopy'] = [123]
        request.POST = DummyPost(result2={'form.copy_finish': 'copy_finish'})
        context['target'].oid_store = {123: context['foobar']}
        inst = self._makeOne(context['target'], request)
        result = inst.copy_finish()
        self.assertEqual(request.session['_f_'], ['Copied 1 item'])
        self.assertEqual(context['target'].added[0][1].__name__, context['foobar'].__name__)

    def test_move_one(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = testing.DummyResource()
        context['foobar'].__objectid__ = 123
        context['foobar1'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('foobar',))
        inst = self._makeOne(context, request)
        result = inst.move()
        self.assertEqual(request.session['_f_info'], ['Choose where to move the items:'])
        self.assertEqual(request.session['tomove'], [123])

    def test_move_none(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost()
        inst = self._makeOne(context, request)
        result = inst.move()
        self.assertEqual(request.session['_f_'], ['No items to move'])
        self.assertFalse('tomove' in request.session)

    def test_move_multi(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = testing.DummyResource()
        context['foobar'].__objectid__ = 123
        context['foobar1'] = testing.DummyResource()
        context['foobar1'].__objectid__ = 456
        request = self._makeRequest()
        request.POST = DummyPost(('foobar','foobar1'))
        inst = self._makeOne(context, request)
        result = inst.move()
        self.assertEqual(request.session['_f_info'], ['Choose where to move the items:'])
        self.assertEqual(request.session['tomove'], [123,456])

    def test_move_finish_cancel(self):
        from .. import Folder
        context = Folder()
        context['foobar'] = testing.DummyResource()
        context['foobar1'] = testing.DummyResource()
        request = self._makeRequest()
        request.session['tomove'] = [123]
        request.POST = DummyPost(('foobar',), {'foobar': 'foobar0',
                                               'form.move_finish': 'cancel'})
        inst = self._makeOne(context, request)
        result = inst.move_finish()
        self.assertEqual(request.session['_f_'], ['No items moved'])

    def test_move_finish_one(self):
        from .. import Folder
        context = Folder()
        context['target'] = DummyFolder()
        context['foobar'] = DummyExportableResource()
        context['foobar1'] = testing.DummyResource()
        foobar_name = context['foobar'].__name__
        request = self._makeRequest()
        request.session['tomove'] = [123]
        request.POST = DummyPost(result2={'form.move_finish': 'move_finish'})
        context['target'].oid_store = {123: context['foobar']}
        inst = self._makeOne(context['target'], request)
        result = inst.move_finish()
        self.assertEqual(request.session['_f_'], ['Moved 1 item'])
        self.assertEqual(context['target'].added[0][1].__name__, foobar_name)
        self.assertFalse('foobar' in context)

    def test_move_finish_multi(self):
        from .. import Folder
        context = Folder()
        context['target'] = DummyFolder()
        context['foobar'] = DummyExportableResource()
        context['foobar1'] = DummyExportableResource()
        context['foobar2'] = testing.DummyResource()
        foobar_name = context['foobar'].__name__
        foobar1_name = context['foobar1'].__name__
        request = self._makeRequest()
        request.session['tomove'] = [123,456]
        request.POST = DummyPost(result2={'form.move_finish': 'move_finish'})
        context['target'].oid_store = {123: context['foobar'], 456: context['foobar1']}
        inst = self._makeOne(context['target'], request)
        result = inst.move_finish()
        self.assertEqual(request.session['_f_'], ['Moved 2 items'])
        self.assertEqual(context['target'].added[0][1].__name__, foobar_name)
        self.assertEqual(context['target'].added[1][1].__name__, foobar1_name)
        self.assertFalse('foobar' in context)
        self.assertFalse('foobar1' in context)

    def test_move_finish_already_exists(self):
        from .. import Folder
        context = Folder()
        context['target'] = DummyFolder()
        context['target']['foobar'] = testing.DummyResource()
        context['foobar'] = DummyExportableResource()
        context['foobar1'] = testing.DummyResource()
        request = self._makeRequest()
        request.session['tomove'] = [123]
        request.POST = DummyPost(result2={'form.move_finish': 'move_finish'})
        context['target'].oid_store = {123: context['foobar']}
        inst = self._makeOne(context['target'], request)
        result = inst.move_finish()
        self.assertEqual(request.session['_f_'], ['Copied 1 item'])
        self.assertEqual(context['target'].added[0][1].__name__, context['foobar'].__name__)

class DummyPost(dict):
    def __init__(self, result=(), result2=None):
        self.result = result
        self.result2 = result2 or {}

    def getall(self, name):
        return self.result

    def get(self, name):
        return self.result2[name]

class DummyFolder(object):
    oid_store = {}
    added = []

    def __init__(self, exc=None):
        self.exc = exc

    def check_name(self, name):
        if self.exc:
            raise self.exc
        return name

    def find_service(self, name):
        om = DummyObjectMap()
        om.oid_store = self.oid_store
        return om

    def add(self, name, other, **kw):
        self.added.append((name, other))

class DummyObjectMap(object):

    def object_for(self, oid):
        return self.oid_store[oid]

class DummyContent(object):
    def __init__(self, resource=None):
        self.resource = resource

    def create(self, iface, *arg, **kw):
        return self.resource

    def metadata(self, v, default=None):
        return default

class DummyExportImport(object):
    def __init__(self, obj):
        self.obj = obj

    def exportFile(self, oid, f):
        pass

    def importFile(self, f):
        import copy
        new_obj = copy.deepcopy(self.obj)
        new_obj.__objectid__ = 0
        return new_obj

class DummyExportableResource(testing.DummyResource):
    _p_oid = 0

    @property
    def _p_jar(self):
        return DummyExportImport(self)
