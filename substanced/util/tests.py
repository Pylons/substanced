import unittest
import colander

from pyramid import testing

from . import _marker

class Test__postorder(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, node):
        from . import postorder
        return postorder(node)

    def test_None_node(self):
        result = list(self._callFUT(None))
        self.assertEqual(result, [None])

    def test_IFolder_node_no_children(self):
        from ..interfaces import IFolder
        model = testing.DummyResource(__provides__=IFolder)
        result = list(self._callFUT(model))
        self.assertEqual(result, [model])

    def test_IFolder_node_nonfolder_children(self):
        from ..interfaces import IFolder
        model = testing.DummyResource(__provides__=IFolder)
        one = testing.DummyResource()
        two = testing.DummyResource()
        model['one'] = one
        model['two'] = two
        result = list(self._callFUT(model))
        self.assertEqual(result, [two, one, model])

    def test_IFolder_node_folder_children(self):
        from ..interfaces import IFolder
        model = testing.DummyResource(__provides__=IFolder)
        one = testing.DummyResource()
        two = testing.DummyResource(__provides__=IFolder)
        model['one'] = one
        model['two'] = two
        three = testing.DummyResource()
        four = testing.DummyResource()
        two['three'] = three
        two['four'] = four
        result = list(self._callFUT(model))
        self.assertEqual(result, [four, three, two, one, model])

class Test_oid_of(unittest.TestCase):
    def _callFUT(self, obj, default=_marker):
        from . import oid_of
        return oid_of(obj, default)

    def test_gardenpath(self):
        obj = testing.DummyResource()
        obj.__objectid__ = 1
        self.assertEqual(self._callFUT(obj), 1)

    def test_no_objectid_no_default(self):
        obj = testing.DummyResource()
        self.assertRaises(AttributeError, self._callFUT, obj)

    def test_no_objectid_with_default(self):
        obj = testing.DummyResource()
        self.assertEqual(self._callFUT(obj, 1), 1)

