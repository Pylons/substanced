"""Add an admin user.
"""

from optparse import OptionParser
import sys

from pyramid.paster import (
    setup_logging,
    bootstrap,
    )
import transaction

def main():
    parser = OptionParser(description=__doc__,
                          usage="%prog <config_uri> <username> <password>",
                         )

    options, args = parser.parse_args()

    try:
        config_uri, username, password = args
    except:
        parser.print_usage()
        sys.exit(1)

    setup_logging(config_uri)
    env = bootstrap(config_uri)
    site = env['root']

    principals = env['root']['principals']
    users = principals['users']
    admins = principals['groups']['admins']
    user = principals.add_user(username, password=password)
    admins.memberids.connect([user])
    transaction.commit()

if __name__ == '__main__':
    main()
