""" Run database evolution steps  """

import getopt
import sys

from pyramid.paster import (
    setup_logging,
    bootstrap,
    )

from substanced.evolution import evolve_packages

def _print(msg):
    sys.stdout.write('%s\n' % msg)

def usage(e=None):
    if e is not None:
        _print(e)
        _print('')
    _print("""\
sd_evolve [--latest] [--set-db-version=num] [--package=name] config_uri
  Evolves new database with changes from scripts in evolve packages
     - with no arguments, evolve just displays versions
     - with the --latest argument, evolve runs scripts as necessary
     - if --package is specified, only operate against the specified
       package name.
     - with the --set-db-version argument, evolve runs no scripts
       but just sets the database 'version number' for a package
       to an arbitrary integer number.  Requires --package.

e.g. sd_evolve --latest etc/development.ini""")
    sys.exit(2)

def main(argv=sys.argv):
    name, argv = argv[0], argv[1:]
    latest = False
    set_db_version = None
    package = None

    try:
        opts, args = getopt.getopt(argv, 'l?hs:p:',
                                         ['latest',
                                          'package=',
                                          'set-db-version=',
                                          'help',
                                         ])
    except getopt.GetoptError as e:
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
                set_db_version = int(v)
                if set_db_version < 0:
                    raise Exception
            except:
                usage('Bad version number %s' % v)

    setup_logging(config_uri)
    env = bootstrap(config_uri)
    root = env['root']
    registry = env['registry']

    try:
        results = evolve_packages(
            registry,
            root,
            package=package,
            set_db_version=set_db_version,
            latest=latest,
            )
    except Exception as e:
        usage(repr(e))

    for result in results:
        _print('Package %(package)s' % result)
        _print('Code at software version %(sw_version)s' % result)
        _print('Database at version %(db_version)s' % result)
        _print(result['message'])
        _print('')

if __name__ == '__main__':
    main()
