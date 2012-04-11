from pyramid.view import view_config

@view_config()
def default_view(request):
    response = request.response
    response.body = """\
    <html><head></head><body>
    <a href="/manage">Go to management interface (log in as admin/admin)</a>
    </body>
    </html>"""
    return response