class TestBatch(unittest.TestCase):
    def _makeOne(self, seq, request, url=None, default_size=15, seqlen=None):
        from . import Batch
        return Batch(seq, request, url, default_size, seqlen=seqlen)

    def test_it_first_batch_of_3(self):
        seq = [1,2,3,4,5,6,7]
        request = testing.DummyRequest()
        request.params['batch_num'] = 0
        request.params['batch_size'] = 3
        request.url = 'http://example.com'
        inst = self._makeOne(seq, request)
        self.assertEqual(inst.items, [1,2,3])
        self.assertEqual(inst.num, 0)
        self.assertEqual(inst.size, 3)
        self.assertEqual(inst.length, 3)
        self.assertEqual(inst.last, 2)
        self.assertEqual(inst.required, True)
        self.assertEqual(inst.first_url, None)
        self.assertEqual(inst.prev_url, None)
        self.assertEqual(inst.next_url,
                         'http://example.com?batch_num=1&batch_size=3')
        self.assertEqual(inst.last_url,
                         'http://example.com?batch_num=2&batch_size=3')

    def test_it_first_batch_of_3_generator(self):
        def gen():
            for x in [1,2,3,4,5,6,7]:
                yield x
        seq = gen()
        request = testing.DummyRequest()
        request.params['batch_num'] = 0
        request.params['batch_size'] = 3
        request.url = 'http://example.com'
        inst = self._makeOne(seq, request, seqlen=7)
        self.assertEqual(inst.items, [1,2,3])
        self.assertEqual(inst.num, 0)
        self.assertEqual(inst.size, 3)
        self.assertEqual(inst.length, 3)
        self.assertEqual(inst.last, 2)
        self.assertEqual(inst.required, True)
        self.assertEqual(inst.first_url, None)
        self.assertEqual(inst.prev_url, None)
        self.assertEqual(inst.next_url,
                         'http://example.com?batch_num=1&batch_size=3')
        self.assertEqual(inst.last_url,
                         'http://example.com?batch_num=2&batch_size=3')

    def test_it_second_batch_of_3(self):
        seq = [1,2,3,4,5,6,7]
        request = testing.DummyRequest()
        request.params['batch_num'] = 1
        request.params['batch_size'] = 3
        request.url = 'http://example.com'
        inst = self._makeOne(seq, request)
        self.assertEqual(inst.items, [4,5,6])
        self.assertEqual(inst.num, 1)
        self.assertEqual(inst.size, 3)
        self.assertEqual(inst.length, 3)
        self.assertEqual(inst.last, 2)
        self.assertEqual(inst.required, True)
        self.assertEqual(inst.first_url,
                         'http://example.com?batch_num=0&batch_size=3')
        self.assertEqual(inst.prev_url,
                         'http://example.com?batch_num=0&batch_size=3')
        self.assertEqual(inst.next_url,
                         'http://example.com?batch_num=2&batch_size=3')
        self.assertEqual(inst.last_url,
                         'http://example.com?batch_num=2&batch_size=3')

    def test_it_second_batch_of_3_generator(self):
        def gen():
            for x in [1,2,3,4,5,6,7]:
                yield x
        seq = gen()
        request = testing.DummyRequest()
        request.params['batch_num'] = 1
        request.params['batch_size'] = 3
        request.url = 'http://example.com'
        inst = self._makeOne(seq, request, seqlen=7)
        self.assertEqual(inst.items, [4,5,6])
        self.assertEqual(inst.num, 1)
        self.assertEqual(inst.size, 3)
        self.assertEqual(inst.length, 3)
        self.assertEqual(inst.last, 2)
        self.assertEqual(inst.required, True)
        self.assertEqual(inst.first_url,
                         'http://example.com?batch_num=0&batch_size=3')
        self.assertEqual(inst.prev_url,
                         'http://example.com?batch_num=0&batch_size=3')
        self.assertEqual(inst.next_url,
                         'http://example.com?batch_num=2&batch_size=3')
        self.assertEqual(inst.last_url,
                         'http://example.com?batch_num=2&batch_size=3')

    def test_it_third_batch_of_3(self):
        seq = [1,2,3,4,5,6,7]
        request = testing.DummyRequest()
        request.params['batch_num'] = 2
        request.params['batch_size'] = 3
        request.url = 'http://example.com'
        inst = self._makeOne(seq, request)
        self.assertEqual(inst.items, [7])
        self.assertEqual(inst.num, 2)
        self.assertEqual(inst.size, 3)
        self.assertEqual(inst.length, 1)
        self.assertEqual(inst.last, 2)
        self.assertEqual(inst.required, True)
        self.assertEqual(inst.first_url,
                         'http://example.com?batch_num=0&batch_size=3')
        self.assertEqual(inst.prev_url,
                         'http://example.com?batch_num=1&batch_size=3')
        self.assertEqual(inst.next_url, None)
        self.assertEqual(inst.last_url, None)

    def test_it_third_batch_of_3_generator(self):
        def gen():
            for x in [1,2,3,4,5,6,7]:
                yield x
        seq = gen()
        request = testing.DummyRequest()
        request.params['batch_num'] = 2
        request.params['batch_size'] = 3
        request.url = 'http://example.com'
        inst = self._makeOne(seq, request, seqlen=7)
        self.assertEqual(inst.items, [7])
        self.assertEqual(inst.num, 2)
        self.assertEqual(inst.size, 3)
        self.assertEqual(inst.length, 1)
        self.assertEqual(inst.last, 2)
        self.assertEqual(inst.required, True)
        self.assertEqual(inst.first_url,
                         'http://example.com?batch_num=0&batch_size=3')
        self.assertEqual(inst.prev_url,
                         'http://example.com?batch_num=1&batch_size=3')
        self.assertEqual(inst.next_url, None)
        self.assertEqual(inst.last_url, None)

    def test_it_invalid_batch_num(self):
        seq = [1,2,3,4,5,6,7]
        request = testing.DummyRequest()
        request.params['batch_num'] = None
        request.params['batch_size'] = 3
        request.url = 'http://example.com'
        inst = self._makeOne(seq, request)
        self.assertEqual(inst.items, [1,2,3])
        self.assertEqual(inst.num, 0)

    def test_it_negative_batch_num(self):
        seq = [1,2,3,4,5,6,7]
        request = testing.DummyRequest()
        request.params['batch_num'] = -1
        request.params['batch_size'] = 3
        request.url = 'http://example.com'
        inst = self._makeOne(seq, request)
        self.assertEqual(inst.items, [1,2,3])
        self.assertEqual(inst.num, 0)

    def test_it_invalid_batch_size(self):
        seq = [1,2,3,4,5,6,7]
        request = testing.DummyRequest()
        request.params['batch_num'] = 0
        request.params['batch_size'] = None
        request.url = 'http://example.com'
        inst = self._makeOne(seq, request)
        self.assertEqual(inst.items, seq)
        self.assertEqual(inst.size, 15)

    def test_it_negative_batch_size(self):
        seq = [1,2,3,4,5,6,7]
        request = testing.DummyRequest()
        request.params['batch_num'] = 0
        request.params['batch_size'] = -1
        request.url = 'http://example.com'
        inst = self._makeOne(seq, request)
        self.assertEqual(inst.items, seq)
        self.assertEqual(inst.size, 15)

    def test_it_size_zero(self):
        seq = [1,2,3,4,5,6,7]
        request = testing.DummyRequest()
        request.params['batch_num'] = 0
        request.params['batch_size'] = 0
        request.url = 'http://example.com'
        inst = self._makeOne(seq, request)
        self.assertEqual(inst.items, seq)
        self.assertEqual(inst.size, 15)

    def test_it_multicolumn_toggle_text(self):
        seq = [1,2,3,4,5,6]
        request = testing.DummyRequest()
        request.params['multicolumn'] = 'True'
        inst = self._makeOne(seq, request)
        self.assertEqual(inst.toggle_text, 'Single column')

    def test_it_not_multicolumn_toggle_text(self):
        seq = [1,2,3,4,5,6]
        request = testing.DummyRequest()
        request.params['multicolumn'] = 'False'
        inst = self._makeOne(seq, request)
        self.assertEqual(inst.toggle_text, 'Multi-column')

    def test_it_make_columns(self):
        seq = [1,2,3,4,5,6]
        request = testing.DummyRequest()
        inst = self._makeOne(seq, request)
        cols = inst.make_columns(column_size=2, num_columns=3)
        expected = [ [1,2], [3,4], [5,6] ]
        self.assertEqual(cols, expected)

