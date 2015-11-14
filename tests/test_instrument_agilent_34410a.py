import unittest
import os

import labtronyx


class Agilent_34410A_Functional_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Setup a mock manager
        self.manager = labtronyx.InstrumentManager()

        dev_list = self.manager.findInstruments(driver='Agilent.Multimeter.d_3441XA')

        if len(dev_list) == 0:
            # Use sim
            lib_path = os.path.join(os.path.dirname(__file__), 'sim', 'agilent_34410a.yaml')

            self.manager.disableInterface('VISA')
            self.manager.enableInterface('VISA', library='%s@sim'%lib_path)

            # Find the instrument by model number
            dev_list = self.manager.findInstruments(driver='Agilent.Multimeter.d_3441XA')

        if len(dev_list) == 1:
            self.dev = dev_list[0]

        else:
            self.dev = None

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

    def test_modes(self):
        validModes = self.dev.getProperties().get('validModes')

        for mode in validModes:
            self.dev.setMode(mode)

            self.assertEqual(self.dev.getMode(), mode)

        self.assertEqual(len(self.dev.getErrors()), 0)

    @unittest.skip("Not yet supported")
    def test_sample_count(self):
        SAMPLES = 10

        self.dev.setSampleCount(SAMPLES)
        self.assertEqual(self.dev.getSampleCount(), SAMPLES)

        self.assertEqual(len(self.dev.getErrors()), 0)
