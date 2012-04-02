""" Run database evolution steps  """

import getopt
import sys

from pyramid.paster import (
    setup_logging,
    bootstrap,
    )

from repoze.evolution import IEvolutionManager
from repoze.evolution import evolve_to_latest

def usage(e=None):
    if e is not None:
        print e
    print "evolve [--latest] [--set-db-version=num] [--package=name] config_uri"
    print "  Evolves new database with changes from scripts in evolve packages"
    print "     - with no arguments, evolve just displays versions"
    print "     - with the --latest argument, evolve runs scripts as necessary"
    print "     - if --package is specified, only operate against the specified"
    print "       package name."
    print "     - with the --set-db-version argument, evolve runs no scripts"
    print "       but just sets the database 'version number' for a package "
    print "       to an arbitrary integer number.  Requires --package."
    print
    print "e.g. sd_evolve --latest etc/development.ini"
    sys.exit(2)

def main(argv=sys.argv):
    name, argv = argv[0], argv[1:]
    latest = False
    set_version = None
    package = None

    try:
        opts, args = getopt.getopt(argv, 'l?hs:p:',
                                         ['latest',
                                          'package=',
                                          'set-db-version=',
                                          'help',
                                         ])
    except getopt.GetoptError, e:
        usage(e)

    if args:
        config_uri = args[0]
    else:
        usage('Requires a config_uri as an argument')

    for k, v in opts:
        if k in ('-l', '--latest'):
            latest = True
        if k in ('-h', '-?', '--help'):
            usage()
        if k in ('-p,' '--package'):
            package = v
        if k in ('-s', '--set-db-version'):
            try:
                set_version = int(v)
                if set_version < 0:
                    raise Exception
            except:
                usage('Bad version number %s' % v)

    if latest and (set_version is not None):
        usage('Cannot use both --latest and --set-version together')

    if set_version and not package:
        usage('Not setting db version to %s (specify --package to '
              'specify which package to set the db version for)' % set_version)

    setup_logging(config_uri)
    env = bootstrap(config_uri)
    root = env['root']
    registry = env['registry']
    managers = registry.getUtilitiesFor(IEvolutionManager)

    if package and package not in [x[0] for x in managers]:
        usage('No such package "%s"' % package)

    for pkg_name, factory in managers:
        if (package is None) or (pkg_name == package):
            __import__(pkg_name)
            pkg = sys.modules[pkg_name]
            VERSION = pkg.VERSION
            print 'Package %s' % pkg_name
            manager = factory(root, pkg_name, VERSION, 0)
            db_version = manager.get_db_version()
            print 'Code at software version %s' % VERSION
            print 'Database at version %s' % db_version
            if set_version is not None:
                manager._set_db_version(set_version)
                manager.transaction.commit()
                print 'Database version set to %s' % set_version
            else:
                if VERSION <= db_version:
                    print 'Nothing to do'
                elif latest:
                    evolve_to_latest(manager)
                    ver = manager.get_db_version()
                    print 'Evolved %s to %s' % (pkg_name, ver)
                else:
                    print 'Not evolving (use --latest to do actual evolution)'
            print ''

if __name__ == '__main__':
    main()
