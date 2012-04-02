import transaction
from pyramid_zodbconn import get_connection

def make_root_factory(cls, *arg, **kw):
    def root_factory(
            request,
            transaction=transaction,
            get_connection=get_connection,
            ): # transaction and get_connection for testing
        conn = get_connection(request)
        zodb_root = conn.root()
        if not 'app_root' in zodb_root:
            app_root = cls(*arg, **kw)
            zodb_root['app_root'] = app_root
            transaction.commit()
        return zodb_root['app_root']
    return root_factory
