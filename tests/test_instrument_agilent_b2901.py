import unittest
import importlib
import os

from labtronyx import InstrumentManager

class InstrumentManager_Instrument_Agilent_B2901_Tests(unittest.TestCase):

    SIM = False

    @classmethod
    def setUpClass(self):
        # Setup a mock manager
        self.manager = InstrumentManager(rpc=False)

        if 'TRAVIS' in os.environ or self.SIM:
            self.m_visa = importlib.import_module('labtronyx.interfaces.i_VISA')
            lib_path = os.path.join(os.path.dirname(__file__), 'sim', 'default.yaml')

            self.manager.enableInterface(self.m_visa.i_VISA, library='%s@sim'%lib_path)

    def setUp(self):
        # Find the instrument by model number
        dev_list = self.manager.findInstruments(driver='drivers.Agilent.SMU.d_B29XX')

        if len(dev_list) == 0:
            self.skipTest("Instrument not present")
            return

        self.dev = dev_list[0]

        # Open the instrument
        self.dev.open()

    def tearDown(self):
        self.dev.close()

    @unittest.skip("Debug test for simulation")
    def test_sim_identify(self):
        dev_list = self.manager.findInstruments(resourceID='USB0::2391::12345::SIM::0::INSTR')
        self.assertEqual(len(dev_list), 1)

        dev = dev_list[0]

        self.assertEqual(dev.query('*IDN?'), "AGILENT TECHNOLOGIES,B2901A,12345,SIM")



