from lxml.etree import HTML
from lxml.etree import tostring
from lxml.objectify import ObjectPath
from zope.interface import Interface
from zope.interface import implementer

from ..file import IFile
from ..util import chunks

HTML_TITLE = ObjectPath('html.head.title')
HTML_META = ObjectPath('html.head.meta')
HTML_BODY = ObjectPath('html.body')

class IEditable(Interface):
    """ Adapter interface for editing content as a file.
    """
    def get():
        """ Return ``(body_iter, mimetype)`` representing the context.

        - ``body_iter`` is an iterable, whose chunks are bytes represenating
          the context as an editable file.

        - ``mimetype`` is the MIMEType corresponding to ``body_iter``.
        """

    def put(fileish):
        """ Update context based on the contents of ``fileish``.

        - ``fileish`` is a file-type object:  its ``read`` method should
          return the (new) file representation of the context.
        """

class ISource(Interface):
    """ Adapter interface for mapping context to / from editable source text.
    """
    def renderAsHTML():
        """ Return True if the source should render as HTML, else False.
        """

    def title():
        """ Return the value to be embedded as the source text's title.
        """

    def metadata():
        """ Return a sequence of tuples for document metadata.

        Tuples are in form ``(name, value)``
        """

    def body():
        """ Return the body of the source.
        """

    def apply(title, metadata, body):
        """ Parse values and update the context.
        """

@implementer(IEditable)
class FileEditable(object):
    """ IEditable adapter for stock SubstanceD 'File' objects.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        """ See IEditable.
        """
        return (
            chunks(open(self.context.blob.committed(), 'rb')),
            self.context.mimetype or 'application/octet-stream',
            )

    def put(self, fp):
        """ See IEditable.
        """
        self.context.upload(fp)

@implementer(IEditable)
class TextEditable(object):
    """ IEditable adapter for "textual" objects.

    - 'context' **must** have an adapter registered for ``ISource``.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        """ See IEditable.
        """
        source = self.request.registry.getMultiAdapter(
                                (self.context, self.request), ISource)
        title = source.title()
        mimetype = _get_mimetype(source.renderAsHTML() and 'html' or 'rst')
        lines = []
        if source.renderAsHTML():
            lines += [
                '<html>',
                '<head>',
                '<title>%s</title>' % title,
            ]
            lines += [('<meta type="%s" value="%s" />' % (name, value))
                                for name, value in source.metadata()]
            lines += [
                '</head>',
                '<body>',
            ]
            lines.extend(source.body().splitlines())
            lines += [
                '</body>',
                '</html>',
            ]
        else:
            t_bar = '=' * len(title)
            lines += ['%s: %s' % x for x in source.metadata()]
            lines += [t_bar, title, t_bar, '', source.body()]
        if lines[-1] != '\n':
            lines.append('\n')
        return (x.encode('utf8') for x in lines), mimetype

    def put(self, fp):
        """ See IEditable.
        """
        source = self.request.registry.getMultiAdapter(
                                (self.context, self.request), ISource)
        body = fp.read()
        text = body.decode('utf8')
        lines = text.splitlines()
        meta = []
        is_html = lines[0].startswith('<html')
        if is_html:
            tree = HTML(body)
            title = HTML_TITLE(tree).text
            for elem in tree.findall('./head/meta'):
                meta.append((elem.get('type'), elem.get('value')))
            body_elem = tree.find('./body')
            body_lines = [body_elem.text.strip()]
            body_lines.extend([tostring(child, method='html',
                                        encoding='unicode',
                                       ).strip()
                                for child in body_elem.getchildren()])
            body = '\n'.join(filter(None, body_lines))
        else:
            while lines and not lines[0].startswith('='):
                line, lines = lines[0], lines[1:]
                name, value = [x.strip() for x in line.split(':', 1)]
                meta.append((name, value))
            if lines:
                lines = lines[1:] # Skip leading '==='
            if lines:
                title, lines = lines[0].strip(), lines[1:]
            if lines:
                body = '\n'.join(lines[2:]) # skip trailing '===', blank
        source.apply(title, meta, body, is_html)

def _get_mimetype(format):
    if format == 'rst':
        mimetype = 'text/x-rst'
    else: # format == 'html':
        mimetype = 'text/html'
    return '%s; charset=utf8' % mimetype

def register_editable_adapter(config, adapter, iface): # pragma: no cover
    """ Configuration directive: register ``IEditable`` adapter for ``iface``.

    - ``adapter`` is the adapter factory (a class or other callable taking
      ``(context, request)``).

    - ``iface`` is the interface / class for which the adapter is registerd.
    """
    def register():
        intr['registered'] = adapter
        config.registry.registerAdapter(adapter, (iface, Interface), IEditable)

    discriminator = ('sd-editable-adapter', iface)
    intr = config.introspectable(
        'sd editable adapters',
        discriminator,
        iface.__name__,
        'sd editable adapter'
        )
    intr['adapter'] = adapter

    config.action(discriminator, callable=register, introspectables=(intr,))

def register_source_adapter(config, adapter, iface): # pragma: no cover
    """ Configuration directive: register ``ISource`` adapter for ``iface``.

    - ``adapter`` is the adapter factory (a class or other callable taking
      ``(context, request)``).

    - ``iface`` is the interface / class for which the adapter is registerd.

    - Also registers ``TextEditable`` as the ``IEditable`` adapter for
      ``iface``.
    """
    def register():
        intr['registered'] = adapter
        config.registry.registerAdapter(adapter, (iface, Interface), ISource)

    discriminator = ('sd-source-adapter', iface)
    intr = config.introspectable(
        'sd source adapters',
        discriminator,
        iface.__name__,
        'sd source adapter'
        )
    intr['adapter'] = adapter

    config.action(discriminator, callable=register, introspectables=(intr,))

    register_editable_adapter(config, TextEditable, iface)
        
def includeme(config): # pragma: no cover
    config.add_directive('register_editable_adapter',
                         register_editable_adapter)
    config.add_directive('register_source_adapter',
                         register_source_adapter)
    config.register_editable_adapter(FileEditable, IFile)
