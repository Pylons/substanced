import os
import yaml

from zope.interface import (
    Interface,
    directlyProvidedBy,
    alsoProvides,
    )

from pyramid.threadlocal import get_current_registry
from pyramid.security import AllPermissionsList, ALL_PERMISSIONS
from pyramid.util import DottedNameResolver

from substanced.interfaces import IFolder
from substanced.workflow import STATE_ATTR
from substanced.content import get_content_type
from substanced.objectmap import find_objectmap

from substanced.util import (
    get_created,
    set_created,
    get_oid,
    set_oid,
    get_acl,
    dotted_name,
    )

RESOURCE_FILENAME = 'resource.yaml'
RESOURCES_DIRNAME = 'resources'

class IDumperFactory(Interface):
    pass

# grrr.. pyyaml has class-based global registries, so we need to subclass
# to provide them

class SDumper(yaml.Dumper):
    pass

class SLoader(yaml.Loader):
    pass

def set_yaml(registry):
    registry.yaml_loader = SLoader
    registry.yaml_dumper = SDumper

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

    set_yaml(registry)

    # dumpers = [f(n, registry) for nm f in self.registry.getUtilitiesFor(IDumperFactory)]
    dumpers = [ f(n, registry) for n, f in DUMPERS]

    stack = [(os.path.abspath(os.path.normpath(directory)), resource)]
    first = None

    while stack: # breadth-first is easiest

        directory, resource = stack.pop()

        if first is None:
            first = resource

        context = ResourceDumpContext(
            directory,
            registry,
            dumpers,
            verbose,
            dry_run
            )

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

    callbacks = registry.__dict__.pop('dumper_callbacks', ())

    for callback in callbacks:
        callback(first)

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

    set_yaml(registry)

    stack = [(os.path.abspath(os.path.normpath(directory)), parent)]

    first = None

    # dumpers = [f(n, registry) for nm f in self.registry.getUtilitiesFor(IDumperFactory)]
    dumpers = [ f(n, registry) for n, f in DUMPERS]

    while stack: # breadth-first is easiest

        directory, parent = stack.pop()

        context = ResourceLoadContext(
            directory,
            registry,
            dumpers,
            verbose,
            dry_run
            )

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

    callbacks = registry.__dict__.pop('loader_callbacks', ())
    for callback in callbacks:
        callback(first)

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

    def load_yaml(self, filename, subdir=None):
        with self.openfile_r(filename, subdir=subdir) as fp:
            return yaml.load(fp, Loader=self.registry.yaml_loader)

    def dump_yaml(self, obj, filename, subdir=None):
        with self.openfile_w(filename, subdir=subdir) as fp:
            return yaml.dump(obj, fp, Dumper=self.registry.yaml_dumper)

class ResourceContext(_YAMLOperations):
    dotted_name_resolver = DottedNameResolver()
    
    def resolve_dotted_name(self, dotted):
        return self.dotted_name_resolver.resolve(dotted)

    def dotted_name(self, object):
        return dotted_name(object)

class ResourceDumpContext(ResourceContext):
    def __init__(self, directory, registry, dumpers, verbose, dry_run):
        self.directory = directory
        self.registry = registry
        self.dumpers = dumpers
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
        self.resource = resource
        self.dump_resource(resource)
        for dumper in self.dumpers:
            dumper.dump(self)

    def add_callback(self, callback):
        dumper_callbacks = getattr(self.registry, 'dumper_callbacks', [])
        dumper_callbacks.append(callback)
        self.registry.dumper_callbacks = dumper_callbacks

class ResourceLoadContext(ResourceContext):
    def __init__(self, directory, registry, loaders, verbose, dry_run):
        self.directory = directory
        self.registry = registry
        self.loaders = loaders
        self.verbose = verbose
        self.dry_run = dry_run

    def _load_resource(self):
        registry = self.registry
        data = self.load_yaml(RESOURCE_FILENAME)
        name = data['name']
        oid = data['oid']
        created = data['created']
        is_service = data['is_service']
        resource = registry.content.create(data['content_type'], __oid=oid)
        resource.__name__ = name
        set_oid(resource, oid)
        if created is not None:
            set_created(resource, created)
        if is_service:
            resource.__is_service__ = True
        return name, resource

    def load(self, parent):
        name, resource = self._load_resource()
        self.name = name
        self.resource = resource
        for loader in self.loaders:
            loader.load(self)
        if parent is not None:
            parent.replace(name, resource, registry=self.registry)
        return resource

    def add_callback(self, callback):
        loader_callbacks = getattr(self.registry, 'loader_callbacks', [])
        loader_callbacks.append(callback)
        self.registry.loader_callbacks = loader_callbacks

