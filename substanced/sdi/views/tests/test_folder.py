import colander
import unittest

from pyramid import testing

from pyramid.httpexceptions import HTTPFound

import mock

class Test_name_validator(unittest.TestCase):
    def _callFUT(self, node, kw):
        from ..folder import name_validator
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
    def _callFUT(self, context, name):
        from ..folder import rename_duplicated_resource
        return rename_duplicated_resource(context, name)
        
    def test_rename_first(self):
        context = testing.DummyResource()
        new_name = self._callFUT(context, 'foobar')
        self.assertEqual(new_name, 'foobar')

    def test_rename_second(self):
        context = testing.DummyResource()
        context['foobar'] = testing.DummyResource()
        new_name = self._callFUT(context, 'foobar')
        self.assertEqual(new_name, 'foobar-1')

    def test_rename_twentyfirst(self):
        context = testing.DummyResource()
        context['foobar-21'] = testing.DummyResource()
        new_name = self._callFUT(context, 'foobar-21')
        self.assertEqual(new_name, 'foobar-22')

    def test_rename_multiple_dashes(self):
        context = testing.DummyResource()
        context['foo-bar'] = testing.DummyResource()
        new_name = self._callFUT(context, 'foo-bar')
        self.assertEqual(new_name, 'foo-bar-1')

    def test_rename_take_fisrt_available(self):
        context = testing.DummyResource()
        context['foobar'] = testing.DummyResource()
        context['foobar-1'] = testing.DummyResource()
        context['foobar-2'] = testing.DummyResource()
        context['foobar-4'] = testing.DummyResource()
        new_name = self._callFUT(context, 'foobar')
        self.assertEqual(new_name, 'foobar-3')

