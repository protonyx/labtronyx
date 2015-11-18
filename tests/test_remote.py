import unittest
import mock
import requests
from nose.tools import * # PEP8 asserts
import time

import labtronyx
from labtronyx.common import jsonrpc


class Remote_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import time
        start = time.clock()
        cls.manager = labtronyx.InstrumentManager(server=True)

        cls.startup_time = time.clock() - start

        # Create a test object
        cls.manager.subtract = lambda subtrahend, minuend: int(subtrahend) - int(minuend)
        cls.manager.foobar = mock.MagicMock(return_value=None)
        cls.manager.raise_exception = mock.MagicMock(side_effect=RuntimeError)

        try:
            cls.client = labtronyx.RemoteManager(host=labtronyx.InstrumentManager.getHostname())

            cls.TEST_URI = cls.client.uri

        except labtronyx.RpcServerNotFound:
            cls.tearDownClass()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'manager'):
            cls.manager.server_stop()
            cls.manager._close()
            del cls.manager

    def setUp(self):
        if not hasattr(self, 'client'):
            self.fail("Client not present")

    def test_jsonrpc_request_call_multi_pos_param(self):
        req = '{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 1)
        self.assertEqual(len(rpc_err), 0)

        rpc_resp = rpc_resp[0]
        self.assertEqual(rpc_resp.result, 19)
        self.assertEqual(rpc_resp.id, 1)

    def test_jsonrpc_request_call_multi_named_param(self):
        req = '{"jsonrpc": "2.0", "method": "subtract", "params": {"subtrahend": 42, "minuend": 23}, "id": 3}'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 1)
        self.assertEqual(len(rpc_err), 0)

        rpc_resp = rpc_resp[0]
        self.assertEqual(rpc_resp.result, 19)
        self.assertEqual(rpc_resp.id, 3)

    def test_jsonrpc_request_call_no_params(self):
        req = '{"jsonrpc": "2.0", "method": "foobar", "id": 2}'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 1)
        self.assertEqual(len(rpc_err), 0)

        rpc_resp = rpc_resp[0]
        self.assertEqual(rpc_resp.result, None)
        self.assertEqual(rpc_resp.id, 2)

    def test_jsonrpc_request_call_multi_combo_param(self):
        req = '{"jsonrpc": "2.0", "method": "subtract", "params": [42], "kwargs": {"minuend": 23}, "id": 3}'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 1)
        self.assertEqual(len(rpc_err), 0)

        rpc_resp = rpc_resp[0]
        self.assertEqual(rpc_resp.result, 19)
        self.assertEqual(rpc_resp.id, 3)

    def test_jsonrpc_request_call_exception(self):
        req = '{"jsonrpc": "2.0", "method": "raise_exception", "id": 4}'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 0)
        self.assertEqual(len(rpc_err), 1)

        rpc_err = rpc_err[0]
        self.assertEqual(type(rpc_err), jsonrpc.JsonRpc_ServerException)

    def test_jsonrpc_request_error_invalid_json(self):
        req = '{"jsonrpc": "2.0", "method": "foobar, "params": "bar", "baz]'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 0)
        self.assertEqual(len(rpc_err), 1)

        rpc_err = rpc_err[0]
        self.assertEqual(type(rpc_err), jsonrpc.JsonRpc_ParseError)

    def test_jsonrpc_request_error_invalid_request(self):
        req = '{"jsonrpc": "2.0", "method": 1, "params": "bar"}'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 0)
        self.assertEqual(len(rpc_err), 1)

        rpc_err = rpc_err[0]
        self.assertEqual(type(rpc_err), jsonrpc.JsonRpc_InvalidRequest)

    def test_jsonrpc_request_error_parse_empty_request(self):
        req = '{}'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 0)
        self.assertEqual(len(rpc_err), 1)

        rpc_err = rpc_err[0]
        self.assertEqual(type(rpc_err), jsonrpc.JsonRpc_InvalidRequest)

    def test_jsonrpc_request_error_batch_invalid_json(self):
        req = '[\
                        {"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"},\
                        {"jsonrpc": "2.0", "method"\
                    ]'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 0)
        self.assertEqual(len(rpc_err), 1)

        rpc_err = rpc_err[0]
        self.assertEqual(type(rpc_err), jsonrpc.JsonRpc_ParseError)

    def test_jsonrpc_request_error_batch_empty(self):
        req = '[]'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 0)
        self.assertEqual(len(rpc_err), 1)

        rpc_err = rpc_err[0]
        self.assertEqual(type(rpc_err), jsonrpc.JsonRpc_InvalidRequest)

    def test_jsonrpc_request_error_batch_invalid_nonempty(self):
        req = '[1]'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 0)
        self.assertEqual(len(rpc_err), 1)

        rpc_err = rpc_err[0]
        self.assertEqual(type(rpc_err), jsonrpc.JsonRpc_InvalidRequest)

    def test_jsonrpc_request_error_parse_invalid_batch(self):
        req = '[1,2,3]'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 0)
        self.assertEqual(len(rpc_err), 3)

        self.assertEqual(type(rpc_err[0]), jsonrpc.JsonRpc_InvalidRequest)
        self.assertEqual(type(rpc_err[1]), jsonrpc.JsonRpc_InvalidRequest)
        self.assertEqual(type(rpc_err[2]), jsonrpc.JsonRpc_InvalidRequest)

    def test_jsonrpc_request_batch(self):
        req = '[{"jsonrpc": "2.0", "method": "subtract", "params": [100, 10], "id": 1}, \
                {"jsonrpc": "2.0", "method": "subtract", "params": [99, 11], "id": 2}]'

        resp = requests.post(self.TEST_URI, data=req)
        self.assertEqual(resp.status_code, 200)

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(resp.content)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 2)
        self.assertEqual(len(rpc_err), 0)

        self.assertEqual(rpc_resp[0].result, 90)
        self.assertEqual(rpc_resp[0].id, 1)
        self.assertEqual(rpc_resp[1].result, 88)
        self.assertEqual(rpc_resp[1].id, 2)

    def test_jsonrpc_decode_invalid(self):
        req = '123'

        rpc_req, rpc_resp, rpc_err = jsonrpc.decode(req)

        self.assertEqual(len(rpc_req), 0)
        self.assertEqual(len(rpc_resp), 0)
        self.assertEqual(len(rpc_err), 1)

        self.assertEqual(type(rpc_err[0]), jsonrpc.JsonRpc_ParseError)

    def test_jsonrpc_encode_empty(self):
        data_out = jsonrpc.encode([], [])

        self.assertEqual(data_out, '')

    def test_startup_time(self):
        assert_less_equal(self.startup_time, 5.0, "Remote initialization time: %f was greater than 5.0 seconds" %
                          self.startup_time)

    def test_remote_client_connect(self):
        methods = self.client._getMethods()
        assert_greater_equal(len(methods), 0)

        assert_in('getVersion', methods)

        assert_equal(self.client.getVersion(), self.manager.getVersion())

    def test_remote_error_server_not_running(self):
        with self.assertRaises(labtronyx.common.rpc.errors.RpcServerNotFound):
            client = labtronyx.RemoteManager(port=6782)

            client.test_connection()

    def test_remote_error_invalid_path(self):
        resp = requests.post(self.TEST_URI + '/invalid', data='')
        self.assertEqual(resp.status_code, 404)

    def test_remote_error_timeout(self):
        old_timeout = self.client.timeout
        self.client.timeout = 0.1

        import time
        self.manager.test_timeout = lambda: time.sleep(0.2)

        with self.assertRaises(labtronyx.common.rpc.errors.RpcTimeout):
            self.client.test_timeout()

        self.client.timeout = old_timeout

    def test_remote_get_resource(self):
        self.client.refresh()

        res_list = self.client.findResources()

        if len(res_list) == 0:
            self.skipTest("No resources on server")

        for res in res_list:
            methods = res._getMethods()
            assert_greater_equal(len(methods), 0)

    def test_remote_exception_handling(self):
        def test_exception():
            raise UserWarning('Test Message')

        self.manager.test_exception = test_exception

        with self.assertRaises(UserWarning):
            self.client.test_exception()

    def test_remote_event_subscribe(self):
        import threading
        event = threading.Event()
        event.clear()

        self.time_set = 0.0

        def on_event(self, event):
            event.set()
            self.time_set = time.time()

        # Create a subscriber
        sub = labtronyx.common.events.EventSubscriber(logger=self.manager.logger)
        sub.connect('localhost')
        sub.registerCallback('TEST_EVENT', lambda _: on_event(self, event))

        # Give time for the client to connect
        time.sleep(0.5)

        # Publish the test event
        time_publish = time.time()
        self.manager._publishEvent('TEST_EVENT')

        # Wait for event to be set
        event.wait(1.0)

        # Stop the subscriber thread
        sub.stop()
        del sub

        # Verify the event was set
        if not event.is_set():
            self.fail('Event not received')

        else:
            time_delta = self.time_set - time_publish
            self.assertLess(time_delta, 1.0)