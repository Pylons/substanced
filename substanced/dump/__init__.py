import os
import yaml

from zope.interface import Interface

from pyramid.threadlocal import get_current_registry
from pyramid.traversal import resource_path
from pyramid.security import AllPermissionsList, ALL_PERMISSIONS

from substanced.interfaces import IFolder
from substanced.workflow import STATE_ATTR
from substanced.content import get_content_type

from substanced.util import (
    get_created,
    set_created,
    get_oid,
    set_oid,
    get_acl,
    )

RESOURCE_FILENAME = 'resource.yaml'
RESOURCES_DIRNAME = 'resources'

class IDumperFactory(Interface):
    pass

class SDumper(yaml.Dumper):
    pass

class SLoader(yaml.Loader):
    pass

def walk_resources(resource, prefix=None):
    if prefix is None:
        prefix = resource_path(resource)
    yield resource, resource_path(resource)[len(prefix):]
    if IFolder.providedBy(resource):
        for v in resource.values():
            for r, p in walk_resources(v, prefix):
                yield r, p
    # seems pointless to do resource._p_deactivate() here, as resource will be
    # re-woken-up by resource_path

def dump(
    resource,
    directory,
    subresources=True,
    verbose=False,
    dry_run=False,
    registry=None
    ):
    """ Dump a resource to ``directory``. The resource will be represented by
    at least one properties file and other subdirectories.  Sub-resources
    will dumped as subdirectories if ``subresources`` is True."""

    if registry is None:
        registry = get_current_registry()

    stack = [(os.path.abspath(os.path.normpath(directory)), resource)]

    while stack: # breadth-first is easiest
        directory, resource = stack.pop()
        context = ResourceDumpContext(directory, registry, verbose, dry_run)
        context.dump(resource)
        if not subresources:
            break
        if IFolder.providedBy(resource):
            for subresource in resource.values():
                subdirectory = os.path.join(
                    directory,
                    RESOURCES_DIRNAME,
                    subresource.__name__
                    )
                stack.append((subdirectory, subresource))

def load(
    directory,
    parent=None,
    subresources=True,
    verbose=False,
    dry_run=False,
    registry=None
    ):
    """ Load a dump of a resource and return the resource."""

    if registry is None:
        registry = get_current_registry()

    stack = [(os.path.abspath(os.path.normpath(directory)), parent)]

    first = None

    while stack: # breadth-first is easiest
        directory, parent = stack.pop()
        context = ResourceLoadContext(directory, registry, verbose, dry_run)
        resource = context.load(parent)
        if first is None:
            first = resource
        if not subresources:
            break
        subobjects_dir = os.path.join(directory, RESOURCES_DIRNAME)
        if os.path.exists(subobjects_dir):
            for fn in os.listdir(subobjects_dir):
                fullpath = os.path.join(subobjects_dir, fn)
                subresource_fn = os.path.join(fullpath, RESOURCE_FILENAME)
                if os.path.isdir(fullpath) and os.path.exists(subresource_fn):
                    stack.append((fullpath, resource))

    return first
                    
class _FileOperations(object):
    def _get_fullpath(self, filename, subdir=None, makedirs=False):
        if subdir is None:
            prefix = self.directory
        else:
            prefix = os.path.join(self.directory, subdir)

        if makedirs:
            if not os.path.exists(prefix):
                os.makedirs(prefix)

        fullpath = os.path.join(prefix, filename)
        return fullpath
        
    def openfile_w(self, filename, mode='w', subdir=None, makedirs=True):
        path = self._get_fullpath(filename, subdir=subdir, makedirs=makedirs)
        fp = open(path, mode)
        return fp

    def openfile_r(self, filename, mode='r', subdir=None):
        path = self._get_fullpath(filename, subdir=subdir)
        fp = open(path, mode)
        return fp

    def exists(self, filename, subdir=None):
        path = self._get_fullpath(filename, subdir=subdir)
        return os.path.exists(path)

class _YAMLOperations(_FileOperations):

    yaml_loader = SLoader
    yaml_dumper = SDumper
    
    def load_yaml(self, filename, subdir=None):
        with self.openfile_r(filename, subdir=subdir) as fp:
            return yaml.load(fp, Loader=self.yaml_loader)

    def dump_yaml(self, obj, filename, subdir=None):
        with self.openfile_w(filename, subdir=subdir) as fp:
            return yaml.dump(obj, fp, Dumper=self.yaml_dumper)

class ResourceContext(object):
    def get_dumpers(self):
        ACLDumper.at_registration()
        return [
            ('acl', ACLDumper),
            ('workflow', WorkflowDumper)
            ]
        #return self.registry.getUtilitiesFor(IDumperFactory)

class ResourceDumpContext(ResourceContext, _YAMLOperations):
    def __init__(self, directory, registry, verbose, dry_run):
        self.directory = directory
        self.registry = registry
        self.verbose = verbose
        self.dry_run = dry_run

    def dump_resource(self, resource):
        registry = self.registry
        ct = get_content_type(resource, registry)
        created = get_created(resource)
        data = {
            'content_type':ct,
            'name':resource.__name__,
            'oid':get_oid(resource),
            'created':created,
            'is_service':bool(getattr(resource, '__is_service__', False)),
            }
        self.dump_yaml(data, RESOURCE_FILENAME)

    def dump(self, resource):
        self.dump_resource(resource)
        for factory_name, factory in self.get_dumpers():
            dumper = factory(self, factory_name)
            dumper.dump(resource)

class ResourceLoadContext(ResourceContext, _YAMLOperations):
    def __init__(self, directory, registry, verbose, dry_run):
        self.directory = directory
        self.registry = registry
        self.verbose = verbose
        self.dry_run = dry_run

    def load_resource(self):
        registry = self.registry
        data = self.load_yaml(RESOURCE_FILENAME)
        resource = registry.content.create(data['content_type'])
        name = resource.__name__ = data['name']
        set_oid(resource, data['oid'])
        created = data['created']
        is_service = data['is_service']
        if created is not None:
            set_created(resource, created)
        if is_service:
            resource.__is_service__ = True
        return name, resource

    def load(self, parent):
        name, resource = self.load_resource()
        for factory_name, factory in self.get_dumpers():
            dumper = factory(self, factory_name)
            dumper.load(resource)
        if parent is not None:
            parent.replace(name, resource, registry=self.registry)
        return resource

class ACLDumper(object):
    def __init__(self, context, name):
        self.context = context
        self.name = name
        self.fn = '%s.yaml' % self.name

    @classmethod
    def at_registration(cls):
        cls.yaml_loader.add_constructor(
            AllPermissionsList,
            lambda *arg: ALL_PERMISSIONS
            )

    def dump(self, resource):
        acl = get_acl(resource)
        if acl is None:
            return
        self.context.dump_yaml(acl, self.fn)

    def load(self, resource):
        if self.context.exists(self.fn):
            acl = self.context.load_yaml(self.fn)
            resource.__acl__ = acl
        
class WorkflowDumper(object):
    def __init__(self, context, name):
        self.context = context
        self.name = name
        self.fn = '%s.yaml' % self.name

    def dump(self, resource):
        if hasattr(resource, STATE_ATTR):
            self.context.dump_yaml(getattr(resource, STATE_ATTR), self.fn)

    def load(self, resource):
        if self.context.exists(self.fn):
            states = self.context.load_yaml(self.fn)
            setattr(resource, STATE_ATTR, states)