class TestAddFolderView(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..folder import AddFolderView
        return AddFolderView(context, request)

    def _makeRequest(self, **kw):
        request = testing.DummyRequest()
        request.registry.content = DummyContent(**kw)
        request.sdiapi = DummySDIAPI()
        return request

    def test_add_success(self):
        resource = testing.DummyResource()
        request = self._makeRequest(Folder=resource)
        context = testing.DummyResource()
        inst = self._makeOne(context, request)
        resp = inst.add_success({'name': 'name'})
        self.assertEqual(context['name'], resource)
        self.assertEqual(resp.location, '/mgmt_path')

class TestFolderContentsViews(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..folder import FolderContentsViews
        return FolderContentsViews(context, request)

    def _makeRequest(self, **kw):
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        request.sdiapi.flash_with_undo = request.session.flash
        request.registry.content = DummyContent(**kw)
        return request

    def test_show_no_columns(self):
        context = testing.DummyResource()
        request = self._makeRequest(columns=None)
        inst = self._makeOne(context, request)
        inst.sdi_folder_contents = mock.Mock(return_value=dummy_folder_contents_0)
        inst._column_headers_sg = mock.Mock(return_value=dummy_column_headers_sg_0)
        inst.sdi_add_views = mock.Mock(return_value=('b',))
        result = inst.show()
        self.assert_('slickgrid_wrapper_options' in result)
        slickgrid_wrapper_options = result['slickgrid_wrapper_options']
        self.assert_('slickgridOptions' in slickgrid_wrapper_options)
        self.assertEqual(slickgrid_wrapper_options['configName'], 'sdi-content-grid')
        self.assertEqual(slickgrid_wrapper_options['sortCol'], None)   # None because it cannot be sorted.  
        self.assertEqual(slickgrid_wrapper_options['sortDir'], True)
        self.assertEqual(slickgrid_wrapper_options['url'], '')
        self.assert_('items' in slickgrid_wrapper_options)
        self.assertEqual(slickgrid_wrapper_options['items']['from'], 0)
        self.assertEqual(slickgrid_wrapper_options['items']['to'], 40)
        self.assertEqual(slickgrid_wrapper_options['items']['total'], 1)
        self.assert_('records' in slickgrid_wrapper_options['items'])
        records = slickgrid_wrapper_options['items']['records']
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], {
            'name': 'the_name',
            'deletable': True,
            'name_url': 'http://foo.bar',
            'id': 'the_name',
            'name_icon': 'the_icon',
            })
        addables = result['addables']
        self.assertEqual(addables, ('b',))
        buttons = result['buttons']
        self.assertEqual(len(buttons), 2)

    def test_show_with_columns(self):
        def sd_columns(folder, subobject, request, default_columns):
            self.assertEqual(len(default_columns), 1)
            return [{'name': 'Col 1', 'field': 'col1', 'value': 'col1'},
                    {'name': 'Col 2', 'field': 'col2', 'value': 'col2'}]
        context = testing.DummyResource()
        request = self._makeRequest(columns=sd_columns)
        inst = self._makeOne(context, request)
        inst.sdi_folder_contents = mock.Mock(return_value=dummy_folder_contents_2)
        inst._column_headers_sg = mock.Mock(return_value=dummy_column_headers_sg_2)
        inst.sdi_add_views = mock.Mock(return_value=('b',))
        result = inst.show()
        self.assert_('slickgrid_wrapper_options' in result)
        slickgrid_wrapper_options = result['slickgrid_wrapper_options']
        self.assert_('slickgridOptions' in slickgrid_wrapper_options)
        self.assertEqual(slickgrid_wrapper_options['configName'], 'sdi-content-grid')
        self.assertEqual(slickgrid_wrapper_options['sortCol'], 'col1')  
        self.assertEqual(slickgrid_wrapper_options['sortDir'], True)
        self.assertEqual(slickgrid_wrapper_options['url'], '')
        self.assert_('items' in slickgrid_wrapper_options)
        self.assertEqual(slickgrid_wrapper_options['items']['from'], 0)
        self.assertEqual(slickgrid_wrapper_options['items']['to'], 40)
        self.assertEqual(slickgrid_wrapper_options['items']['total'], 1)
        self.assert_('records' in slickgrid_wrapper_options['items'])
        records = slickgrid_wrapper_options['items']['records']
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], {
            'name': 'the_name',
            'col1': 'value4col1',
            'col2': 'value4col2',
            'deletable': True,
            'name_url': 'http://foo.bar',
            'id': 'the_name',
            'name_icon': 'the_icon',
            })

        addables = result['addables']
        self.assertEqual(addables, ('b',))
        buttons = result['buttons']
        self.assertEqual(len(buttons), 2)

    def test_show_non_sortable_columns(self):
        def sd_columns(folder, subobject, request, default_columns):
            self.assertEqual(len(default_columns), 1)
            return [{'name': 'Col 1', 'field': 'col1', 'value': 'col1', 'sortable': False},
                    {'name': 'Col 2', 'field': 'col2', 'value': 'col2'}]
        context = testing.DummyResource()
        request = self._makeRequest(columns=sd_columns)
        inst = self._makeOne(context, request)
        inst.sdi_folder_contents = mock.Mock(return_value=dummy_folder_contents_2)
        inst._column_headers_sg = mock.Mock(return_value=dummy_column_headers_sg_2)
        inst.sdi_add_views = mock.Mock(return_value=('b',))
        result = inst.show()
        self.assert_('slickgrid_wrapper_options' in result)
        slickgrid_wrapper_options = result['slickgrid_wrapper_options']
        self.assert_('slickgridOptions' in slickgrid_wrapper_options)
        self.assertEqual(slickgrid_wrapper_options['configName'], 'sdi-content-grid')

        
        # XXX This should actually be 'col2'! TODO make the grid choose the first column
        # that is actually sortable.
        #####self.assertEqual(slickgrid_wrapper_options['sortCol'], 'col2')  

        
        self.assertEqual(slickgrid_wrapper_options['sortDir'], True)
        self.assertEqual(slickgrid_wrapper_options['url'], '')
        self.assert_('items' in slickgrid_wrapper_options)
        self.assertEqual(slickgrid_wrapper_options['items']['from'], 0)
        self.assertEqual(slickgrid_wrapper_options['items']['to'], 40)
        self.assertEqual(slickgrid_wrapper_options['items']['total'], 1)
        self.assert_('records' in slickgrid_wrapper_options['items'])
        records = slickgrid_wrapper_options['items']['records']
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], {
            'name': 'the_name',
            'col1': 'value4col1',
            'col2': 'value4col2',
            'deletable': True,
            'name_url': 'http://foo.bar',
            'id': 'the_name',
            'name_icon': 'the_icon',
            })
        addables = result['addables']
        self.assertEqual(addables, ('b',))
        buttons = result['buttons']
        self.assertEqual(len(buttons), 2)
        # We don't actually see the sortability in the records, because
        # this information is in the columns metadata. So, we test this
        # in test_metadata_for_non_sortable_columns.


    def test_metadata_for_non_sortable_columns(self):
        def sd_columns(folder, subobject, request, default_columns):
            self.assertEqual(len(default_columns), 1)
            return [{'name': 'Col 1', 'field': 'col1', 'value': 'col1', 'sortable': False},
                    {'name': 'Col 2', 'field': 'col2', 'value': 'col2'}]
        context = testing.DummyResource()
        request = self._makeRequest(columns=sd_columns)
        inst = self._makeOne(context, request)
        result = inst._column_headers_sg(context, request)
        self.assertEqual(len(result), 2)

        col = result[0]
        self.assertEqual(col['field'], 'col1')
        self.assertEqual(col['id'], 'col1')
        self.assertEqual(col['name'], 'Col 1')
        self.assertEqual(col['width'], 120)
        self.assertEqual(col['formatterName'], '')
        self.assertEqual(col['cssClass'], 'cell-col1')

        self.assertEqual(col['sortable'], False)

        col = result[1]
        self.assertEqual(col['field'], 'col2')
        self.assertEqual(col['id'], 'col2')
        self.assertEqual(col['name'], 'Col 2')
        self.assertEqual(col['width'], 120)
        self.assertEqual(col['formatterName'], '')
        self.assertEqual(col['cssClass'], 'cell-col2')

        self.assertEqual(col['sortable'], True)


    def test_show_non_filterable_columns(self):
        def sd_columns(folder, subobject, request, default_columns):
            self.assertEqual(len(default_columns), 1)
            return [{'name': 'Col 1', 'field': 'col1', 'value': 'col1'},
                    {'name': 'Col 2', 'field': 'col2', 'value': 'col2', 'filterable': False}]
        context = testing.DummyResource()
        request = self._makeRequest(columns=sd_columns)
        inst = self._makeOne(context, request)
        inst.sdi_folder_contents = mock.Mock(return_value=dummy_folder_contents_2)
        inst._column_headers_sg = mock.Mock(return_value=dummy_column_headers_sg_2)
        inst.sdi_add_views = mock.Mock(return_value=('b',))
        result = inst.show()
        self.assert_('slickgrid_wrapper_options' in result)
        slickgrid_wrapper_options = result['slickgrid_wrapper_options']
        self.assert_('slickgridOptions' in slickgrid_wrapper_options)
        self.assertEqual(slickgrid_wrapper_options['configName'], 'sdi-content-grid')
        self.assertEqual(slickgrid_wrapper_options['sortDir'], True)
        self.assertEqual(slickgrid_wrapper_options['url'], '')
        self.assert_('items' in slickgrid_wrapper_options)
        self.assertEqual(slickgrid_wrapper_options['items']['from'], 0)
        self.assertEqual(slickgrid_wrapper_options['items']['to'], 40)
        self.assertEqual(slickgrid_wrapper_options['items']['total'], 1)
        self.assert_('records' in slickgrid_wrapper_options['items'])
        records = slickgrid_wrapper_options['items']['records']
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], {
            'name': 'the_name',
            'col1': 'value4col1',
            'col2': 'value4col2',
            'deletable': True,
            'name_url': 'http://foo.bar',
            'id': 'the_name',
            'name_icon': 'the_icon',
            })
        addables = result['addables']
        self.assertEqual(addables, ('b',))
        buttons = result['buttons']
        self.assertEqual(len(buttons), 2)

        # We don't actually see the sortability in the records, because
        # this information is in the columns metadata. So, we test this
        # in another test case, but right now this data is not
        # actually handled by the grid yet.


    def test_delete_none_deleted(self):
        context = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost()
        inst = self._makeOne(context, request)
        result = inst.delete()
        self.assertEqual(request.session['_f_'], ['No items deleted'])
        self.assertEqual(result.location, '/mgmt_path')

    def test_delete_one_deleted(self):
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(None, 'a')
        inst = self._makeOne(context, request)
        result = inst.delete()
        self.assertEqual(request.session['_f_'], ['Deleted 1 item'])
        self.assertEqual(result.location, '/mgmt_path')
        self.assertFalse('a' in context)

    def test_delete_multiple_deleted(self):
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        context['b'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(None, 'a,b')
        inst = self._makeOne(context, request)
        result = inst.delete()
        self.assertEqual(request.session['_f_'], ['Deleted 2 items'])
        self.assertEqual(result.location, '/mgmt_path')
        self.assertFalse('a' in context)
        self.assertFalse('b' in context)

    def test_delete_undeletable_item(self):
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(None, 'a,b')
        inst = self._makeOne(context, request)
        result = inst.delete()
        self.assertEqual(request.session['_f_'], ['Deleted 1 item'])
        self.assertEqual(result.location, '/mgmt_path')
        self.assertFalse('a' in context)

    @mock.patch('substanced.sdi.views.folder.rename_duplicated_resource')
    def test_duplicate_multiple(self, mock_rename_duplicated_resource):
        context = mock.Mock()
        request = mock.Mock()
        request.POST.get.return_value = 'a,b'
        mock_rename_duplicated_resource.side_effect = ['a-1', 'b-1']

        inst = self._makeOne(context, request)
        inst.duplicate()

        mock_rename_duplicated_resource.assert_any_call(context, 'a')
        mock_rename_duplicated_resource.assert_any_call(context, 'b')
        request.sdiapi.flash_with_undo.assert_called_once_with(
            'Duplicated 2 items')
        request.sdiapi.mgmt_path.called_once_with(context, '@@contents')
        context.copy.assert_any_call('a', context, 'a-1')
        context.copy.assert_any_call('b', context, 'b-1')

    def test_duplicate_none(self):
        context = mock.Mock()
        request = mock.Mock()
        request.POST.get.return_value = ''
        inst = self._makeOne(context, request)
        inst.duplicate()

        self.assertEqual(context.mock_calls, [])
        request.session.flash.assert_called_once_with('No items duplicated')
        request.sdiapi.mgmt_path.called_once_with(context, '@@contents')

    @mock.patch('substanced.sdi.views.folder.rename_duplicated_resource')
    def test_duplicate_one(self, mock_rename_duplicated_resource):
        mock_rename_duplicated_resource.side_effect = ['a-1']
        context = mock.Mock()
        request = mock.Mock()
        request.POST.get.return_value = 'a'
        inst = self._makeOne(context, request)
        inst.duplicate()

        mock_rename_duplicated_resource.assert_any_call(context, 'a')
        context.copy.assert_any_call('a', context, 'a-1')
        request.sdiapi.flash_with_undo.assert_called_once_with(
            'Duplicated 1 item')
        request.sdiapi.mgmt_path.called_once_with(context, '@@contents')

    def test_rename_one(self):
        context = testing.DummyResource()
        context['foobar'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(None, 'foobar')
        inst = self._makeOne(context, request)
        result = inst.rename()
        self.assertEqual(result, {'torename': [context['foobar']]})

    def test_rename_missing_child(self):
        context = testing.DummyResource()
        context['foobar'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(None, 'foobar,foobar1')
        inst = self._makeOne(context, request)
        result = inst.rename()
        self.assertEqual(result, {'torename': [context['foobar']]})

    def test_rename_multiple(self):
        context = testing.DummyResource()
        context['foobar'] = testing.DummyResource()
        context['foobar2'] = testing.DummyResource()
        context['foobar3'] = testing.DummyResource()
        request = self._makeRequest()
        request.POST = DummyPost(None, 'foobar,foobar3')
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
        request.POST = DummyPost(None, '')
        inst = self._makeOne(context, request)
        result = inst.rename()
        self.assertEqual(request.session['_f_'], ['No items renamed'])
        self.assertEqual(result.location, '/mgmt_path')

    def test_rename_finish(self):
        context = mock.Mock()
        request = mock.Mock()
        request.POST.getall.return_value = ('foobar',)
        request.POST.get.side_effect = lambda x: {
            'foobar': 'foobar2',
            'form.rename_finish': 'rename_finish'}[x]

        inst = self._makeOne(context, request)
        inst.rename_finish()
        request.sdiapi.flash_with_undo.assert_called_once_with(
            'Renamed 1 item')
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

        request.sdiapi.flash_with_undo.assert_called_once_with(
            'Renamed 2 items')
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
        from ....folder import FolderKeyError
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

    @mock.patch('substanced.sdi.views.folder.get_oid')
    def test_copy_one(self, mock_get_oid):
        context = mock.Mock()
        context.get.side_effect = lambda x: {
            'foobar': 'foobar',
            'foobar1': 'foobar1'}[x]
        request = mock.MagicMock()
        request.POST.get.return_value = 'foobar'

        inst = self._makeOne(context, request)
        inst.copy()

        request.session.flash.assert_called_once_with(
            'Choose where to copy the items:', 'info')
        self.assertEqual(mock_get_oid.mock_calls, [mock.call('foobar')])
        self.assertTrue(request.session.__setitem__.called)

    @mock.patch('substanced.sdi.views.folder.get_oid')
    def test_copy_multi(self, mock_get_oid):
        context = mock.Mock()
        context.get.side_effect = lambda x: {'foobar': 'foobar',
                                             'foobar1': 'foobar1',
                                             'foobar2': 'foobar2'}[x]
        request = mock.MagicMock()
        request.POST.get.return_value = 'foobar,foobar1'

        inst = self._makeOne(context, request)
        inst.copy()

        request.session.flash.assert_called_once_with(
            'Choose where to copy the items:', 'info')
        self.assertEqual(mock_get_oid.mock_calls,
                         [mock.call('foobar'), mock.call('foobar1')])
        self.assertTrue(request.session.__setitem__.called)

    @mock.patch('substanced.sdi.views.folder.get_oid')
    def test_copy_missing_child(self, mock_get_oid):
        context = mock.Mock()
        context.get.side_effect = lambda x: {
            'foobar': 'foobar',
            'foobar2': 'foobar2'}.get(x, None)
        request = mock.MagicMock()
        request.POST.get.return_value = 'foobar,foobar1'

        inst = self._makeOne(context, request)
        inst.copy()
        request.session.flash.assert_called_once_with(
            'Choose where to copy the items:', 'info')
        self.assertEqual(mock_get_oid.mock_calls, [mock.call('foobar')])
        self.assertTrue(request.session.__setitem__.called)

    @mock.patch('substanced.sdi.views.folder.get_oid')
    def test_copy_none(self, mock_get_oid):
        context = mock.Mock()
        context.__contains__ = mock.Mock(return_value=True)
        request = mock.MagicMock()
        request.POST.get.return_value = ''

        inst = self._makeOne(context, request)
        inst.copy()

        request.session.flash.assert_called_once_with('No items to copy')
        self.assertFalse(mock_get_oid.called)

    def test_copy_finish_cancel(self):
        context = mock.Mock()
        request = mock.MagicMock()
        request.POST.get.return_value = ('foobar',)
        request.POST.get.side_effect = lambda x: {
            'foobar': 'foobar0',
            'form.copy_finish': 'cancel'}[x]
        inst = self._makeOne(context, request)
        inst.copy_finish()

        request.session.flash.assert_called_once_with('No items copied')
        self.assertEqual(request.session.__delitem__.call_args,
                         mock.call('tocopy'))

    @mock.patch('substanced.sdi.views.folder.find_objectmap')
    def test_copy_finish_one(self, mock_find_objectmap):
        context = mock.MagicMock()
        mock_folder = mock_find_objectmap().object_for()
        mock_folder.__parent__ = mock.MagicMock()
        mock_folder.__name__ = mock.sentinel.name
        request = mock.MagicMock()
        request.session.__getitem__.return_value = [123]
        request.POST.get.side_effect = lambda x: {
            'form.copy_finish': 'copy_finish'}[x]

        inst = self._makeOne(context, request)
        inst.copy_finish()

        self.assertEqual(mock_folder.__parent__.copy.call_args,
                         mock.call(mock.sentinel.name, context))
        request.sdiapi.flash_with_undo.assert_called_once_with('Copied 1 item')
        self.assertEqual(request.session.__delitem__.call_args,
                         mock.call('tocopy'))

    @mock.patch('substanced.sdi.views.folder.find_objectmap')
    def test_copy_finish_multi(self, mock_find_objectmap):
        context = mock.MagicMock()
        mock_folder = mock_find_objectmap().object_for()
        mock_folder.__parent__ = mock.MagicMock()
        mock_folder.__name__ = mock.sentinel.name
        request = mock.MagicMock()
        request.session.__getitem__.return_value = [123, 456]
        request.POST.get.side_effect = lambda x: {
            'form.copy_finish': 'copy_finish'}[x]

        inst = self._makeOne(context, request)
        inst.copy_finish()

        self.assertTrue(mock.call(123) in
                        mock_find_objectmap().object_for.mock_calls)
        self.assertTrue(mock.call(456) in
                        mock_find_objectmap().object_for.mock_calls)
        self.assertEqual(mock_folder.__parent__.copy.call_args,
                         mock.call(mock.sentinel.name, context))
        request.sdiapi.flash_with_undo.assert_called_once_with('Copied 2 items')
        self.assertEqual(request.session.__delitem__.call_args,
                         mock.call('tocopy'))

    @mock.patch('substanced.sdi.views.folder.find_objectmap')
    def test_copy_finish_already_exists(self, mock_find_objectmap):
        from ....folder import FolderKeyError
        context = mock.MagicMock()
        mock_folder = mock_find_objectmap().object_for()
        mock_folder.__parent__ = mock.MagicMock()
        mock_folder.__parent__.copy.side_effect = FolderKeyError(u'foobar')
        mock_folder.__name__ = mock.sentinel.name
        request = mock.MagicMock()
        request.session.__getitem__.return_value = [123]
        request.POST.get.side_effect = lambda x: {
            'form.copy_finish': 'copy_finish'}[x]

        inst = self._makeOne(context, request)
        self.assertRaises(HTTPFound, inst.copy_finish)
        request.session.flash.assert_called_once_with(u'foobar', 'error')

    @mock.patch('substanced.sdi.views.folder.get_oid')
    def test_move_one(self, mock_get_oid):
        context = mock.Mock()
        context.get.side_effect = lambda x: {
            'foobar': 'foobar',
            'foobar1': 'foobar1'}[x]
        request = mock.MagicMock()
        request.POST.get.return_value = 'foobar'

        inst = self._makeOne(context, request)
        inst.move()

        request.session.flash.assert_called_once_with(
            'Choose where to move the items:', 'info')
        self.assertEqual(mock_get_oid.mock_calls, [mock.call('foobar')])
        self.assertTrue(request.session.__setitem__.call_args,
                        [mock.call('tomove')])

    @mock.patch('substanced.sdi.views.folder.get_oid')
    def test_move_multi(self, mock_get_oid):
        context = mock.Mock()
        context.get.side_effect = lambda x: {'foobar': 'foobar',
                                             'foobar1': 'foobar1'}[x]
        request = mock.MagicMock()
        request.POST.get.return_value = 'foobar,foobar1'

        inst = self._makeOne(context, request)
        inst.move()

        request.session.flash.assert_called_once_with(
            'Choose where to move the items:', 'info')
        self.assertEqual(mock_get_oid.mock_calls,
                         [mock.call('foobar'), mock.call('foobar1')])
        self.assertTrue(request.session.__setitem__.call_args,
                        [mock.call('tomove')])

    @mock.patch('substanced.sdi.views.folder.get_oid')
    def test_move_missing_child(self, mock_get_oid):
        context = mock.Mock()
        context.get.side_effect = lambda x: {'foobar': 'foobar',
                                             'foobar1': 'foobar1'}.get(x, None)
        request = mock.MagicMock()
        request.POST.get.return_value = 'foobar,foobar2'

        inst = self._makeOne(context, request)
        inst.move()

        request.session.flash.assert_called_once_with(
            'Choose where to move the items:', 'info')
        self.assertEqual(mock_get_oid.mock_calls, [mock.call('foobar')])
        self.assertTrue(request.session.__setitem__.call_args,
                        [mock.call('tomove')])

    @mock.patch('substanced.sdi.views.folder.get_oid')
    def test_move_none(self, mock_get_oid):
        context = mock.Mock()
        context.get.side_effect = lambda x: {'foobar': 'foobar',
                                             'foobar1': 'foobar1'}.get(x, None)
        request = mock.MagicMock()
        request.POST.get.return_value = ''

        inst = self._makeOne(context, request)
        inst.move()

        request.session.flash.assert_called_once_with('No items to move')
        self.assertFalse(mock_get_oid.called)
        self.assertFalse(request.session.__setitem__.called)

    def test_move_finish_cancel(self):
        context = mock.Mock()
        request = mock.MagicMock()
        request.POST.get.return_value = 'foobar'
        request.POST.get.side_effect = lambda x: {
            'foobar': 'foobar0',
            'form.move_finish': 'cancel'}[x]
        inst = self._makeOne(context, request)
        inst.move_finish()

        request.session.flash.assert_called_once_with('No items moved')
        self.assertEqual(request.session.__delitem__.call_args,
                         mock.call('tomove'))

    @mock.patch('substanced.sdi.views.folder.find_objectmap')
    def test_move_finish_one(self, mock_find_objectmap):
        context = mock.MagicMock()
        mock_folder = mock_find_objectmap().object_for()
        mock_folder.__parent__ = mock.MagicMock()
        mock_folder.__name__ = mock.sentinel.name
        request = mock.MagicMock()
        request.session.__getitem__.return_value = [123]
        request.POST.get.side_effect = lambda x: {
            'form.move_finish': 'move_finish'}[x]

        inst = self._makeOne(context, request)
        inst.move_finish()

        self.assertEqual(mock_folder.__parent__.move.call_args,
                         mock.call(mock.sentinel.name, context))
        request.sdiapi.flash_with_undo.assert_called_once_with('Moved 1 item')
        self.assertEqual(request.session.__delitem__.call_args,
                         mock.call('tomove'))

    @mock.patch('substanced.sdi.views.folder.find_objectmap')
    def test_move_finish_multi(self, mock_find_objectmap):
        context = mock.MagicMock()
        mock_folder = mock_find_objectmap().object_for()
        mock_folder.__parent__ = mock.MagicMock()
        mock_folder.__name__ = mock.sentinel.name
        request = mock.MagicMock()
        request.session.__getitem__.return_value = [123, 456]
        request.POST.get.side_effect = lambda x: {
            'form.move_finish': 'move_finish'}[x]

        inst = self._makeOne(context, request)
        inst.move_finish()

        self.assertTrue(mock.call(123) in
                        mock_find_objectmap().object_for.mock_calls)
        self.assertTrue(mock.call(456) in
                        mock_find_objectmap().object_for.mock_calls)
        self.assertEqual(mock_folder.__parent__.move.call_args,
                         mock.call(mock.sentinel.name, context))
        self.assertEqual(request.session.__delitem__.call_args,
                         mock.call('tomove'))
        request.sdiapi.flash_with_undo.assert_called_once_with('Moved 2 items')

    @mock.patch('substanced.sdi.views.folder.find_objectmap')
    def test_move_finish_already_exists(self, mock_find_objectmap):
        from ....folder import FolderKeyError
        context = mock.MagicMock()
        mock_folder = mock_find_objectmap().object_for()
        mock_folder.__parent__ = mock.MagicMock()
        mock_folder.__parent__.move.side_effect = FolderKeyError(u'foobar')
        mock_folder.__name__ = mock.sentinel.name
        request = mock.MagicMock()
        request.session.__getitem__.return_value = [123]
        request.POST.get.side_effect = lambda x: {
            'form.move_finish': 'move_finish'}[x]

        inst = self._makeOne(context, request)
        self.assertRaises(HTTPFound, inst.move_finish)
        request.session.flash.assert_called_once_with(u'foobar', 'error')

    def test_buttons_is_None(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        request.registry.content = DummyContent(buttons=None)
        result = inst._buttons(context, request)
        self.assertEqual(result, [])

    def test_buttons_is_clbl(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        def sdi_buttons(contexr, request, default_buttons):
            return 'abc'
        inst = self._makeOne(context, request)
        request.registry.content = DummyContent(buttons=sdi_buttons)
        result = inst._buttons(context, request)
        self.assertEqual(result, 'abc')

class DummyFolder(object):
    oid_store = {}

    def __init__(self, exc=None):
        self.exc = exc

    def check_name(self, name):
        if self.exc:
            raise self.exc
        return name

class DummyContent(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def create(self, iface, *arg, **kw):
        return getattr(self, iface, None)

    def metadata(self, context, name, default=None):
        return getattr(self, name, default)


class DummyPost(dict):
    def __init__(self, getall_result=(), get_result=None):
        self.getall_result = getall_result
        self.get_result = get_result

    def getall(self, name):
        return self.getall_result

    def get(self, name, default=None):
        if self.get_result is None:
            return default
        return self.get_result

class DummySDIAPI(object):
    def mgmt_path(self, *arg, **kw):
        return '/mgmt_path'


dummy_folder_contents_0 = [{
    'name': 'the_name',
    'icon': 'the_icon',
    'url':  'http://foo.bar',
    'viewable':  True,
    'deletable':  True,
    'columns': [],
    }]

dummy_column_headers_sg_0 = []


dummy_folder_contents_2 = [{
    'name': 'the_name',
    'icon': 'the_icon',
    'url':  'http://foo.bar',
    'viewable':  True,
    'deletable':  True,
    'columns': ['value4col1', 'value4col2'],
    }]

dummy_column_headers_sg_2 = [{
    'field': 'col1',
    }, {
    'field': 'col2',
    }]