class ACLDumper(object):
    def __init__(self, name, registry):
        self.name = name
        self.registry = registry
        self.fn = '%s.yaml' % self.name
        def ap_constructor(loader, node):
            return ALL_PERMISSIONS
        def ap_representer(dumper, data):
            return dumper.represent_scalar(u'!all_permissions', '')
        registry.yaml_loader.add_constructor(
            u'!all_permissions',
            ap_constructor,
            )
        registry.yaml_dumper.add_representer(
            AllPermissionsList,
            ap_representer,
            )

    def dump(self, context):
        acl = get_acl(context.resource)
        if acl is None:
            return
        context.dump_yaml(acl, self.fn)

    def load(self, context):
        if context.exists(self.fn):
            acl = context.load_yaml(self.fn)
            context.resource.__acl__ = acl
        
class WorkflowDumper(object):
    def __init__(self, name, registry):
        self.name = name
        self.registry = registry
        self.fn = '%s.yaml' % self.name

    def dump(self, context):
        resource = context.resource
        if hasattr(resource, STATE_ATTR):
            self.context.dump_yaml(getattr(resource, STATE_ATTR), self.fn)

    def load(self, context):
        if context.exists(self.fn):
            states = context.load_yaml(self.fn)
            setattr(context.resource, STATE_ATTR, states)

class ReferencesDumper(object):
    def __init__(self, name, registry):
        self.name = name
        self.registry = registry
        self.fn = '%s.yaml' % self.name

    def dump(self, context):
        resource = context.resource
        objectmap = find_objectmap(resource)
        references = {}
        if objectmap is not None:
            if objectmap.has_references(resource):
                for reftype in objectmap.get_reftypes():
                    dotted = context.dotted_name(reftype)
                    sourceids = list(objectmap.sourceids(resource, reftype))
                    targetids = list(objectmap.targetids(resource, reftype))
                    if sourceids:
                        d = references.setdefault(dotted, {})
                        d['sources'] = sourceids
                    if targetids:
                        d = references.setdefault(dotted, {})
                        d['targets'] = targetids
        if references:
            context.dump_yaml(references, self.fn)

    def load(self, context):
        if context.exists(self.fn):
            references = context.load_yaml(self.fn)
            resource = context.resource
            oid = get_oid(resource)
            def add_references(root):
                for dotted, d in references.items():
                    reftype = context.resolve_dotted_name(dotted)
                    targets = d.get('targets', ())
                    sources = d.get('sources', ())
                    objectmap = find_objectmap(root)
                    if objectmap is not None:
                        for target in targets:
                            objectmap.connect(oid, target, reftype)
                        for source in sources:
                            objectmap.connect(source, oid, reftype)
            context.add_callback(add_references)
    
class SDIPropertiesDumper(object):
    def __init__(self, name, registry):
        self.name = name
        self.registry = registry
        self.fn = '%s.yaml' % self.name

    def dump(self, context):
        # __sdi_deletable__
        # __sdi_hidden__
        # __sdi_addable__
        resource = context.resource
        resource._p_activate()
        d = resource.__dict__
        properties = {}
        deletable = d.get('__sdi_deletable__')
        hidden = d.get('__sdi_hidden__')
        addable = d.get('__sdi_addable__')
        if deletable is not None:
            properties['__sdi_deletable__'] = deletable
        if hidden is not None:
            properties['__sdi_hidden__'] = hidden
        if addable is not None:
            properties['__sdi_addable__'] = addable
        if properties:
            context.dump_yaml(properties, self.fn)

    def load(self, context):
        resource = context.resource
        if context.exists(self.fn):
            properties = context.load_yaml(self.fn)
            resource._p_activate()
            resource.__dict__.update(properties)
            resource._p_changed = True
            
class DirectlyProvidedInterfacesDumper(object):
    def __init__(self, name, registry):
        self.name = name
        self.registry = registry
        self.fn = '%s.yaml' % self.name

    def dump(self, context):
        resource = context.resource
        ifaces = list(directlyProvidedBy(resource).interfaces())
        if ifaces:
            dotted_names = [ context.dotted_name(i) for i in ifaces ]
            context.dump_yaml(dotted_names, self.fn)

    def load(self, context):
        if context.exists(self.fn):
            dotted_names = context.load_yaml(self.fn)
            for name in dotted_names:
                iface = context.resolve_dotted_name(name)
                alsoProvides(context.resource, iface)

DUMPERS = [
    ('acl', ACLDumper),
    ('workflow', WorkflowDumper),
    ('references', ReferencesDumper),
    ('sdiproperties', SDIPropertiesDumper),
    ('interfaces', DirectlyProvidedInterfacesDumper),
    ]
