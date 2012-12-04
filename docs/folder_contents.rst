===========================
Configuring Folder Contents
===========================

The folder contents, as mentioned previously in
:ref:`sdi-folder-contents`, the SDI's folder contents uses a powerful
datagrid to view and manage items in a folder. This chapter covers how
your content types can plug into the folder contents view.

Adding Columns
==============

Perhaps your system has content types with extra attributes that are
meaningful and you'd like your contents listings to show that column.
You can change the columns available on folder contents listings by
passing in a ``columns`` argument to the ``@content`` directive. The
value of this argument is a callable which returns a sequence of
mappings conforming to the datagrid's contract. For example:

.. code-block:: python

    def binder_columns(folder, subobject, request, default_columnspec):
        subobject_name = getattr(subobject, '__name__', str(subobject))
        objectmap = find_objectmap(folder)
        user_oid = getattr(subobject, '__creator__', None)
        created = getattr(subobject, '__created__', None)
        modified = getattr(subobject, '__modified__', None)
        if user_oid is not None:
            user = objectmap.object_for(user_oid)
            user_name = getattr(user, '__name__', 'anonymous')
        else:
            user_name = 'anonymous'
        if created is not None:
            created = created.isoformat()
        if modified is not None:
            modified = modified.isoformat()
        return default_columnspec + [
            {'name': 'Title',
            'field': 'title',
            'value': getattr(subobject, 'title', subobject_name),
            'sortable': True,
            'formatter': 'icon_label_url',
            },
            {'name': 'Created',
            'field': 'created',
            'value': created,
            'sortable': True,
            'formatter': 'date',
            },
            {'name': 'Last edited',
            'field': 'modified',
            'value': modified,
            'sortable': True,
            'formatter': 'date',
            },
            {'name': 'Creator',
            'field': 'creator',
            'value': user_name,
            'sortable': True,
            }
            ]

    @content(
        'Binder',
        icon='icon-book',
        add_view='add_binder',
        propertysheets = (
            ('Basic', BinderPropertySheet),
            ),
        columns=binder_columns,
        catalog=True,
        )

The callable is passed the folder, a subobject, the ``request``,
and a set of default column specifications. To display the datagrid
column headers, your callable is invoked on the first resource.
Later, this callable is used to get the value for the fields of each
column for each resource in a request's batch.

The mappings returned can indicate whether a particular column should
be sortable. In general, it is better if your sortable columns are
hooked up to a catalog index, in case the folder contains a large set
of resources.

Buttons
=======

As we just showed, you can extend the folder contents with extra
columns to display and possibly sort on. You can also add new buttons
that will trigger operations on selected resources.

As with columns, we pass a new argument to the ``@content`` directive.
For example, the folder contents view for the catalogs folder allows you
to reindex multiple indexes at once:

.. image:: images/catalog_contents.png

The ``Reindex`` button illustrates a useful facility for performing
many custom operations at once.

The :py:mod:`substanced.catalog` module's ``@content`` directive has a
``buttons`` argument:

.. code-block:: python

    @content(
        'Catalog',
        icon='icon-search',
        service_name='catalog',
        buttons=catalog_buttons,
        )

This points at a callable:

.. code-block:: python

    def catalog_buttons(context, request, default_buttons):
        """ Show a reindex button before default buttons in the folder contents
        view of a catalog"""
        buttons = [
            {'type':'single',
             'buttons':
             [
                 {'id':'reindex',
                  'name':'form.reindex',
                  'class':'btn-primary btn-sdi-sel',
                  'value':'reindex',
                  'text':'Reindex'}
                 ]
             }
            ] + default_buttons
        return buttons

In this case, the ``Reindex`` button was inserted before the other
buttons, in the place where an add button would normally appear.

The ``class`` on your buttons affect behavior in the datagrid:

- ``btn-primary`` gives this button the styling for the primary button
  of a form, using Twitter Bootstrap form styling

- ``btn-sdi-act`` makes the button always enabled

- ``btn-sdi-sel`` disables the button until one or more items are
  selected

- ``btn-sdi-del`` disables the button if any of the selected resources
  is marked as "non-deletable" (discussed below)

When clicked, this button will do a form ``POST`` of the selected
docids to a view that you have implemented. Which view? The
``'name': 'form.reindex'`` item sets the parameter on the POST. You can
then register a view against this.
:py:mod:`substanced.sdi.views.catalog` shows this:

.. code-block:: python

    @mgmt_view(
        context=IFolder,
        content_type='Catalog',
        name='contents',
        request_param='form.reindex',
        request_method='POST',
        renderer='substanced.sdi:templates/contents.pt',
        permission='sdi.manage-contents',
        tab_condition=False,
        )
    def reindex_indexes(context, request):
        toreindex = request.POST.getall('item-modify')
        if toreindex:
            context.reindex(indexes=toreindex, registry=request.registry)
            request.session.flash(
                'Reindex of selected indexes succeeded',
                'success'
                )
        else:
            request.session.flash(
                'No indexes selected to reindex',
                'error'
                )

        return HTTPFound(request.sdiapi.mgmt_path(context, '@@contents'))

Selection and Button Enabling
=============================

As mentioned above, some buttons are driven by the selection. If
nothing is selected, the button is disabled.

Buttons can also be disabled if any selected item is "non-deletable".
How does that get signified? An item is 'deletable' if the user has
the ``sdi.manage-contents`` permission on ``folder`` *and* if the
subobject has a ``__sdi_deletable__`` attribute which resolves to a
boolean ``True`` value.