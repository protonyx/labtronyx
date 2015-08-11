import unittest
import importlib
import time
import os

from labtronyx import InstrumentManager

class InstrumentManager_Instrument_Agilent_34410A(unittest.TestCase):

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
        dev_list = self.manager.findInstruments(deviceModel="34410A")

        if len(dev_list) == 0:
            self.skipTest("Instrument not present")
            return

        self.dev = dev_list[0]

        # Open the instrument
        self.dev.open()

    def tearDown(self):
        self.dev.close()

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
