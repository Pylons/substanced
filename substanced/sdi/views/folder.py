import itertools
import re

import colander


from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_defaults
from pyramid.security import has_permission

from ...folder import FolderKeyError
from ...form import FormView
from ...interfaces import IFolder
from ...objectmap import find_objectmap
from ...schema import Schema
from ...util import (
    JsonDict,
    get_oid,
    find_catalog,
    )

from .. import (
    mgmt_view,
    sdi_add_views,
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
        return HTTPFound(location=self.request.sdiapi.mgmt_path(self.context))

@view_defaults(
    context=IFolder,
    name='contents',
    renderer='templates/contents.pt'
    )
class FolderContentsViews(object):

    sdi_add_views = staticmethod(sdi_add_views) # for testing

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def _modified_items(self):
        items = self.request.POST.get('item-modify', '').split(',')
        modified = filter(None, items) # remove empty
        return modified

    def _buttons(self):
        context = self.context
        request = self.request
        buttons = default_sdi_buttons(context, request)
        custom_buttons = request.registry.content.metadata(
            context, 'buttons', _marker)
        if custom_buttons is None:
            return []
        if custom_buttons is not _marker:
            buttons = custom_buttons(context, request, buttons)
        return buttons

    def _column_headers(self):
        context = self.context
        request = self.request

        headers = []

        content_registry  = request.registry.content

        columns = default_sdi_columns(self, None, request)

        custom_columns = content_registry.metadata(context, 'columns', _marker)

        if custom_columns is None:
            return headers

        if custom_columns is not _marker:
            columns = custom_columns(context, None, request, columns)
        
        for order, column in enumerate(columns):
            name = column['name']
            field = column['field']
            sortable = column.get('sortable', True)

            if context.is_ordered():
                sortable = False

            formatter = column.get('formatter', '')
            cssClass = column.get('cssClass', '')
            cssClass= "cell-%s" % field + ((' ' + cssClass) if cssClass else '')

            headers.append({
                "id": field,
                "name": name,
                "field": field,
                "width": 120,
                "minWidth": 120,
                "cssClass": cssClass,
                "sortable": sortable,
                "formatterName": formatter,
                })

        return headers
   
    def _folder_contents(
        self,
        start=None,
        end=None,
        reverse=False,
        sort_index=None,
        filter_text=None,
        ):

        """
        Returns a sequence of dictionaries that can be used by a 'folder
        contents' view.  The sequence is implemented as a generator.  The
        ``folder`` object passed must implement the methods of the
        :class:`substanced.interfaces.IFolder` interface, and the ``request``
        object passed must be a Pyramid request.

        Each dictionary in the sequence reflects information about a single
        subobject in the folder.  Each dictionary in the sequence returned will
        have the following keys:

        ``name``

          The name of the subobject.

        ``deletable``

          A boolean indicating whether or not this subobject is deletable.

        ``url``

          The URL to the subobject.  This will be
          ``/path/to/subob/@@manage_main``.

        ``columns``

          The column values obtained from this subobject's attributes, as
          defined by the ``columns`` content-type hook (or the default columns,
          if no hook was supplied).

        This function considers a subobject:

        - 'deletable' if the user has the ``sdi.manage-contents`` permission on
          ``folder`` or if the subobject has a ``__sdi_deletable__`` attribute
          which resolves to a boolean ``True`` value.

        This function honors one subobject hook:: ``__sdi_deletable__``.  If a
        subobject has an attribute named ``__sdi_deletable__``, it is expected
        to be either a boolean or a callable.  If ``__sdi_deletable__`` is a
        boolean, the value is used verbatim.  If ``__sdi_deletable__`` is a
        callable, the callable is called with two positional arguments: the
        subobject and the request; the result is expected to be a boolean.  If
        a subobject has an ``__sdi_deletable__`` attribute, and its resolved
        value is not ``None``, the value will used as the ``deletable`` value
        returned in the dictionary for the subobject.  If ``__sdi_deletable__``
        does not exist on a subobject or resolves to ``None``, the
        ``deletable`` value will be the default: a boolean indicating whether
        the current user has the ``sdi.manage-contents`` permission on the
        ``folder``.

        This function honors three content type hooks: ``icon``, ``buttons``,
        and ``columns``.

        The first content type hook is named ``icon``.  If the ``icon``
        supplied to the content type configuration of a subobject is a
        callable, the callable will be passed the subobject and the
        ``request``; it is expected to return an icon name or ``None``.
        ``icon`` may alternately be either ``None`` or a string representing a
        icon name instead of a callable.

        The second content type hook is named ``buttons``.  The folder contents
        view is a good place to wire up application specific functionality that
        depends on content selection, so the button toolbar that shows up at
        the bottom of the page is customizable. The default buttons can be
        overridden by supplying a ``buttons`` keyword argument to the content
        type argument list.  It must be a callable object which accepts
        ``context, request, default_buttonspec`` and which returns a list of
        dictionaries; each dictionary represents a button or a button group.

        The ``buttons`` callable you supply will be passed the ``context`` and
        the ``request`` and ``buttonspec`` (a sequence of default button
        specifications). It must return a list of dictionaries representing
        button specifications with at least a ``type`` key for the button
        specification type and a ``buttons`` key with a list of dictionaries
        representing the buttons. The ``type`` should be one of the string
        values ``group`` or ``single``. A group will display its buttons side
        by side, with no margin, while the single type will display each button
        separately.

        Each button in a ``buttons`` dictionary is rendered using the button
        tag and requires five keys: ``id`` for the button's id attribute,
        ``name`` for the button's name attribute, ``class`` for any additional
        css classes to be applied to it (see below), ``value`` for the value
        that will be passed as a request parameter when the form is submitted
        and ``text`` for the button's text.

        The ``class`` value is special because it will define the button's
        behavior. There are four mutually exclusive class names that can be
        used. ``btn-sdi-act`` is for buttons that will always be enabled,
        independently of any selected content items. ``btn-sdi-sel`` means
        the button will start as disabled and will only be enabled once one
        or more items are selected. ``btn-sdi-one`` means the button will
        only be enabled if there's exactly one item selected. Finally,
        ``btn-sdi-del`` means the button will stay disabled until one or
        more *deletable* items are selected. You *must* use one of these
        classes for the button to be enabled.
        
        The ``class`` value can contain several classes separated by spaces.
        In addition to the classes mentioned above, any custom css class or any
        bootstrap button class can be used.
        
        Finally, each button can optionally include an ``enabled_for`` key,
        which will point to a callable that will be passed a subobject from the
        current folder and must return True if the button should be enabled for
        that subobect or False if not.

        Most of the time, the best strategy for using the buttons callable will
        be to return a value containing the default buttonspec sequence passed
        in to the function (it will be a list).::

          def custom_buttons(context, request, default_buttonspec):
              def some_condition(folder, subobject, request):
                  return getattr(context, 'can_use_button1', False)

              custom_buttonspec = [{'type': 'single',
                                   'buttons': [{'id': 'button1',
                                                'name': 'button1',
                                                'class': 'btn-sdi-sel',
                                                'enabled_for': some_condition,
                                                'value': 'button1',
                                                'text': 'Button 1'},
                                               {'id': 'button2',
                                                'name': 'button2',
                                                'class': 'btn-sdi-act',
                                                'value': 'button2',
                                                'text': 'Button 2'}]}]
              return default_buttonspec + custom_buttonspec

          @content(
              'My Custom Folder',
              buttons=custom_buttons,
              )
          class MyCustomFolder(Persistent):
              pass

        Once the buttons are defined, a view needs to be registered to handle
        the new buttons. The view configuration has to set Folder as a context
        and include a ``request_param`` predicate with the same name as the
        ``value`` defined for the corresponding button. The following template
        can be used to register such views, changing only the ``request_param``
        value::

          @mgmt_view(
          context=IFolder,
          name='contents',
          renderer='substanced.sdi:templates/contents.pt',
          permission='sdi.manage-contents',
          request_method='POST',
          request_param='button1',
          tab_condition=False,
          )
          def button1(context, request):
              # add button functionality here, then go back to contents
              request.session.flash('Just did what button1 does')
              return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

        Note that context has to be IFolder for this to work. If you need to
        restrict a button to some specific list of content types, the Pyramid
        ``content_type`` predicate can be used.

        The third content-type hook is named ``columns``.  To display the
        contents using a table with any given subobject attributes, a callable
        named ``columns`` can be passed to a content type as metadata.  When
        the folder contents SDI view is invoked against an object of the type,
        the ``columns`` callable will be passed the folder, a subobject, the
        ``request``, and a default column specification. It will be called once
        for every object in the folder to obtain column representations for
        each of its subobjects.  It must return a list of dictionaries with at
        least a ``name`` key for the column header, a ``field`` key for the
        field name to use in javascript manipulations, and a ``value`` key with
        the correct column value given the subobject. The callable **must** be
        prepared to receive subobjects that will *not* have the desired
        attributes (the subobject passed will be ``None`` at least once in
        order for the system to compute headers).

        In addition to ``name``, ``field`` and ``value``, the column dictionary
        can contain the keys ``sortable`` and ``formatter``. The first one
        specifies whether the column will have buttons for sorting the
        rows. The default value is ``True``. The last key, ``formatter``, can
        give the name of a javascript method for formatting the
        ``value``. Currently, available formatters are ``icon_label_url`` and
        ``date``.
        
        The ``icon_label_url`` formatter gets the URL and icon (if any) of the
        subobject and creates a link using ``value`` as link text. The ``date``
        formatter expects that ``value`` is an ISO date and returns a text date
        in the format "<month name> <day>, <year>".

        Here's an example of using the ``columns`` content type hook::

          def custom_columns(folder, subobject, request, default_columnspec):
              return default_columnspec + [
                  {'name': 'Review date',
                   'field': 'date',
                   'value': getattr(subobject, 'review_date', ''),
                   'sortable': True,
                   'formatter': 'date'},
                  {'name': 'Rating',
                   'field': 'rating',
                   'value': getattr(subobject, 'rating', ''),
                   'sortable': True}
                  ]

          @content(
              'My Custom Folder',
              columns=custom_columns,
              )
          class MyCustomFolder(Persistent):
              pass
              
        In some cases, it might be needed to override the custom columns
        defined for an already existing content type. This can be accomplished
        by registering the content type a second time, but passing the columns
        then. For example, to add columns to the user folder content listing
        from substanced::
        
          from substanced import root_factory
          from substanced.interfaces import IUsers
          from substanced.principal import Users
          from myapp import custom_user_columns
          
          def main(global_config, **settings):
              config = Configurator(root_factory=root_factory, settings=settings)
              config.include('substanced')
              config.add_content_type(IUsers,
                                  factory=Users,
                                  icon='icon-list-alt',
                                  columns=custom_user_columns)
              config.scan()

        XXX TODO Document ``sort_index``, ``reverse``, ``filter_text``.
        sort_index now also takes a string which looks up the catalog index.
        """
        folder = self.context
        request = self.request
        catalog = find_catalog(folder, 'system')
        objectmap = find_objectmap(folder)

        path = catalog['path']
        allowed = catalog['allowed']

        if start is None:
            start = 0

        if end is None:
            end = start + 40

        q = ( path.eq(folder, depth=1, include_origin=False) &
              allowed.allows(request, 'sdi.view') )

        if filter_text:
            if not filter_text.endswith('*'):
                filter_text = filter_text + '*' # glob (prefix) search
            text = catalog['text']
            q = q & text.eq(filter_text)

        # BR: sort_index can be a string with the name of the catalog index,
        # or, the index object itself. If it is a name, it is looked up.  XXX
        # Untested!!! XXX TODO!!!
        #
        # CM: this should be a tuple of (catalog_name, index_name) at least,
        # and optionally a callback that accepts the folder, and which returns
        # the index object.  This logic should not be done here; it should
        # be done in views that call this method instead.
            
        if isinstance(sort_index, basestring):
            try:
                sort_index = catalog[sort_index]
            except KeyError:
                keys = tuple(catalog.keys())
                raise KeyError(
                    (
                        'Index %r is missing from the catalog. '
                        'If sort_index is a string, then it must match the '
                        'name of a catalog index. %r' % (sort_index, keys)
                     )
                    )

        if folder.is_ordered() and sort_index is None:
            # hypatia resultset.sort will call IFolder.sort method
            sort_index = folder

        if sort_index is None:
            sort_index = catalog['name']

        resultset = q.execute()
        folder_length = len(resultset)

        resultset = resultset.sort(sort_index, reverse=reverse, limit=end)
        ids = resultset.ids

        can_manage = bool(has_permission('sdi.manage-contents', folder,request))
        custom_columns = request.registry.content.metadata(
            folder, 'columns', _marker)

        buttons = self._buttons()

        records = []

        for oid in itertools.islice(ids, start, end):
            resource = objectmap.object_for(oid)
            name = getattr(resource, '__name__', '')
            deletable = getattr(resource, '__sdi_deletable__', None)
            if deletable is not None:
                if callable(deletable):
                    deletable = deletable(resource, request)
            if deletable is None:
                deletable = can_manage
            deletable = bool(deletable) # cast return/attr value to bool
            icon = request.registry.content.metadata(resource, 'icon')
            if callable(icon):
                icon = icon(resource, request)
            url = request.sdiapi.mgmt_path(resource, '@@manage_main')
            record = dict(
                id=name,
                # Use the unique name, as an id.  (A unique row id is needed
                # for slickgrid.  In addition, we will pass back this same id
                # from the client, when a row is selected for an operation.)
                deletable=deletable,
                name=name,
                name_icon=icon,
                name_url=url,
            )
            columns = default_sdi_columns(folder, resource, request)
            if custom_columns is None:
                columns = []
            elif custom_columns is not _marker:
                columns = custom_columns(folder, resource, request, columns)
            for column in columns:
                field = column['field']
                record[field] = column['value']
            disable = []
            for button_group in buttons:
                for button in button_group['buttons']:
                    if 'enabled_for' not in button:
                        continue
                    condition = button['enabled_for']
                    if not callable(condition):
                        continue
                    if not condition(folder, resource, request):
                        disable.append(button['id'])
            record['disable'] = disable
            records.append(record)

        return folder_length, records

    @mgmt_view(
        request_method='GET',
        permission='sdi.view',
        xhr=False,
        )
    def show(self):
        request = self.request
        context = self.context

        columns = self._column_headers()

        buttons = self._buttons()

        addables = self.sdi_add_views(context, request)

        # construct the default slickgrid widget options
        slickgrid_options = dict(
            editable = False,
            enableAddRow = False,
            enableCellNavigation = True,
            asyncEditorLoading = True,
            forceFitColumns = True,
            rowHeight = 35,
            )

        minimum_load = 40 # load at least this many records.

        # Is the folder content ordered?
        is_ordered = context.is_ordered()
        is_reorderable = context.is_reorderable()

        if is_ordered:
            # Nothing is sortable if the content is ordered.
            sortCol = None
        else:
            # The sorted column is always the first sortable column in the row.
            # This gives the visual cue to the user who can see the sorted
            # column and its direction.  It does _not_ affect the actual
            # sorting, which is done on the server and not on the grid.
            for col in columns:
                if col.get('sortable', True):
                    # We found the first sortable column.
                    sortCol = col['field']
                    break
            else:
                # Nothing is sortable.
                sortCol = None

        sortDir = True    # True ascending, or False descending.
        reverse = (not sortDir)

        folder_length, records = self._folder_contents(
            0, minimum_load, reverse=reverse, sort_index=sortCol
            )

        items  = {
            'from':0,
            'to':minimum_load,
            'records':records,
            'total':folder_length,
            }

        # We pass the wrapper options which contains all information
        # needed to configure the several components of the grid config.

        slickgrid_wrapper_options = JsonDict(
            # below line refers to slickgrid-config.js
            configName='sdi-content-grid',
            columns=columns,
            slickgridOptions=slickgrid_options,
            items=items,
            # initial sorting (The grid will really not sort the initial data,
            # just display it in the order we provide it. It will use the
            # information to just visually show in the headers the sorted
            # column.)
            sortCol=sortCol,
            sortDir=sortDir,
            # is the grid reorderable?
            isReorderable=is_reorderable,
            #
            # Parameters for the remote data model
            url='',   # use same url for ajax
            minimumLoad=minimum_load,
            )

        result = dict(
            addables=addables,
            buttons=buttons,
            slickgrid_wrapper_options=slickgrid_wrapper_options,
            )

        return result

    @mgmt_view(
        request_method='GET',
        permission='sdi.view',
        xhr=True,
        renderer='json',
        )
    def show_json(self):
        return self._get_json()

    def _get_json(self):
        request = self.request
        if 'from' in request.params:
            start = int(request.params.get('from'))
            end = int(request.params.get('to'))
            sort_col = request.params.get('sortCol')
            sort_dir = request.params.get('sortDir') in ('true', 'True')
            filter_text = request.params.get('filter', '').strip()

            reverse = (not sort_dir)


            folder_length, records = self._folder_contents(
                start, end, reverse=reverse, filter_text=filter_text,
                sort_index=sort_col,
                )

            items = {
                'from': start,
                'to': end,
                'records': records,
                'total': folder_length,
                }
        else:
            # If the request did not ask for an data update,
            # just return an empty dict.
            items = {}

        return items

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
        todelete = self._modified_items()
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
            request.sdiapi.flash_with_undo(msg)
        else:
            msg = 'Deleted %s items' % deleted
            request.sdiapi.flash_with_undo(msg)
        return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

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
        toduplicate = self._modified_items()
        for name in toduplicate:
            newname = rename_duplicated_resource(context, name)
            context.copy(name, context, newname)
        if not len(toduplicate):
            msg = 'No items duplicated'
            request.session.flash(msg)
        elif len(toduplicate) == 1:
            msg = 'Duplicated 1 item'
            request.sdiapi.flash_with_undo(msg)
        else:
            msg = 'Duplicated %s items' % len(toduplicate)
            request.sdiapi.flash_with_undo(msg)
        return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

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
        torename = self._modified_items()
        if not torename:
            request.session.flash('No items renamed')
            return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))
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
            return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

        torename = request.POST.getall('item-rename')
        try:
            for old_name in torename:
                new_name = request.POST.get(old_name)
                context.rename(old_name, new_name)
        except FolderKeyError as e:
            self.request.session.flash(e.args[0], 'error')
            raise HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

        if len(torename) == 1:
            msg = 'Renamed 1 item'
            request.sdiapi.flash_with_undo(msg)
        else:
            msg = 'Renamed %s items' % len(torename)
            request.sdiapi.flash_with_undo(msg)
        return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

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
        tocopy = self._modified_items()
        
        if tocopy:
            l = []
            for name in tocopy:
                obj = context.get(name)
                if obj is not None:
                    l.append(get_oid(obj))
            request.session['tocopy'] = l
            request.session.flash('Choose where to copy the items:', 'info')
        else:
            request.session.flash('No items to copy')

        return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

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
            return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

        try:
            for oid in tocopy:
                obj = objectmap.object_for(oid)
                obj.__parent__.copy(obj.__name__, context)
        except FolderKeyError as e:
            self.request.session.flash(e.args[0], 'error')
            raise HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

        if len(tocopy) == 1:
            msg = 'Copied 1 item'
            request.sdiapi.flash_with_undo(msg)
        else:
            msg = 'Copied %s items' % len(tocopy)
            request.sdiapi.flash_with_undo(msg)

        return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

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
        tomove = self._modified_items()

        if tomove:
            l = []
            for name in tomove:
                obj = context.get(name)
                if obj is not None:
                    l.append(get_oid(obj))
            request.session['tomove'] = l
            request.session.flash('Choose where to move the items:', 'info')
        else:
            request.session.flash('No items to move')

        return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

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
            return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

        try:
            for oid in tomove:
                obj = objectmap.object_for(oid)
                obj.__parent__.move(obj.__name__, context)
        except FolderKeyError as e:
            self.request.session.flash(e.args[0], 'error')
            raise HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

        if len(tomove) == 1:
            msg = 'Moved 1 item'
            request.sdiapi.flash_with_undo(msg)
        else:
            msg = 'Moved %s items' % len(tomove)
            request.sdiapi.flash_with_undo(msg)

        return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

    @mgmt_view(
        request_method='POST',
        xhr=True,
        renderer='json',
        request_param="ajax.reorder",
        permission='sdi.manage-contents',
        tab_condition=False,
        check_csrf=False
        )
    def reorder_rows(self):
        request = self.request
        context = self.context
        item_modify = request.params.get('item-modify').split('/')
        insert_before = request.params.get('insert-before')
        if not insert_before:
            # '' or None means appending after the last item.
            insert_before = None
        context.reorder(item_modify, insert_before)
        msg = '%i rows moved.' % (len(item_modify), )
        msg = request.sdiapi.get_flash_with_undo_snippet(msg)
        results = {
            'flash': msg,
            }
        # Generate content update as requested by the client.
        results.update(self._get_json())
        return results
