import unittest

from labtronyx import InstrumentManager

class InstrumentManager_Interface_VISA_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.instr = InstrumentManager(rpc=False)

    def test_interface_visa_init(self):
        self.assertIn('labtronyx.interfaces.i_VISA', self.instr.getInterfaces())
        
        