from pyramid.threadlocal import get_current_request
from pyramid.security import unauthenticated_userid

from substanced.event import subscribe_acl_modified
from substanced.util import get_oid

from . import AuditScribe

@subscribe_acl_modified()
def aclchanged(event):
    request = get_current_request()
    userid = unauthenticated_userid(request)
    eventscribe = AuditScribe(event.object)
    oid = get_oid(event.object)
    old_acl = str(event.old_acl)
    new_acl = str(event.new_acl)
    eventscribe.add(
        'aclchanged',
        oid,
        old_acl=old_acl,
        new_acl=new_acl,
        userid=userid,
        )
