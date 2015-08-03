import unittest

from labtronyx import InstrumentManager, RemoteManager

class RemoteManager_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Setup an InstrumentManager with RPC
        self.instr = InstrumentManager(rpc=True)

        # Create a fake resource

        self.client = RemoteManager(uri='http://localhost:6780/')

    @classmethod
    def tearDownClass(self):
        self.instr.rpc_stop()

    def test_remote_connect(self):
        self.assertEqual(self.client.getVersion(), self.instr.getVersion())
