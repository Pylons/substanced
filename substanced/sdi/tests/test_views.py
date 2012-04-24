import unittest
from pyramid import testing

class TestResetPasswordView(unittest.TestCase):
    def setUp(self):
        from ...site import Site
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        self._setupEvents()
        self.context = Site('good_login', 'password')
        self.request = testing.DummyRequest()
        self.request.mgmt_path = lambda *arg : 'http://example.com'
        self.request.context = self.context
        self.request.POST['csrf_token'] = self.request.session.get_csrf_token()

    def tearDown(self):
        testing.tearDown()

    def _setupEvents(self):
        from ...objectmap import object_will_be_added
        from zope.interface import Interface
        from substanced.event import IObjectWillBeAdded
        self.config.add_subscriber(
            object_will_be_added, [Interface,IObjectWillBeAdded])
        # ^^^ to get user.__objectid__ set up right

    def _makeOne(self):
        from ..views import reset_password
        return reset_password

    def test_reset_valid_login(self):
        inst = self._makeOne()
        self.request.POST['form.submitted'] = True
        self.request.POST['login'] = 'good_login'
        resp = inst(self.context, self.request)
        self.assertEqual(resp.location, 'http://example.com')

    def test_reset_invalid_login(self):
        inst = self._makeOne()
        self.request.POST['form.submitted'] = True
        self.request.POST['login'] = 'bad_login'
        resp = inst(self.context, self.request)
        self.assertEqual(resp['login'], 'bad_login')

    def test_reset_not_submitted(self):
        inst = self._makeOne()
        resp = inst(self.context, self.request)
        self.assertEqual(resp['login'], '')

    def test_reset_bad_csrf(self):
        inst = self._makeOne()
        self.request.POST['form.submitted'] = True
        self.request.POST['csrf_token'] = 'bad_token'
        resp = inst(self.context, self.request)
        self.assert_('Failed login (CSRF)' in self.request.session.peek_flash('error'))

