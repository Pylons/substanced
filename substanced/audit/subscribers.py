from pyramid.threadlocal import get_current_request
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
    subscribe_content_indexed,
    subscribe_content_unindexed,
    )

from substanced.util import get_oid

from . import AuditScribe

def get_userinfo():
    request = get_current_request()
    user = getattr(request, 'user', None)
    userid = get_oid(user, None)
    username = getattr(user, '__name__', None)
    return {'oid':userid, 'name':username}

@subscribe_acl_modified()
def acl_modified(event):
    """ Generates ACLModified audit events """
    userinfo = get_userinfo()
    scribe = AuditScribe(event.object)
    oid = get_oid(event.object, None)
    old_acl = str(event.old_acl)
    new_acl = str(event.new_acl)
    path = resource_path(event.object)
    content_type = str(event.registry.content.typeof(event.object))
    scribe.add(
        'ACLModified',
        oid,
        object_path=path,
        old_acl=old_acl,
        new_acl=new_acl,
        userinfo=userinfo,
        content_type=content_type,
        )

@subscribe_added()
@subscribe_will_be_removed()
def content_added_or_removed(event):
    """ Generates ContentAdded and ContentRemoved audit events """
    if IObjectWillBeRemoved.providedBy(event):
        name = 'ContentRemoved'
    elif IObjectAdded.providedBy(event):
        name = 'ContentAdded'
    else:
        return False # for testing
    userinfo = get_userinfo()
    scribe = AuditScribe(event.object)
    parent = event.parent
    # this is an event related to the *container*, not to the object.
    oid = get_oid(parent, None)
    object_oid = get_oid(event.object, None)
    folder_path = resource_path(parent)
    object_name = event.name
    moving = bool(event.moving)
    loading = bool(event.loading)
    content_type = str(event.registry.content.typeof(event.object))
    scribe.add(
        name,
        oid,
        object_oid=object_oid,
        folder_oid=oid,
        folder_path=folder_path,
        object_name=object_name,
        content_type=content_type,
        userinfo=userinfo,
        moving=moving,
        loading=loading,
        )

@subscribe_modified()
def content_modified(event):
    userinfo = get_userinfo()
    scribe = AuditScribe(event.object)
    oid = get_oid(event.object, None)
    object_path = resource_path(event.object)
    content_type = str(event.registry.content.typeof(event.object))
    scribe.add(
        'ContentModified',
        oid,
        object_oid=oid,
        object_path=object_path,
        content_type=content_type,
        userinfo=userinfo,
        )

@subscribe_content_indexed()
def content_indexed(event):
    userinfo = get_userinfo()
    scribe = AuditScribe(event.object)
    object_oid = get_oid(event.object, None)
    catalog_path = resource_path(event.catalog)
    object_path = resource_path(event.object)
    catalog_oid = get_oid(event.catalog, None)
    scribe.add(
        'ContentIndexed',
        object_oid,
        catalog_oid=catalog_oid,
        catalog_path=catalog_path,
        object_path=object_path,
        object_oid=object_oid,
        userinfo=userinfo,
        )
    
@subscribe_content_unindexed()
def content_unindexed(event):
    userinfo = get_userinfo()
    scribe = AuditScribe(event.object)
    object_oid = event.oid
    catalog_path = resource_path(event.catalog)
    catalog_oid = get_oid(event.catalog, None)
    scribe.add(
        'ContentUnindexed',
        object_oid,
        catalog_oid=catalog_oid,
        catalog_path=catalog_path,
        object_oid=event.oid,
        userinfo=userinfo,
        )
    
