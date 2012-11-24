import itertools
import re

import colander


from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_defaults

from ...folder import FolderKeyError
from ...form import FormView
from ...interfaces import IFolder
from ...objectmap import find_objectmap
from ...schema import Schema
from ...util import (
    oid_of,
    JsonDict,
    )

from .. import (
    mgmt_view,
    sdi_add_views,
    sdi_folder_contents,
    default_sdi_buttons,
    default_sdi_columns,
    )

_marker = object()

def rename_duplicated_resource(context, name):
    """Finds next available name inside container by appending
    dash and positive number.
    """
    if name not in context:
        return name

    m = re.search(r'-(\d+)$', name)
    if m:
        new_id = int(m.groups()[0]) + 1
        new_name = name.rsplit('-', 1)[0] + u'-%d' % new_id
    else:
        new_name = name + u'-1'

    if new_name in context:
        return rename_duplicated_resource(context, new_name)
    else:
        return new_name

@colander.deferred
def name_validator(node, kw):
    context = kw['request'].context

    def namecheck(node, value):
        try:
            context.check_name(value)
        except Exception as e:
            raise colander.Invalid(node, e.args[0], value)

    return colander.All(
        colander.Length(min=1, max=100),
        namecheck,
        )

class AddFolderSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        validator=name_validator,
        )

@mgmt_view(
    context=IFolder,
    name='add_folder',
    tab_condition=False,
    permission='sdi.add-content',
    renderer='substanced.sdi:templates/form.pt'
    )
class AddFolderView(FormView):
    title = 'Add Folder'
    schema = AddFolderSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct['name']
        folder = registry.content.create('Folder')
        self.context[name] = folder
        return HTTPFound(location=self.request.mgmt_path(self.context))

@view_defaults(
    context=IFolder,
    name='contents',
    renderer='templates/contents.pt'
    )
