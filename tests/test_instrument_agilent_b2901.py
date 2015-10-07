import unittest
import importlib
import os

import labtronyx
labtronyx.logConsole()

class Agilent_B2901_Functional_Tests(unittest.TestCase):

    SIM = True

    @classmethod
    def setUpClass(self):
        # Setup a mock manager
        self.manager = labtronyx.InstrumentManager(rpc=False)

        if 'TRAVIS' in os.environ or self.SIM:
            lib_path = os.path.join(os.path.dirname(__file__), 'sim', 'agilent_b2901.yaml')

            self.manager.enableInterface('VISA', library='%s@sim'%lib_path)

        # Find the instrument by model number
        dev_list = self.manager.findInstruments(deviceVendor='Agilent', deviceModel='B2901A')

        if len(dev_list) == 1:
            self.dev = dev_list[0]

        else:
            self.dev = None

    def setUp(self):
        if self.dev is None:
            self.skipTest("Instrument not present")
            return

        # Open the instrument
        self.dev.open()

        # Shorten timeout
        self.dev.configure(timeout=0.5)

        # Clear errors
        self.dev.getErrors()

    def tearDown(self):
        self.dev.close()

    def test_bad_command(self):
        self.assertRaises(labtronyx.common.errors.InterfaceTimeout, self.dev.query, 'BAD COMMAND')

        self.assertEqual(len(self.dev.getErrors()), 1)

    def test_configuration(self):
        conf = self.dev.getConfiguration()

    def test_aperture(self):
        self.dev.setSourceMode(1, 'VOLT')

        self.dev.setApertureTime(1, 1.0)
        self.dev.enableAutoAperture(1)
        self.dev.disableAutoAperture(1)

        self.assertEqual(len(self.dev.getErrors()), 0)

    def test_source_voltage(self):
        self.dev.setSourceVoltage(1, 1.25)
        self.assertEqual(self.dev.getSourceVoltage(1), 1.25)

        self.assertEqual(len(self.dev.getErrors()), 0)

    def test_source_current(self):
        self.dev.setSourceCurrent(1, 0.25)
        self.assertEqual(self.dev.getSourceCurrent(1), 0.25)

        self.assertEqual(len(self.dev.getErrors()), 0)

