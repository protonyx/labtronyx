import unittest
import importlib

from labtronyx import InstrumentManager

class InstrumentManager_Instrument_Agilent_B2901_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Setup a mock manager
        self.manager = InstrumentManager(rpc=False)

        self.m_visa = importlib.import_module('labtronyx.interfaces.i_VISA')

        import os
        lib_path = os.path.join(os.path.dirname(__file__), 'sim', 'default.yaml')
        # lib_path = ''
        self.i_visa = self.m_visa.i_VISA(manager=self.manager, library='%s@sim'%lib_path)

        if not self.i_visa.open():
            print self.i_visa.getError()
            raise EnvironmentError("VISA Library did not initialize properly")

        self.manager._interfaces['labtronyx.interfaces.i_VISA'] = self.i_visa

    @classmethod
    def tearDownClass(self):
        self.i_visa.close()

    def test_identify(self):
        dev_list = self.manager.findInstruments(resourceID='USB0::2391::12345::SIM::0::INSTR')
        self.assertEqual(len(dev_list), 1)

        dev = dev_list[0]
        dev.open()

        self.assertEqual(dev.query('*IDN?'), "AGILENT TECHNOLOGIES,B2901A,12345,SIM")

        dev_list = self.manager.findInstruments(deviceModel="B2901A")
        self.assertEqual(len(dev_list), 1)

