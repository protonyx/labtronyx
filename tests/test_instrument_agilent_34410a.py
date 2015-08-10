import unittest
import importlib
import time

from labtronyx import InstrumentManager

class InstrumentManager_Instrument_Agilent_34410A(unittest.TestCase):

    SIM = False

    @classmethod
    def setUpClass(self):
        # Setup a mock manager
        self.manager = InstrumentManager(rpc=False)

        if self.SIM:
            self.m_visa = importlib.import_module('labtronyx.interfaces.i_VISA')

            import os
            lib_path = os.path.join(os.path.dirname(__file__), 'sim', 'default.yaml')
            # lib_path = ''
            self.i_visa = self.m_visa.i_VISA(manager=self.manager, library='%s@sim'%lib_path)

            if not self.i_visa.open():
                print self.i_visa.getError()
                raise EnvironmentError("VISA Library did not initialize properly")

            self.manager._interfaces['labtronyx.interfaces.i_VISA'] = self.i_visa

        # Find the instrument by model number
        dev_list = self.manager.findInstruments(deviceModel="34410A")
        self.dev = dev_list[0]

        # Open the instrument
        self.dev.open()

    @classmethod
    def tearDownClass(self):
        self.dev.close()

        if self.SIM:
            self.i_visa.close()

    @unittest.skip("")
    def test_sweep_modes(self):
        for mode, code in self.dev.modes.items():
            self.dev.setMode(mode)

            time.sleep(0.5)

            self.assertNotEqual(self.dev.getMode(), 'Unknown')

        self.dev.setMode('DC Voltage')

    def test_sample_count(self):
        SAMPLES = 10

        self.dev.setSampleCount(SAMPLES)
        self.assertEqual(self.dev.getSampleCount(), SAMPLES)

        self.dev.setSampleCount(1)