class FolderContentsViews(object):

    sdi_add_views = staticmethod(sdi_add_views) # for testing
    sdi_folder_contents = staticmethod(sdi_folder_contents) # for testing

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def _buttons(self, context, request):
        buttons = default_sdi_buttons(context, request)
        custom_buttons = request.registry.content.metadata(
            context, 'buttons', _marker)
        if custom_buttons is None:
            return []
        if custom_buttons is not _marker:
            buttons = custom_buttons(context, request, buttons)
        return buttons

    def _column_headers(self, context, request):
        headers = []
        non_sortable = [0]
        non_filterable = [0]

        columns = default_sdi_columns(self, None, request)

        custom_columns = request.registry.content.metadata(
            context, 'columns', _marker)

        if custom_columns is None:
            return headers, non_sortable, non_filterable

        if custom_columns is not _marker:
            columns = custom_columns(context, None, request, columns)
        
        for order, column in enumerate(columns):
            headers.append(column['name'])
            sortable = column.get('sortable', True)
            if not sortable:
                non_sortable.append(order + 1)
            filterable = column.get('filterable', True)
            if not filterable:
                non_filterable.append(order + 1)

        return headers, non_sortable, non_filterable

    def _column_headers_sg(self, context, request):
        """Generate columns from SlickGrid."""
        # TODO As the slickgrid's column desription format contains different fields
        # from our internal column schema (both more feature rich, and
        # uses different attributes), we will need to convert our schema to
        # SlickGrid's here. As there is no "universal grid column description format" exists,
        # this also means that here we have to limit the flexible configuration
        # possibilities of the slickgrid to those use cases that we wish to support.
        headers = []

        columns = default_sdi_columns(self, None, request)

        custom_columns = request.registry.content.metadata(
            context, 'columns', _marker)

        if custom_columns is None:
            return headers

        if custom_columns is not _marker:
            columns = custom_columns(context, None, request, columns)
        
        for order, column in enumerate(columns):
            name = column['name']
            field = column['field']
            sortable = column.get('sortable', True)
            formatter = column.get('formatter', '')
            
            headers.append(
                { "id": field, 
                "name": name, "field": field,
                "width": 120, "minWidth": 120,
                "cssClass": "cell-%s" % field, "sortable": sortable,
                "formatterName": formatter,
                },
                )

        return headers


    @mgmt_view(
        request_method='GET',
        permission='sdi.view'
        )
    def show(self):
        request = self.request
        context = self.context

        headers, non_sortable, non_filterable = self._column_headers(
            context, request
            )
        # XXX the parallel equivalent of the above line, for slickgrid.
        columns_sg = self._column_headers_sg(
            context, request
            )

        buttons = self._buttons(context, request)

        addables = self.sdi_add_views(context, request)

        seq = self.sdi_folder_contents(context, request) # generator

        # We need an accurate length but len(self.context) will not take into
        # account hidden items. To gen an accurate length we tee the generator
        # and exaust one copy to produce a sum, we use the other copy as the
        # items we pass to the template.  This is probably unsat for huge
        # folders, but at least has a slight advantage over doing
        # len(list(seq)) because we don't unnecessarily create a large data
        # structure in memory.
        items, items_copy = itertools.tee(seq)
        num_items = sum(1 for _ in items_copy) 

        # construct the slickgrid widget options.
        slickgrid_options = dict(
            # default options for Slick.Grid come here.
            editable = False,
            enableAddRow = False,
            enableCellNavigation = True,
            asyncEditorLoading = True,
            forceFitColumns = True,
            rowHeight = 34,
            )
        # The items for the slickgrid are really in a format similar to the
        # items used for the static table. However, it has some problems so we have
        # to convert the records:
        #
        # - The records must be json-marshallable, so we convert 'deletable' to bool.
        # - SlickGrid requires a unique id to each row
        # - more reasonable keys, that match slickgrid's rendering (actually, we could leave
        #   it intact here, and just handle this from the formatters in the js code,
        #   but then it would be more difficult to understand the code.
        # - remove the 'columns' attribute that contains the rendered parts. Slickgrid will
        #   format the html on the client.
        #
        items_sg = []
        my_items, items = itertools.tee(items, 2)
        for i, item in enumerate(my_items):
            name = item['name']
            item_sg = dict(
                id=name,    # Use the unique name, as an id.
                    # (A unique row id is needed for slickgrid.
                    # In addition, we will pass back this same id from the client,
                    # when a row is selected for an operation.)
                deletable=bool(item['deletable']),
                name=name,
                name_icon=item['icon'],
                name_url=item['url'],
            )
            if item['viewable']:
                item_sg['name_url'] = item['url']
            for index_sg, column_value in enumerate(item['columns']):
                field_sg = columns_sg[index_sg]['field']
                item_sg[field_sg] = column_value
            items_sg.append(item_sg)
        # We pass the wrapper options which contains all information
        # needed to configure the several components of the grid config.
        slickgrid_wrapper_options = JsonDict(
            configName='sdi-content-grid', # << this refers to slickgrid-config.js
            columns=columns_sg,
            slickgridOptions=slickgrid_options,
            items=items_sg,
            # initial sorting (The grid will really not sort the initial data,
            # just display it in the order we provide it. It will use the information
            # to just visually show in the headers the sorted column.)
            sortCol = columns_sg[0]['field'], 
            sortDir = True,   # True ascending, or False descending.
            )

        return dict(
            items=items, # NB: do not use "seq" here, we teed it above
            num_items=num_items,
            addables=addables,
            headers=headers,
            buttons=buttons,
            non_filterable=non_filterable,
            non_sortable=non_sortable,
            # XXX for slickgrid
            slickgrid_wrapper_options=slickgrid_wrapper_options,
            )

    @mgmt_view(
        request_method='POST',
        request_param="form.delete",
        permission='sdi.manage-contents',
        tab_condition=False,
        check_csrf=True
        )
    def delete(self):
        request = self.request
        context = self.context
        todelete = request.POST.get('item-modify').split(',')
        deleted = 0
        for name in todelete:
            v = context.get(name)
            if v is not None:
                del context[name]
                deleted += 1
        if not deleted:
            msg = 'No items deleted'
            request.session.flash(msg)
        elif deleted == 1:
            msg = 'Deleted 1 item'
            request.flash_with_undo(msg)
        else:
            msg = 'Deleted %s items' % deleted
            request.flash_with_undo(msg)
        return HTTPFound(request.mgmt_path(context, '@@contents'))

    @mgmt_view(
        request_method='POST',
        request_param="form.duplicate",
        permission='sdi.manage-contents',
        tab_condition=False,
        check_csrf=True
        )
    def duplicate(self):
        request = self.request
        context = self.context
        toduplicate = request.POST.get('item-modify').split(',')
        for name in toduplicate:
            newname = rename_duplicated_resource(context, name)
            context.copy(name, context, newname)
        if not len(toduplicate):
            msg = 'No items duplicated'
            request.session.flash(msg)
        elif len(toduplicate) == 1:
            msg = 'Duplicated 1 item'
            request.flash_with_undo(msg)
        else:
            msg = 'Duplicated %s items' % len(toduplicate)
            request.flash_with_undo(msg)
        return HTTPFound(request.mgmt_path(context, '@@contents'))

    @mgmt_view(
        request_method='POST',
        request_param="form.rename",
        permission='sdi.manage-contents',
        renderer='templates/rename.pt',
        tab_condition=False,
        check_csrf=True
        )
    def rename(self):
        request = self.request
        context = self.context
        torename = request.POST.get('item-modify').split(',')
        if not torename:
            request.session.flash('No items renamed')
            return HTTPFound(request.mgmt_path(context, '@@contents'))
        return dict(torename=[context.get(name)
                              for name in torename
                              if name in context])

    @mgmt_view(
        request_method='POST',
        request_param="form.rename_finish",
        name="rename",
        permission='sdi.manage-contents',
        tab_condition=False,
        check_csrf=True
        )
    def rename_finish(self):
        request = self.request
        context = self.context

        if self.request.POST.get('form.rename_finish') == "cancel":
            request.session.flash('No items renamed')
            return HTTPFound(request.mgmt_path(context, '@@contents'))

        torename = request.POST.getall('item-rename')
        try:
            for old_name in torename:
                new_name = request.POST.get(old_name)
                context.rename(old_name, new_name)
        except FolderKeyError as e:
            self.request.session.flash(e.args[0], 'error')
            raise HTTPFound(request.mgmt_path(context, '@@contents'))

        if len(torename) == 1:
            msg = 'Renamed 1 item'
            request.flash_with_undo(msg)
        else:
            msg = 'Renamed %s items' % len(torename)
            request.flash_with_undo(msg)
        return HTTPFound(request.mgmt_path(context, '@@contents'))

    @mgmt_view(
        request_method='POST',
        request_param="form.copy",
        permission='sdi.view',
        tab_condition=False,
        check_csrf=True
        )
    def copy(self):
        request = self.request
        context = self.context
        tocopy = request.POST.get('item-modify').split(',')
        
        print tocopy

        if tocopy:
            l = []
            for name in tocopy:
                obj = context.get(name)
                if obj is not None:
                    l.append(oid_of(obj))
            request.session['tocopy'] = l
            request.session.flash('Choose where to copy the items:', 'info')
        else:
            request.session.flash('No items to copy')

        return HTTPFound(request.mgmt_path(context, '@@contents'))

    @mgmt_view(
        request_method='POST',
        request_param="form.copy_finish",
        permission='sdi.manage-contents',
        tab_condition=False,
        check_csrf=True
        )
    def copy_finish(self):
        request = self.request
        context = self.context
        objectmap = find_objectmap(context)
        tocopy = request.session['tocopy']
        del request.session['tocopy']

        if self.request.POST.get('form.copy_finish') == "cancel":
            request.session.flash('No items copied')
            return HTTPFound(request.mgmt_path(context, '@@contents'))

        try:
            for oid in tocopy:
                obj = objectmap.object_for(oid)
                obj.__parent__.copy(obj.__name__, context)
        except FolderKeyError as e:
            self.request.session.flash(e.args[0], 'error')
            raise HTTPFound(request.mgmt_path(context, '@@contents'))

        if len(tocopy) == 1:
            msg = 'Copied 1 item'
            request.flash_with_undo(msg)
        else:
            msg = 'Copied %s items' % len(tocopy)
            request.flash_with_undo(msg)

        return HTTPFound(request.mgmt_path(context, '@@contents'))

    @mgmt_view(
        request_method='POST',
        request_param="form.move",
        permission='sdi.view',
        tab_condition=False,
        check_csrf=True
        )
    def move(self):
        request = self.request
        context = self.context
        tomove = request.POST.get('item-modify').split(',')

        if tomove:
            l = []
            for name in tomove:
                obj = context.get(name)
                if obj is not None:
                    l.append(oid_of(obj))
            request.session['tomove'] = l
            request.session.flash('Choose where to move the items:', 'info')
        else:
            request.session.flash('No items to move')

        return HTTPFound(request.mgmt_path(context, '@@contents'))

    @mgmt_view(
        request_method='POST',
        request_param="form.move_finish",
        permission='sdi.manage-contents',
        tab_condition=False,
        check_csrf=True
        )
    def move_finish(self):
        request = self.request
        context = self.context
        objectmap = find_objectmap(context)
        tomove = request.session['tomove']
        del request.session['tomove']

        if self.request.POST.get('form.move_finish') == "cancel":
            request.session.flash('No items moved')
            return HTTPFound(request.mgmt_path(context, '@@contents'))

        try:
            for oid in tomove:
                obj = objectmap.object_for(oid)
                obj.__parent__.move(obj.__name__, context)
        except FolderKeyError as e:
            self.request.session.flash(e.args[0], 'error')
            raise HTTPFound(request.mgmt_path(context, '@@contents'))

        if len(tomove) == 1:
            msg = 'Moved 1 item'
            request.flash_with_undo(msg)
        else:
            msg = 'Moved %s items' % len(tomove)
            request.flash_with_undo(msg)

        return HTTPFound(request.mgmt_path(context, '@@contents'))

