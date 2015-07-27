import unittest

from labtronyx import InstrumentManager

class InstrumentManager_RPC_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.instr = InstrumentManager(rpc=False)

    def test_start_rpc(self):
        self.assertTrue(self.instr.rpc_start())

    def test_stop_rpc(self):
        self.assertTrue(self.instr.rpc_start())

        self.instr.rpc_stop()