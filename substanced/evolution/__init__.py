import sys

import transaction

from repoze.evolution import (
    IEvolutionManager,
    ZODBEvolutionManager,
    evolve_to_latest,
    )

VERSION = 8
NAME = 'substanced'

def add_evolution_package(config, package_name):
    """ Add a package to the evolution manager.  The package should contain
    evolveN.py scripts which evolve the database (see the ``repoze.evolution``
    package).  Call via ``config.add_evolution_package``."""
    config.registry.registerUtility(
        ZODBEvolutionManager,
        IEvolutionManager, 
        name=package_name
        )

# custom exceptions FBO defining reprs for command-line display

class ConflictingFlags(Exception):
    def __init__(self, flag1, flag2):
        self.flag1 = flag1
        self.flag2 = flag2

    def __repr__(self):
        return 'Conflicting flags: %s cannot be used when %s is used' % (
            self.flag1, self.flag2)

class NoSuchPackage(Exception):
    def __init__(self, pkg_name):
        self.pkg_name = pkg_name

    def __repr__(self):
        return 'No such package named %s' % (self.pkg_name,)

class NoPackageSpecified(Exception):
    def __repr__(self):
        return 'No package specified: %s' % (self.args[0],)

def importer(pkg_name):
    __import__(pkg_name)
    return sys.modules[pkg_name]

def evolve_packages(
    registry,
    root,
    package=None,
    set_db_version=None,
    latest=False,
    mark_all_current=False,
    importer=importer,
    ):
    """ Evolve the package named ``package`` """
    # importer in kwarg list for testing purposes only

    if latest and (set_db_version is not None):
        raise ConflictingFlags('latest', 'set_db_version')

    if mark_all_current and (set_db_version is not None):
        raise ConflictingFlags('mark_all_current', 'set_db_version')

    if set_db_version and not package:
        raise NoPackageSpecified(
            'Not setting db version to %s ' % set_db_version
            )

    managers = list(registry.getUtilitiesFor(IEvolutionManager))

    # XXX temporary hack to make substanced evolution happen before any other
    # evolution (must die if/when we add topological sorting of evolution steps
    # or packages)
    for i, (pkg_name, factory) in enumerate(list(managers)):
        if pkg_name == 'substanced.evolution':
            managers.pop(i)
            managers.insert(0, (pkg_name, factory))
            break

    if package and package not in [x[0] for x in managers]:
        raise NoSuchPackage(package)

    results = []

    for pkg_name, factory in managers:
        if (package is None) or (pkg_name == package):
            
            pkg = importer(pkg_name)

            sw_version = pkg.VERSION

            manager = factory(root, pkg_name, sw_version, 0)

            db_version = manager.get_db_version()

            result = {'package':pkg_name}
            result['sw_version'] = sw_version
            result['db_version'] = db_version

            if set_db_version is None:

                if latest:
                    # does its own commit
                    evolve_to_latest(manager)
                    new_version = manager.get_db_version()
                    result['new_version'] = new_version
                    result['message'] = 'Evolved %s to %s' % (
                        pkg_name, new_version)

                elif mark_all_current:
                    manager._set_db_version(sw_version)
                    transaction.commit()
                    result['new_version'] = sw_version
                    result['message'] = 'Evolved %s to %s' % (
                        pkg_name, sw_version)

                else:
                    result['new_version'] = db_version
                    result['message'] = 'Not evolving (latest not specified)'

            else:

                if set_db_version == db_version:
                    result['new_version'] = db_version
                    result['message'] = 'Nothing to do'

                else:
                    manager._set_db_version(set_db_version)
                    transaction.commit()
                    result['new_version'] = set_db_version
                    result['message'] = (
                        'Database version set to %s' % set_db_version
                        )

            results.append(result)

    return results

def includeme(config): #pragma: no cover
    config.add_directive('add_evolution_package', add_evolution_package)
    config.add_evolution_package('substanced.evolution')
