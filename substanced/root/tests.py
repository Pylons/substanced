import unittest
from pyramid import testing
from pyramid.exceptions import ConfigurationError

class TestRoot(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _setupEvents(self):
        from ..objectmap import object_will_be_added
        from zope.interface import Interface
        from substanced.event import IObjectWillBeAdded
        def wrapper(event, obj, container):
            return object_will_be_added(event)
        self.config.add_subscriber(
            wrapper,
            [IObjectWillBeAdded, Interface, Interface]
            )
        # ^^^ to get user.__objectid__ set up right

    def _makeOne(self, settings):
        from . import Root
        return Root(settings)

    def test_ctor(self):
        self._setupEvents()
        settings = {
            'substanced.initial_password':'password',
            'substanced.initial_login':'login',
            'substanced.initial_email':'email@example.com',
            }
        inst = self._makeOne(settings)
        self.assertTrue('__services__' in inst)
        self.assertTrue('principals' in inst['__services__'])
        self.assertTrue('objectmap' in inst['__services__'])

    def test_ctor_no_initial_password(self):
        self._setupEvents()
        settings = {}
        self.assertRaises(
            ConfigurationError,
            self._makeOne,
            settings
            )

