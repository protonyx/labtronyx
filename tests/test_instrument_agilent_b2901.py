import unittest
import os

import labtronyx


class Agilent_B2901_Functional_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Setup a mock manager
        self.manager = labtronyx.InstrumentManager()

        dev_list = self.manager.findInstruments(driver='Agilent.SMU.d_B29XX')

        if len(dev_list) == 0:
            lib_path = os.path.join(os.path.dirname(__file__), 'sim', 'agilent_b2901.yaml')

            self.manager.disableInterface('VISA')
            self.manager.enableInterface('VISA', library='%s@sim'%lib_path)

            # Find the instrument by model number
            dev_list = self.manager.findInstruments(driver='Agilent.SMU.d_B29XX')

        if len(dev_list) == 1:
            self.dev = dev_list[0]

        else:
            self.dev = None

    @classmethod
    def tearDownClass(cls):
        cls.manager._close()

    def setUp(self):
        if self.dev is None:
            self.fail("Instrument not present")

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
        self.dev._setSourceOutputMode(1, 'VOLT')

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

