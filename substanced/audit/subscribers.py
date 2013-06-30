from substanced.event import subscribe_acl_modified
from substanced.util import get_oid

from . import AuditScribe

@subscribe_acl_modified()
def aclchanged(event):
    eventscribe = AuditScribe(event.object)
    oid = get_oid(event.object)
    old_acl = str(event.old_acl)
    new_acl = str(event.new_acl)
    eventscribe.add('aclchanged', oid, old_acl=old_acl, new_acl=new_acl)
