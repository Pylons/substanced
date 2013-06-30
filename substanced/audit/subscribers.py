from pyramid.threadlocal import get_current_request
from pyramid.security import unauthenticated_userid
from pyramid.traversal import resource_path

from substanced.interfaces import (
    IObjectWillBeRemoved,
    IObjectAdded,
    )

from substanced.event import (
    subscribe_acl_modified,
    subscribe_will_be_removed,
    subscribe_added,
    subscribe_modified,
    )

from substanced.util import get_oid

from . import AuditScribe

@subscribe_acl_modified()
def acl_modified(event):
    """ Generates ACLModified audit events """
    request = get_current_request()
    userid = unauthenticated_userid(request)
    eventscribe = AuditScribe(event.object)
    oid = get_oid(event.object)
    old_acl = str(event.old_acl)
    new_acl = str(event.new_acl)
    path = resource_path(event.object)
    eventscribe.add(
        'ACLModified',
        oid,
        object_path=path,
        old_acl=old_acl,
        new_acl=new_acl,
        userid=userid,
        )

@subscribe_added()
@subscribe_will_be_removed()
def content_addded_or_removed(event):
    """ Generates ContentAdded and ContentRemoved audit events """
    if IObjectWillBeRemoved.providedBy(event):
        name = 'ContentRemoved'
    elif IObjectAdded.providedBy(event):
        name = 'ContentAdded'
    else:
        return
    request = get_current_request()
    userid = unauthenticated_userid(request)
    eventscribe = AuditScribe(event.object)
    oid = get_oid(event.object)
    parent = event.parent
    parent_oid = get_oid(parent, None)
    parent_path = resource_path(parent)
    object_name = event.name
    moving = bool(event.moving)
    loading = bool(event.loading)
    eventscribe.add(
        name,
        oid,
        userid=userid,
        object_oid=oid,
        parent_oid=parent_oid,
        parent_path=parent_path,
        object_name=object_name,
        moving=moving,
        loading=loading,
        )

@subscribe_modified()
def content_modified(event):
    request = get_current_request()
    userid = unauthenticated_userid(request)
    eventscribe = AuditScribe(event.object)
    oid = get_oid(event.object)
    object_path = resource_path(event.object)
    eventscribe.add(
        'ContentModified',
        oid,
        userid=userid,
        object_oid=oid,
        object_path=object_path,
        )
