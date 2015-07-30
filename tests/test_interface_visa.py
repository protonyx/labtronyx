import unittest
import importlib
import mock

from labtronyx import InstrumentManager

class InstrumentManager_Interface_VISA_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # Setup a mock manager
        self.manager = mock.Mock(spec=InstrumentManager)

        self.m_visa = importlib.import_module('labtronyx.interfaces.i_VISA')
        self.i_visa = self.m_visa.i_VISA(manager=self.manager)

    def test_interface_visa_open(self):
        self.i_visa.open()

    def test_interface_visa_enumerate_time(self):
        import time
        start = time.clock()
        self.i_visa.enumerate()
        self.assertLessEqual(time.clock() - start, 1.0, "VISA refresh time must be less than 1.0 second(s)")

    def test_interface_visa_get_resources(self):
        ret = self.i_visa.getResources()

        self.assertEqual(type(ret), dict)

    def test_interface_visa_close(self):
        self.i_visa.close()
        
        