import unittest
from pyramid import testing

class check_csrf_token(unittest.TestCase):
    def _callFUT(self, request, token):
        from .. import check_csrf_token
        return check_csrf_token(request, token)

    def test_success(self):
        request = testing.DummyRequest()
        request.params['csrf_token'] = request.session.get_csrf_token()
        self.assertEqual(self._callFUT(request, 'csrf_token'), None)

    def test_failure(self):
        from pyramid.httpexceptions import HTTPBadRequest
        request = testing.DummyRequest()
        self.assertRaises(HTTPBadRequest, self._callFUT, request, 'csrf_token')

class Test_add_mgmt_view(unittest.TestCase):
    def _callFUT(self, config, **kw):
        from .. import add_mgmt_view
        return add_mgmt_view(config, **kw)

    def _makeConfig(self):
        config = DummyConfigurator()
        return config

    def test_with_request_method_sorted(self):
        config = self._makeConfig()
        self._callFUT(config, request_method=('HEAD', 'GET'))
        self.assertEqual(config._added['request_method'], ('GET', 'HEAD'))
        self.assertTrue(config._actions)

    def test_with_request_method_get_implies_head(self):
        config = self._makeConfig()
        self._callFUT(config, request_method='GET')
        self.assertEqual(config._added['request_method'], ('GET', 'HEAD'))
        self.assertTrue(config._actions)

    def test_with_check_csrf(self):
        from pyramid.httpexceptions import HTTPBadRequest
        config = self._makeConfig()
        self._callFUT(config, check_csrf=True)
        preds = config._added['custom_predicates']
        self.assertEqual(len(preds), 1)
        self.assertTrue(config._actions)
        request = testing.DummyRequest()
        self.assertRaises(HTTPBadRequest, preds[0], None, request)
        request = testing.DummyRequest()
        request.params['csrf_token'] = request.session.get_csrf_token()
        self.assertTrue(preds[0](None, request))

    def test_view_isclass_with_attr(self):
        class AView(object):
            pass
        config = self._makeConfig()
        self._callFUT(config, view=AView, attr='foo')
        self.assertTrue(config.desc.startswith('method'))

    def test_discriminator(self):
        config = self._makeConfig()
        self._callFUT(config)
        self.assertTrue(config._actions[0][0], 'sdi view')

    def test_intr_action(self):
        config = self._makeConfig()
        self._callFUT(config)
        self.assertEqual(config._actions[0][1][0], config._intr)

    def test_intr_related(self):
        config = self._makeConfig()
        self._callFUT(config)
        self.assertTrue('views' in config._intr.related)

    def test_intr_values(self):
        config = self._makeConfig()
        self._callFUT(
            config, tab_title='tab_title', tab_condition='tab_condition',
            check_csrf=True, csrf_token='csrf_token')
        self.assertEqual(config._intr['tab_title'], 'tab_title')
        self.assertEqual(config._intr['tab_condition'], 'tab_condition')
        self.assertEqual(config._intr['check_csrf'], True)
        self.assertEqual(config._intr['csrf_token'], 'csrf_token')
        
class DummyConfigurator(object):
    _ainfo = None
    def __init__(self):
        self._intr = DummyIntrospectable()
        self._actions = []
        self._added = None

    def object_description(self, ob):
        return ob
        
    def maybe_dotted(self, thing):
        return thing

    def add_view(self, **kw):
        self._added = kw

    def introspectable(self, category, discrim, desc, name):
        self.desc = desc
        return self._intr

    def action(self, discriminator, introspectables):
        self._actions.append((discriminator, introspectables))
    
class DummyIntrospectable(dict):
    def __init__(self):
        dict.__init__(self)
        self.related = {}
        
    def relate(self, category, discrim):
        self.related[category] = discrim
        
