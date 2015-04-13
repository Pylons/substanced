import datetime
import pytz

from docutils.core import publish_parts
from webob import Response

from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.url import resource_url
from substanced.util import find_catalog
from pyramid.view import (
    view_config,
    view_defaults,
    )

def _getentrybody(format, entry):
    if format == 'rst':
       body = publish_parts(entry, writer_name='html')['fragment']
    else:
       body = entry
    return body

@view_config(
    renderer='templates/frontpage.pt',
    content_type='Root',
    )
def blogview(context, request):
    system_catalog = find_catalog(context, 'system')
    blog_catalog = find_catalog(context, 'blog')
    content_type = system_catalog['content_type']
    query = content_type.eq('Blog Entry')
    query_result = query.execute().sort(blog_catalog['pubdate'], reverse=True)
    blogentries = []
    for blogentry in query_result:
        blogentries.append(
            {'url': resource_url(blogentry, request),
             'title': blogentry.title,
             'body': _getentrybody(blogentry.format, blogentry.entry),
             'pubdate': blogentry.pubdate,
             'attachments': [
                {'name': a.__name__, 'url': resource_url(a, request, 'download')} 
                for a in blogentry['attachments'].values()],
             'numcomments': len(blogentry['comments'].values()),
             })
    return dict(blogentries = blogentries)

@view_defaults(
    content_type='Blog Entry',
    renderer='templates/blogentry.pt',
    )
class BlogEntryView(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    @reify
    def blogentry(self):
        return _getentrybody(self.context.format, self.context.entry)

    @reify
    def comments(self):
        context = self.context
        system_catalog = find_catalog(context, 'system')
        blog_catalog = find_catalog(context, 'blog')
        content_type = system_catalog['content_type']
        path = system_catalog['path']
        comments_path = self.request.resource_path(context['comments'])
        query = content_type.eq('Comment') & path.eq(comments_path)
        query_result = query.execute().sort(blog_catalog['pubdate'])
        return query_result

    @reify
    def attachments(self):
        return self.context['attachments'].values()

    @view_config(request_method='GET')
    def view_blogentry(self):
        return dict(error_message = '')

    @view_config(request_method='POST')
    def add_comment(self):
        params = self.request.params
        commenter_name = params.get('commenter_name')
        comment_text = params.get('comment_text')
        spambot = params.get('spambot')
        if spambot:
           message = 'Your comment could not be posted'
        elif comment_text == '' and commenter_name == '':
           message = 'Please enter your name and a comment'
        elif comment_text == '':
           message = 'Please enter a comment'
        elif commenter_name == '':
           message = 'Please enter your name'
        else: 
           pubdate = datetime.datetime.now()
           comment = self.request.registry.content.create(
               'Comment', commenter_name, comment_text, pubdate)
           self.context.add_comment(comment)
           return HTTPFound(location=self.request.resource_url(self.context))
           
        return dict(error_message=message)

@view_config(
    content_type='File',
    name='download',
    )
def download_attachment(context, request):
    f = context.blob.open()
    headers = [('Content-Type', str(context.mimetype)),
               ('Content-Disposition',
                    'attachment;filename=%s' % str(context.__name__)),
              ]
    response = Response(headerlist=headers, app_iter=f)
    return response

@view_defaults(
    content_type='Root',
    )
class FeedViews(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def _nowtz(self):
        now = datetime.datetime.utcnow() # naive
        y, mo, d, h, mi, s = now.timetuple()[:6]
        return datetime.datetime(y, mo, d, h, mi, s, tzinfo=pytz.utc)

    def _get_feed_info(self):
        context = self.context
        request = self.request
        feed = {"rss_url": request.application_url + "/rss.xml",
                "atom_url": request.application_url + "/index.atom",
                "blog_url": request.application_url,
                "title": context.sdi_title,
                "description": context.description,
                }

        def _add_updated_strings(updated, info):
            if getattr(updated, 'now', None) is None:
                y, mo, d, h, mi, s = updated.timetuple()[:6]
                updated = datetime.datetime(y, mo, d, h, mi, s, tzinfo=pytz.utc)
            info['updated_atom'] = updated.astimezone(pytz.utc).isoformat()
            info['updated_rss'] = updated.strftime('%a, %d %b %Y %H:%M:%S %z')

        blogentries = []
        for name, blogentry in context.items():
            if request.registry.content.istype(blogentry, 'Blog Entry'):
                updated = blogentry.pubdate
                info = {'url': resource_url(blogentry, request),
                        'title': blogentry.title,
                        'body': _getentrybody(blogentry.format,
                                              blogentry.entry),
                        'created': updated,
                        'pubdate': updated,
                       }
                _add_updated_strings(updated, info)
                blogentries.append((updated, info))
                
        blogentries.sort(key=lambda x: x[0].isoformat())
        blogentries = [entry[1] for entry in reversed(blogentries)][:15]
        updated = blogentries and blogentries[0]['pubdate'] or self._nowtz()
        _add_updated_strings(updated, feed)
        
        return feed, blogentries

    @view_config(
        name='rss.xml',
        renderer='templates/rss.pt',
        )
    def blog_rss(self):
        feed, blogentries = self._get_feed_info()
        self.request.response.content_type = 'application/rss+xml'
        return dict(
            feed = feed,
            blogentries = blogentries,
            )

    @view_config(
        name='index.atom',
        renderer='templates/atom.pt',
        )
    def blog_atom(self):
        feed, blogentries = self._get_feed_info()
        self.request.response.content_type = 'application/atom+xml'
        return dict(
            feed = feed,
            blogentries = blogentries,
            )
