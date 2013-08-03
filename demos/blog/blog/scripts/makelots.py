import os
import datetime
import transaction
from optparse import OptionParser

def main():
    from pyramid.paster import get_app
    from pyramid.scripting import get_root
    from ..resources import BlogEntry
    parser = OptionParser(description=__doc__, usage='usage: %prog [options]')
    parser.add_option('-c', '--config', dest='config',
                      help='Specify a paster config file.')
    parser.add_option('-n', '--name', dest='name', default='main',
                      help='The paster config file section indicating the app.')
    parser.add_option('-i', '--num', dest='num', default='10000',
                      help='Specify the number of blog entries to add.')
    options, args = parser.parse_args()
    config = options.config
    name = options.name
    num = int(options.num)
    if config is None:
       raise ValueError('must supply config file name')
    config = os.path.abspath(os.path.normpath(config))
    
    app = get_app(config, name)
    root, closer = get_root(app)
    for n in range(0, num):
        print ("adding", n)
        entry = BlogEntry('title %s' % n, 'entry %s' % n,
                          'html', datetime.date.today())
        id = 'blogentry_%s' % n
        root[id] = entry
    print ('committing')
    transaction.commit()
           
if __name__ == '__main__':
   main()
