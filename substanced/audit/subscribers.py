from pyramid.threadlocal import get_current_request
from pyramid.traversal import resource_path

from substanced.event import (
    subscribe_acl_modified,
    subscribe_will_be_removed,
    subscribe_added,
    subscribe_modified,
    )

from substanced.util import (
    get_oid,
    postorder,
    acquire,
    )

from . import AuditScribe

def _get_userinfo():
    request = get_current_request()
    user = getattr(request, 'user', None)
    userid = get_oid(user, None)
    username = getattr(user, '__name__', None)
    return {'oid':userid, 'name':username}

def _get_scribe(context):
    auditlog = acquire(context, '__auditlog__', None)
    if auditlog is not None:
        return AuditScribe(context)

def _add_record(event_name, event, objects):
    scribe = _get_scribe(event.parent)
    if scribe is None:
        return
    userinfo = _get_userinfo()
    object_name = event.name
    for obj in objects:
        content_type = str(event.registry.content.typeof(obj))
        parent = obj.__parent__
        folder_path = resource_path(parent)
        folder_oid = get_oid(parent, None)
        object_oid = get_oid(obj, None)
        scribe.add(
            event_name,
            folder_oid, # this is an event related to the *container*
            object_oid=object_oid,
            folder_oid=folder_oid,
            folder_path=folder_path,
            object_name=object_name,
            content_type=content_type,
            userinfo=userinfo,
            )

@subscribe_acl_modified()
def acl_modified(event):
    """ Generates ACLModified audit events """
    scribe = _get_scribe(event.object)
    if scribe is None:
        return
    userinfo = _get_userinfo()
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
def content_added_moved_or_duplicated(event):
    """ Generates ContentAdded (and ContentMoved/ContentDuplicated)
    audit events """
    if event.moving is not None:
        return _add_record('ContentMoved', event, [event.object])
    elif event.duplicating is not None:
        return _add_record('ContentDuplicated', event, [event.object])
    else:
        return _add_record('ContentAdded', event, postorder(event.object))

@subscribe_will_be_removed()
def content_removed(event):
    """ Generates ContentRemoved audit events """
    if event.moving is not None:
        return # content_moved action is is handled by content_added_moved...
    return _add_record('ContentRemoved', event, [event.object])

@subscribe_modified()
def content_modified(event):
    scribe = _get_scribe(event.object)
    if scribe is None:
        return
    userinfo = _get_userinfo()
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
