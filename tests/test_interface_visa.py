import unittest
import importlib
import mock

from labtronyx import InstrumentManager

class InstrumentManager_Interface_VISA_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Setup a mock manager
        self.manager = InstrumentManager(rpc=False)

        self.m_visa = importlib.import_module('labtronyx.interfaces.i_VISA')

        # import os
        # lib_path = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir)))
        # lib_path = os.path.join(lib_path, 'sim', 'default.yaml')
        # self.i_visa = self.m_visa.i_VISA(manager=self.manager, library='%s@sim'%lib_path)

        self.i_visa = self.m_visa.i_VISA(manager=self.manager, library='@sim')

        if not self.i_visa.open():
            raise EnvironmentError("VISA Library did not initialize properly")

        self.manager._interfaces['labtronyx.interfaces.i_VISA'] = self.i_visa

    @classmethod
    def tearDownClass(self):
        self.i_visa.close()

    def test_interface_visa_enumerate_time(self):
        import time
        start = time.clock()
        self.i_visa.enumerate()
        self.assertLessEqual(time.clock() - start, 1.0, "VISA refresh time must be less than 1.0 second(s)")

    def test_interface_visa_get_resources(self):
        ret = self.i_visa.getResources()

        self.assertEqual(type(ret), dict)
        self.assertEqual(len(ret), 1)

        print ret

    def test_instrument_agilent_b2901(self):
        test = self.manager.getProperties()

        dev_list = self.manager.findInstruments(deviceModel='B2901A')

        self.assertEqual(len(dev_list), 1)

        
        