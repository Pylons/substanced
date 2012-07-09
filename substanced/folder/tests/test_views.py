import unittest
import mock

from pyramid import testing
from pyramid.httpexceptions import HTTPFound
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

    @mock.patch('substanced.folder.views.rename_duplicated_resource')
    def test_duplicate_multiple(self, mock_rename_duplicated_resource):
        context = mock.Mock()
        request = mock.Mock()
        request.POST.getall.return_value = ('a', 'b')
        mock_rename_duplicated_resource.side_effect = ['a-1', 'b-1']

        inst = self._makeOne(context, request)
        inst.duplicate()

        mock_rename_duplicated_resource.assert_any_call(context, 'a')
        mock_rename_duplicated_resource.assert_any_call(context, 'b')
        request.flash_with_undo.assert_called_once_with('Duplicated 2 items')
        request.mgmt_path.called_once_with(context, '@@contents')
        context.copy.assert_any_call('a', context, 'a-1')
        context.copy.assert_any_call('b', context, 'b-1')

    def test_duplicate_none(self):
        context = mock.Mock()
        request = mock.Mock()
        request.POST.getall.return_value = tuple()
        inst = self._makeOne(context, request)
        inst.duplicate()

        self.assertEqual(context.mock_calls, [])
        request.session.flash.assert_called_once_with('No items duplicated')
        request.mgmt_path.called_once_with(context, '@@contents')

    @mock.patch('substanced.folder.views.rename_duplicated_resource')
    def test_duplicate_one(self, mock_rename_duplicated_resource):
        mock_rename_duplicated_resource.side_effect = ['a-1']
        context = mock.Mock()
        request = mock.Mock()
        request.POST.getall.return_value = ('a',)
        inst = self._makeOne(context, request)
        inst.duplicate()

        mock_rename_duplicated_resource.assert_any_call(context, 'a')
        context.copy.assert_any_call('a', context, 'a-1')
        request.flash_with_undo.assert_called_once_with('Duplicated 1 item')
        request.mgmt_path.called_once_with(context, '@@contents')

    def test_rename_one(self):
        context = testing.DummyResource()
        context['foobar'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('foobar',))
        inst = self._makeOne(context, request)
        result = inst.rename()
        self.assertEqual(result, {'torename': [context['foobar']]})

    def test_rename_missing_child(self):
        context = testing.DummyResource()
        context['foobar'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(('foobar', 'foobar1'))
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
        self.assertEqual(result, {'torename': [context['foobar'],
                                               context['foobar3']]})

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

    def test_rename_finish(self):
        context = mock.Mock()
        request = mock.Mock()
        request.POST.getall.return_value = ('foobar',)
        request.POST.get.side_effect = lambda x: {
            'foobar': 'foobar2',
            'form.rename_finish': 'rename_finish'}[x]

        inst = self._makeOne(context, request)
        inst.rename_finish()
        request.flash_with_undo.assert_called_once_with('Renamed 1 item')
        context.rename.assert_called_once_with('foobar', 'foobar2')

    def test_rename_finish_multiple(self):
        context = mock.Mock()
        request = mock.Mock()
        request.POST.getall.return_value = ('foobar', 'foobar1')
        request.POST.get.side_effect = lambda x: {
            'foobar': 'foobar0',
            'foobar1': 'foobar11',
            'form.rename_finish': 'rename_finish'}[x]

        inst = self._makeOne(context, request)
        inst.rename_finish()

        request.flash_with_undo.assert_called_once_with('Renamed 2 items')
        context.rename.assert_any_call('foobar', 'foobar0')
        context.rename.assert_any_call('foobar1', 'foobar11')

    def test_rename_finish_cancel(self):
        context = mock.Mock()
        request = mock.Mock()
        request.POST.getall.return_value = ('foobar',)
        request.POST.get.side_effect = lambda x: {
            'foobar': 'foobar0',
            'form.rename_finish': 'cancel'}[x]
        inst = self._makeOne(context, request)
        inst.rename_finish()

        request.session.flash.assert_called_once_with('No items renamed')
        self.assertFalse(context.rename.called)

    def test_rename_finish_already_exists(self):
        from ...exceptions import FolderKeyError
        context = mock.MagicMock()
        context.rename.side_effect = FolderKeyError(u'foobar')
        request = mock.Mock()
        request.POST.getall.return_value = ('foobar',)
        request.POST.get.side_effect = lambda x: {
            'foobar': 'foobar0',
            'foobar1': 'foobar0',
            'form.rename_finish': 'rename_finish'}[x]
        inst = self._makeOne(context, request)

        self.assertRaises(HTTPFound, inst.rename_finish)
        context.rename.assert_any_call('foobar', 'foobar0')
        request.session.flash.assert_called_once_with(u'foobar', 'error')

    @mock.patch('substanced.folder.views.oid_of')
    def test_copy_one(self, mock_oid_of):
        context = mock.Mock()
        context.get.side_effect = lambda x: {
            'foobar': 'foobar',
            'foobar1': 'foobar1'}[x]
        request = mock.MagicMock()
        request.POST.getall.return_value = ('foobar',)

        inst = self._makeOne(context, request)
        inst.copy()

        request.session.flash.assert_called_once_with(
            'Choose where to copy the items:', 'info')
        self.assertEqual(mock_oid_of.mock_calls, [mock.call('foobar')])
        self.assertTrue(request.session.__setitem__.called)

    @mock.patch('substanced.folder.views.oid_of')
    def test_copy_multi(self, mock_oid_of):
        context = mock.Mock()
        context.get.side_effect = lambda x: {'foobar': 'foobar',
                                             'foobar1': 'foobar1',
                                             'foobar2': 'foobar2'}[x]
        request = mock.MagicMock()
        request.POST.getall.return_value = ('foobar', 'foobar1')

        inst = self._makeOne(context, request)
        inst.copy()

        request.session.flash.assert_called_once_with(
            'Choose where to copy the items:', 'info')
        self.assertEqual(mock_oid_of.mock_calls,
                         [mock.call('foobar'), mock.call('foobar1')])
        self.assertTrue(request.session.__setitem__.called)

    @mock.patch('substanced.folder.views.oid_of')
    def test_copy_missing_child(self, mock_oid_of):
        context = mock.Mock()
        context.get.side_effect = lambda x: {
            'foobar': 'foobar',
            'foobar2': 'foobar2'}.get(x, None)
        request = mock.MagicMock()
        request.POST.getall.return_value = ('foobar', 'foobar1')

        inst = self._makeOne(context, request)
        inst.copy()
        request.session.flash.assert_called_once_with(
            'Choose where to copy the items:', 'info')
        self.assertEqual(mock_oid_of.mock_calls, [mock.call('foobar')])
        self.assertTrue(request.session.__setitem__.called)

    @mock.patch('substanced.folder.views.oid_of')
    def test_copy_none(self, mock_oid_of):
        context = mock.Mock()
        context.__contains__ = mock.Mock(return_value=True)
        request = mock.MagicMock()
        request.POST.getall.return_value = tuple()

        inst = self._makeOne(context, request)
        inst.copy()

        request.session.flash.assert_called_once_with('No items to copy')
        self.assertFalse(mock_oid_of.called)

    def test_copy_finish_cancel(self):
        context = mock.Mock()
        request = mock.MagicMock()
        request.POST.getall.return_value = ('foobar',)
        request.POST.get.side_effect = lambda x: {
            'foobar': 'foobar0',
            'form.copy_finish': 'cancel'}[x]
        inst = self._makeOne(context, request)
        inst.copy_finish()

        request.session.flash.assert_called_once_with('No items copied')
        self.assertEqual(request.session.__delitem__.call_args,
                         mock.call('tocopy'))

    def test_copy_finish_one(self):
        context = mock.MagicMock()
        mock_folder = context['target'].find_service().object_for()
        mock_folder.__parent__ = mock.MagicMock()
        mock_folder.__name__ = mock.sentinel.name
        request = mock.MagicMock()
        request.session.__getitem__.return_value = [123]
        request.POST.get.side_effect = lambda x: {
            'form.copy_finish': 'copy_finish'}[x]

        inst = self._makeOne(context['target'], request)
        inst.copy_finish()

        self.assertEqual(mock_folder.__parent__.copy.call_args,
                         mock.call(mock.sentinel.name, context['target']))
        request.flash_with_undo.assert_called_once_with('Copied 1 item')
        self.assertEqual(request.session.__delitem__.call_args, mock.call('tocopy'))

    def test_copy_finish_multi(self):
        context = mock.MagicMock()
        mock_folder = context['target'].find_service().object_for()
        mock_folder.__parent__ = mock.MagicMock()
        mock_folder.__name__ = mock.sentinel.name
        request = mock.MagicMock()
        request.session.__getitem__.return_value = [123, 456]
        request.POST.get.side_effect = lambda x: {
            'form.copy_finish': 'copy_finish'}[x]

        inst = self._makeOne(context['target'], request)
        inst.copy_finish()

        self.assertTrue(mock.call(123) in
                        context['target'].find_service().object_for.mock_calls)
        self.assertTrue(mock.call(456) in
                        context['target'].find_service().object_for.mock_calls)
        self.assertEqual(mock_folder.__parent__.copy.call_args,
                         mock.call(mock.sentinel.name, context['target']))
        request.flash_with_undo.assert_called_once_with('Copied 2 items')
        self.assertEqual(request.session.__delitem__.call_args,
                         mock.call('tocopy'))

    def test_copy_finish_already_exists(self):
        from ...exceptions import FolderKeyError
        context = mock.MagicMock()
        mock_folder = context['target'].find_service().object_for()
        mock_folder.__parent__ = mock.MagicMock()
        mock_folder.__parent__.copy.side_effect = FolderKeyError(u'foobar')
        mock_folder.__name__ = mock.sentinel.name
        request = mock.MagicMock()
        request.session.__getitem__.return_value = [123]
        request.POST.get.side_effect = lambda x: {
            'form.copy_finish': 'copy_finish'}[x]

        inst = self._makeOne(context['target'], request)
        self.assertRaises(HTTPFound, inst.copy_finish)
        request.session.flash.assert_called_once_with(u'foobar', 'error')

    @mock.patch('substanced.folder.views.oid_of')
    def test_move_one(self, mock_oid_of):
        context = mock.Mock()
        context.get.side_effect = lambda x: {
            'foobar': 'foobar',
            'foobar1': 'foobar1'}[x]
        request = mock.MagicMock()
        request.POST.getall.return_value = ('foobar',)

        inst = self._makeOne(context, request)
        inst.move()

        request.session.flash.assert_called_once_with(
            'Choose where to move the items:', 'info')
        self.assertEqual(mock_oid_of.mock_calls, [mock.call('foobar')])
        self.assertTrue(request.session.__setitem__.call_args,
                        [mock.call('tomove')])

    @mock.patch('substanced.folder.views.oid_of')
    def test_move_multi(self, mock_oid_of):
        context = mock.Mock()
        context.get.side_effect = lambda x: {'foobar': 'foobar',
                                             'foobar1': 'foobar1'}[x]
        request = mock.MagicMock()
        request.POST.getall.return_value = ('foobar', 'foobar1')

        inst = self._makeOne(context, request)
        inst.move()

        request.session.flash.assert_called_once_with(
            'Choose where to move the items:', 'info')
        self.assertEqual(mock_oid_of.mock_calls,
                         [mock.call('foobar'), mock.call('foobar1')])
        self.assertTrue(request.session.__setitem__.call_args,
                        [mock.call('tomove')])

    @mock.patch('substanced.folder.views.oid_of')
    def test_move_missing_child(self, mock_oid_of):
        context = mock.Mock()
        context.get.side_effect = lambda x: {'foobar': 'foobar',
                                             'foobar1': 'foobar1'}.get(x, None)
        request = mock.MagicMock()
        request.POST.getall.return_value = ('foobar', 'foobar2')

        inst = self._makeOne(context, request)
        inst.move()

        request.session.flash.assert_called_once_with(
            'Choose where to move the items:', 'info')
        self.assertEqual(mock_oid_of.mock_calls, [mock.call('foobar')])
        self.assertTrue(request.session.__setitem__.call_args,
                        [mock.call('tomove')])

    @mock.patch('substanced.folder.views.oid_of')
    def test_move_none(self, mock_oid_of):
        context = mock.Mock()
        context.get.side_effect = lambda x: {'foobar': 'foobar',
                                             'foobar1': 'foobar1'}.get(x, None)
        request = mock.MagicMock()
        request.POST.getall.return_value = tuple()

        inst = self._makeOne(context, request)
        inst.move()

        request.session.flash.assert_called_once_with('No items to move')
        self.assertFalse(mock_oid_of.called)
        self.assertFalse(request.session.__setitem__.called)

    def test_move_finish_cancel(self):
        context = mock.Mock()
        request = mock.MagicMock()
        request.POST.getall.return_value = ('foobar',)
        request.POST.get.side_effect = lambda x: {
            'foobar': 'foobar0',
            'form.move_finish': 'cancel'}[x]
        inst = self._makeOne(context, request)
        inst.move_finish()

        request.session.flash.assert_called_once_with('No items moved')
        self.assertEqual(request.session.__delitem__.call_args,
                         mock.call('tomove'))

    def test_move_finish_one(self):
        context = mock.MagicMock()
        mock_folder = context['target'].find_service().object_for()
        mock_folder.__parent__ = mock.MagicMock()
        mock_folder.__name__ = mock.sentinel.name
        request = mock.MagicMock()
        request.session.__getitem__.return_value = [123]
        request.POST.get.side_effect = lambda x: {
            'form.move_finish': 'move_finish'}[x]

        inst = self._makeOne(context['target'], request)
        inst.move_finish()

        self.assertEqual(mock_folder.__parent__.move.call_args,
                         mock.call(mock.sentinel.name, context['target']))
        request.flash_with_undo.assert_called_once_with('Moved 1 item')
        self.assertEqual(request.session.__delitem__.call_args,
                         mock.call('tomove'))

    def test_move_finish_multi(self):
        context = mock.MagicMock()
        mock_folder = context['target'].find_service().object_for()
        mock_folder.__parent__ = mock.MagicMock()
        mock_folder.__name__ = mock.sentinel.name
        request = mock.MagicMock()
        request.session.__getitem__.return_value = [123, 456]
        request.POST.get.side_effect = lambda x: {
            'form.move_finish': 'move_finish'}[x]

        inst = self._makeOne(context['target'], request)
        inst.move_finish()

        self.assertTrue(mock.call(123) in
                        context['target'].find_service().object_for.mock_calls)
        self.assertTrue(mock.call(456) in
                        context['target'].find_service().object_for.mock_calls)
        self.assertEqual(mock_folder.__parent__.move.call_args,
                         mock.call(mock.sentinel.name, context['target']))
        self.assertEqual(request.session.__delitem__.call_args,
                         mock.call('tomove'))
        request.flash_with_undo.assert_called_once_with('Moved 2 items')

    def test_move_finish_already_exists(self):
        from ...exceptions import FolderKeyError
        context = mock.MagicMock()
        mock_folder = context['target'].find_service().object_for()
        mock_folder.__parent__ = mock.MagicMock()
        mock_folder.__parent__.move.side_effect = FolderKeyError(u'foobar')
        mock_folder.__name__ = mock.sentinel.name
        request = mock.MagicMock()
        request.session.__getitem__.return_value = [123]
        request.POST.get.side_effect = lambda x: {
            'form.move_finish': 'move_finish'}[x]

        inst = self._makeOne(context['target'], request)
        self.assertRaises(HTTPFound, inst.move_finish)
        request.session.flash.assert_called_once_with(u'foobar', 'error')


class DummyPost(dict):
    def __init__(self, result=(), result2=None):
        self.result = result
        self.result2 = result2 or {}

    def getall(self, name):
        return self.result

class DummyFolder(object):
    oid_store = {}

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