class Test_merge_url_qs(unittest.TestCase):
    def _callFUT(self, url, **kw):
        from . import merge_url_qs
        return merge_url_qs(url, **kw)

    def test_with_no_qs(self):
        url = 'http://example.com'
        result = self._callFUT(url, a=1, b=2)
        self.assertEqual(result, 'http://example.com?a=1&b=2')

    def test_with_existing_qs_overlap(self):
        url = 'http://example.com?a=3'
        result = self._callFUT(url, a=1, b=2)
        self.assertEqual(result, 'http://example.com?a=1&b=2')

    def test_with_existing_qs_no_overlap(self):
        url = 'http://example.com?c=3'
        result = self._callFUT(url, a=1, b=2)
        self.assertEqual(result, 'http://example.com?a=1&b=2&c=3')

class TestNameSchemaNode(unittest.TestCase):
    def _makeOne(self, **kw):
        from . import NameSchemaNode
        return NameSchemaNode(**kw)

    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _makeBindings(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        return dict(request=request, context=context)

    def test_it_invalid_len(self):
        bindings = self._makeBindings()
        node = self._makeOne()
        def check_name(value): pass
        bindings['context'].check_name = check_name
        bindings['request'].registry.content = DummyContent(True)
        node.bindings = bindings
        node.max_len = 1
        self.assertRaises(colander.Invalid, node.validator, node, 'abc')

    def test_it_invalid_check_name(self):
        bindings = self._makeBindings()
        node = self._makeOne()
        def check_name(value):
            self.assertEqual(value, 'abc')
            raise ValueError('abc')
        bindings['context'].check_name = check_name
        bindings['request'].registry.content = DummyContent(True)
        node.bindings = bindings
        self.assertRaises(colander.Invalid, node.validator, node, 'abc')

    def test_it_valid(self):
        bindings = self._makeBindings()
        node = self._makeOne()
        def check_name(value): pass
        bindings['context'].check_name = check_name
        bindings['request'].registry.content = DummyContent(True)
        node.bindings = bindings
        self.assertEqual(node.validator(node, 'abc'), None)

    def test_it_editing_True_invalid(self):
        bindings = self._makeBindings()
        parent = testing.DummyResource()
        def check_name(value):
            raise ValueError('foo')
        parent.check_name = check_name
        bindings['context'].__parent__ = parent
        bindings['request'].registry.content = DummyContent(True)
        node = self._makeOne(editing=True)
        node.bindings = bindings
        self.assertRaises(colander.Invalid, node.validator, node, 'abc')

    def test_it_editing_True_valid(self):
        bindings = self._makeBindings()
        parent = testing.DummyResource()
        def check_name(value): pass
        parent.check_name = check_name
        bindings['context'].__parent__ = parent
        bindings['request'].registry.content = DummyContent(True)
        node = self._makeOne(editing=True)
        node.bindings = bindings
        self.assertEqual(node.validator(node, 'abc'), None)

    def test_it_editing_is_callable(self):
        bindings = self._makeBindings()
        parent = testing.DummyResource()
        def check_name(value): pass
        parent.check_name = check_name
        bindings['context'].__parent__ = parent
        bindings['request'].registry.content = DummyContent(True)
        def editing(context, request):
            self.assertEqual(context, bindings['context'])
            self.assertEqual(request, bindings['request'])
            return True
        node = self._makeOne(editing=editing)
        node.bindings = bindings
        self.assertEqual(node.validator(node, 'abc'), None)

class Test_acquire(unittest.TestCase):
    def _callFUT(self, node, name, default=None):
        from . import acquire
        return acquire(node, name, default=default)

    def test_missing_with_default(self):
        inst = DummyContent(None)
        marker = object()
        self.assertEqual(self._callFUT(inst, 'abc', marker), marker)

    def test_missing_no_default(self):
        inst = DummyContent(None)
        self.assertEqual(self._callFUT(inst, 'abc'), None)

    def test_hit(self):
        inst = DummyContent(None)
        inst.abc = '123'
        self.assertEqual(self._callFUT(inst, 'abc'), '123')

class Test_coarse_datetime_repr(unittest.TestCase):
    def _callFUT(self, d):
        from . import coarse_datetime_repr
        return coarse_datetime_repr(d)

    def test_it(self):
        import calendar
        import datetime
        d = datetime.datetime.utcnow()
        result = self._callFUT(d)
        timetime = calendar.timegm(d.timetuple())
        val = int(timetime) // 100        
        self.assertEqual(result, val)


class DummyContent(object):
    def __init__(self, result):
        self.result = result
