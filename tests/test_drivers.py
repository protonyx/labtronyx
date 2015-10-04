import unittest
import nose.tools as nose # PEP8 asserts

import labtronyx

instr = labtronyx.InstrumentManager()

def test_drivers():
    for driverName, driverCls in instr.drivers.items():
        print driverName
        yield check_driver_api, driverCls

def check_driver_api(driverCls):
    nose.assert_true(hasattr(driverCls, 'info'))
    nose.assert_in('deviceVendor', driverCls.info)
    nose.assert_in('deviceModel', driverCls.info)
    nose.assert_in('deviceType', driverCls.info)
    nose.assert_in('validResourceTypes', driverCls.info)

    if 'VISA' in driverCls.info['validResourceTypes']:
        check_visa_api(driverCls)

def check_visa_api(driverCls):
    nose.assert_true(hasattr(driverCls, 'VISA_validResource'))
    nose.assert_equal(type(driverCls.VISA_validResource(['','','',''])), bool)


class DriverUnitTests(unittest.TestCase):
    """

    """

    def setUp(self):
        pass

    def tearDown(self):
        pass



if __name__ == '__main__':
    unittest.main()
