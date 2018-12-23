import sys
import types

# PY3 is left as bw-compat but PY2 should be used for most checks.
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2: # pragma: no cover
    string_types = (str, unicode)
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str
    long = long
else: # pragma: no cover
    string_types = (str,)
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes
    long = int

try:
    u = unicode
except NameError: # pragma NO COVER Python >= 3.0
    TEXT = str
    def u(x, encoding='ascii'):
        if isinstance(x, str):
            return x
        if isinstance(x, bytes):
            return x.decode(encoding)
    b = bytes
else: #pragma NO COVER Python < 3.0
    TEXT = unicode
    b = str

try:
    INT_TYPES = (int, long)
except NameError: #pragma NO COVER Python >= 3.0
    INT_TYPES = (int,)

try: # pragma: no cover Python < 3.0
    from base64 import decodebytes
    from base64 import encodebytes
except ImportError: #pragma NO COVER
    from base64 import decodestring as decodebytes
    from base64 import encodestring as encodebytes

try:
    from urllib.parse import parse_qsl
except ImportError: #pragma NO COVER
    from cgi import parse_qsl

try:
    from urllib.parse import urlsplit
except ImportError: #pragma NO COVER
    from urlparse import urlsplit
    from urlparse import urlunsplit
else: #pragma NO COVER
    from urllib.parse import urlunsplit

import string
try:
    _LETTERS = string.letters
except AttributeError: #pragma NO COVER
    _LETTERS = string.ascii_letters
del string

try:
    from html import escape # py3
except ImportError: #pragma NO COVER
    from cgi import escape


if PY2: # pragma: no cover
    def is_nonstr_iter(v):
        return hasattr(v, '__iter__')
else: # pragma: no cover
    def is_nonstr_iter(v):
        if isinstance(v, str):
            return False
        return hasattr(v, '__iter__')

if PY2: # pragma: no cover
    def native_(s, encoding='latin-1', errors='strict'):
        """ If ``s`` is an instance of ``text_type``, return
        ``s.encode(encoding, errors)``, otherwise return ``str(s)``"""
        if isinstance(s, text_type):
            return s.encode(encoding, errors)
        return str(s)
else: # pragma: no cover
    def native_(s, encoding='latin-1', errors='strict'):
        """ If ``s`` is an instance of ``text_type``, return
        ``s``, otherwise return ``str(s, encoding, errors)``"""
        if isinstance(s, text_type):
            return s
        return str(s, encoding, errors)

if PY2: # pragma: no cover
    import urlparse
    from urllib import quote as url_quote
    from urllib import quote_plus as url_quote_plus
    from urllib import unquote as url_unquote
    from urllib import urlencode as url_encode
    from urllib2 import urlopen as url_open

    def url_unquote_text(v, encoding='utf-8', errors='replace'): # pragma: no cover
        v = url_unquote(v)
        return v.decode(encoding, errors)

    def url_unquote_native(v, encoding='utf-8', errors='replace'): # pragma: no cover
        return native_(url_unquote_text(v, encoding, errors))
else: # pragma: no cover
    from urllib import parse
    urlparse = parse
    from urllib.parse import quote as url_quote
    from urllib.parse import quote_plus as url_quote_plus
    from urllib.parse import unquote as url_unquote
    from urllib.parse import urlencode as url_encode
    from urllib.request import urlopen as url_open
    url_unquote_text = url_unquote
    url_unquote_native = url_unquote

def text_(s, encoding='latin-1', errors='strict'): # pragma: no cover
    """ If ``s`` is an instance of ``binary_type``, return
    ``s.decode(encoding, errors)``, otherwise return ``s``"""
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    return s
