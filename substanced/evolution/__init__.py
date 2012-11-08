import sys

import transaction

from repoze.evolution import (
    IEvolutionManager,
    ZODBEvolutionManager,
    evolve_to_latest,
    )


VERSION = 1
NAME = 'substanced'

def add_evolution_package(config, package_name):
    """ Add a package to the evolution manager.  The package should contain
    eveolveN.py scripts which evolve the database (see the ``repoze.evolution``
    package).  Call via ``config.add_evolution_package``."""
    config.registry.registerUtility(
        ZODBEvolutionManager,
        IEvolutionManager, 
        name=package_name
        )

def evolve_packages(
    registry,
    root,
    pkg_name,
    set_db_version=None,
    latest=False
    ):
    """ Evolve the package named ``pkg_name`` """
    results = []
    managers = list(registry.getUtilitiesFor(IEvolutionManager))

    if latest and (set_db_version is not None):
        # FBO scripts.evolve.main
        raise ValueError(
            'Cannot use both --latest and --set--db-version together'
            )

    if set_db_version and not pkg_name:
        # FBO scripts.evolve.main
        raise ValueError(
            'Not setting db version to %s (specify --package to '
            'specify which package to set the db version for)' %
            set_db_version
            )


    if pkg_name and pkg_name not in [x[0] for x in managers]:
        raise ValueError('No such package "%s"' % pkg_name)

    for pkg_name, factory in managers:
        result = {'package':pkg_name}
        __import__(pkg_name)
        pkg = sys.modules[pkg_name]
        sw_version = pkg.VERSION
        manager = factory(root, pkg_name, sw_version, 0)
        db_version = manager.get_db_version()
        result['sw_version'] = sw_version
        result['db_version'] = db_version

        if set_db_version is None:

            if latest:
                evolve_to_latest(manager)
                new_version = manager.get_db_version()
                result['new_version'] = new_version
                result['message'] = 'Evolved %s to %s' % (pkg_name, new_version)

            else:
                result['new_version'] = db_version
                # FBO scripts.evolve.main
                result['message'] = (
                    'Not evolving (use --latest to do actual evolution)')

        else:

            if set_db_version <= db_version:
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
