import colander
import deform_bootstrap.widget
import deform.widget

from hypatia.interfaces import IIndex

from pyramid.httpexceptions import HTTPFound

from pyramid.view import view_defaults

from ..interfaces import ICatalog

from ..content import find_service
from ..sdi import mgmt_view
from ..form import FormView
from ..schema import Schema
from ..util import oid_of

from . import logger

@mgmt_view(
    content_type='Services',
    name='add_catalog_service',
    tab_condition=False,
    permission='sdi.add-services',
    )
def add_catalog_service(context, request):
    catalog = request.registry.content.create('Catalog')
    context['catalog'] = catalog
    return HTTPFound(location=request.mgmt_path(context))

@view_defaults(
    name='manage_catalog',
    context=ICatalog,
    renderer='templates/manage_catalog.pt',
    permission='sdi.manage-catalog')
class ManageCatalog(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def redir_location(self):
        return self.request.mgmt_path(self.context, '@@manage_catalog')
        
    @mgmt_view(request_method='GET', tab_title='Manage')
    def view(self):
        cataloglen = len(self.context.objectids)
        return dict(cataloglen=cataloglen)

    @mgmt_view(request_method='POST', request_param='reindex', check_csrf=True)
    def reindex(self):
        self.context.reindex()
        self.request.session.flash('Catalog reindexed')
        return HTTPFound(location=self.redir_location)

@view_defaults(
    name='manage_index',
    context=IIndex,
    renderer='templates/manage_index.pt',
    permission='sdi.manage-catalog')
class ManageIndex(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def redir_location(self):
        return self.request.mgmt_path(self.context, '@@manage_index')

    @mgmt_view(request_method='GET', tab_title='Manage')
    def view(self):
        index = self.context
        indexed = index.indexed_count()
        not_indexed = index.not_indexed_count()
        index_name = index.__name__
        return dict(
            indexed=indexed,
            not_indexed=not_indexed,
            index_name=index_name,
            index_type = index.__class__.__name__,
            )

    @mgmt_view(request_method='POST', request_param='reindex', check_csrf=True)
    def reindex(self):
        index_name = self.context.__name__
        catalog  = self.context.__parent__
        if ICatalog.providedBy(catalog):
            catalog.reindex(indexes=[index_name])
            self.request.session.flash('Index "%s" reindexed' % index_name)
        else:
            self.request.session.flash(
                'Cannot reindex an index unless it is contained in a catalog',
                'error'
                )
        return HTTPFound(location=self.redir_location)

@colander.deferred
def principals_widget(node, kw):
    request = kw['request']
    principals = find_service(request.context, 'principals')
    groups = [(str(oid_of(group)), name) for name, group in 
              principals['groups'].items()]
    users = [(str(oid_of(user)), name) for name, user in 
              principals['users'].items()]
    values = (
        {'label':'Groups', 'values':groups}, 
        {'label':'Users', 'values':users},
        )
    widget = deform_bootstrap.widget.ChosenOptGroupWidget(values=values)
    return widget

class Principals(colander.SequenceSchema):
    principal = colander.SchemaNode(
        colander.Int(),
        missing=colander.null,
        widget = principals_widget,
        )

class Permitted(Schema):
    permission = colander.SchemaNode(
        colander.String(),
        missing='',
        )
    principals = Principals(missing=colander.null)

class SearchSchema(Schema):
    cqe_expression = colander.SchemaNode(
        colander.String(),
        widget = deform.widget.TextAreaWidget(rows=10, cols=120),
        title='CQE Expression',
        )
    permitted = Permitted(title='Principals and Permission Filter')

@mgmt_view(context=ICatalog, name='search_catalog', 
           permission='sdi.manage-catalog', 
           renderer='templates/searchform.pt', tab_title='Search')
class SearchCatalogView(FormView):
    schema = SearchSchema(title='Expression')
    buttons = ('search',)
    catalog_results = None
    logger = logger

    def search_success(self, appstruct):
        """ Accept a CQE expression and a permitted value and return a 
        sequence of object renderings """
        self.request.session['catalogsearch.appstruct'] = appstruct
        context = self.context
        return HTTPFound(
            location=self.request.mgmt_path(context, '@@search_catalog')
            )

    def show(self, form):
        appstruct = self.request.session.pop('catalogsearch.appstruct',
                                             colander.null)
        searchresults = ()
        if appstruct:
            permitted = appstruct['permitted']
            permission = permitted['permission']
            principals = permitted['principals']
            if not permission:
                permitted = None
            else:
                permitted = principals, permission
            expr = appstruct['cqe_expression']
            try:
                n, oids, res = self.request.query_catalog(
                    expr, permitted=permitted)
            except Exception as e:
                self.logger.exception('During search')
                cls_name = e.__class__.__name__
                msg = 'Query failed (%s: %s)' % (cls_name, e.args[0])
                self.request.session.flash(msg, 'error')
            else:
                searchresults = list([(x, res(x)) for x in oids])
                if not searchresults:
                    searchresults = [('', 'No results')]
                self.request.session.flash('Query succeeded', 'success')
        return {
            'searchresults':searchresults,
            'form':form.render(appstruct=appstruct),
            }
        
