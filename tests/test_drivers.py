import unittest
from nose.tools import * # PEP8 asserts

import labtronyx

def setUpModule():
    global instr
    instr = labtronyx.InstrumentManager(rpc=False)

def test_drivers():
    global instr
    for driverName, driverCls in instr.drivers.items():
        yield check_driver_api, driverCls

def check_driver_api(driverCls):
    assert_true(hasattr(driverCls, 'info'))
    assert_in('deviceVendor', driverCls.info)
    assert_in('deviceModel', driverCls.info)
    assert_in('deviceType', driverCls.info)
    assert_in('validResourceTypes', driverCls.info)

    # Regression test
    assert_false(hasattr(driverCls, '_onLoad'))
    assert_false(hasattr(driverCls, '_onUnload'))

    if 'VISA' in driverCls.info['validResourceTypes']:
        check_visa_api(driverCls)

def check_visa_api(driverCls):
    assert_true(hasattr(driverCls, 'VISA_validResource'))
    assert_equal(type(driverCls.VISA_validResource(['','','',''])), bool)

# TODO: Write Integration tests for drivers