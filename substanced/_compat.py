
try:
    STRING_TYPES = (str, unicode)
except NameError: #pragma NO COVER Python >= 3.0
    STRING_TYPES = (str,)

try:
    u = unicode
except NameError: #pragma NO COVER Python >= 3.0
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
    
