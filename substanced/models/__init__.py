from .folder import Folder # API
Folder = Folder # pyflakes
from .site import Site

from ..interfaces import ISite

def includeme(config):
    config.add_content_type(ISite, Site)
