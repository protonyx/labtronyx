import unittest
from nose.tools import * # PEP8 asserts

import labtronyx

class Server_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import time
        start = time.clock()
        cls.manager = labtronyx.InstrumentManager(server=True)

        cls.startup_time = time.clock() - start

    @classmethod
    def tearDownClass(cls):
        cls.manager.server_stop()
        del cls.manager

    def test_startup_time(self):
        assert_less_equal(self.startup_time, 2.0, "RPC Init time must be less than 2.0 second(s)")

    def test_remote_connect(self):
        client = labtronyx.RemoteManager(address='localhost')

        assert_equal(client.getVersion(), instr.getVersion())
