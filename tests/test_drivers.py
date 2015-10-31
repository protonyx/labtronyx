import unittest
from nose.tools import * # PEP8 asserts

import mock

import labtronyx
from labtronyx.bases import Base_Resource, Base_Driver, Base_Interface

def setUpModule():
    global instr
    instr = labtronyx.InstrumentManager()

def test_driver_api():
    global instr
    for driverName, driverCls in instr.drivers.items():
        yield check_driver_api, driverCls

def check_driver_api(driverCls):
    driverCls._validateAttributes()

    # Regression test
    assert_false(hasattr(driverCls, '_onLoad'))
    assert_false(hasattr(driverCls, '_onUnload'))

    if 'VISA' in driverCls.compatibleInterfaces:
        check_visa_api(driverCls)

def check_visa_api(driverCls):
    assert_true(hasattr(driverCls, 'VISA_validResource'))
    assert_equal(type(driverCls.VISA_validResource(['','','',''])), bool)

def test_driver_integration():
    instr = labtronyx.InstrumentManager()

    # Create a fake interface, imitating the interface API
    interf = Base_Interface(manager=instr)
    interf.info = dict(instrumentName='Debug')
    interf.open = mock.Mock(return_value=True)
    interf.close = mock.Mock(return_value=True)

    # Create a fake resource
    res = Base_Resource(manager=instr,
                             interface=interf,
                             resID='DEBUG')
    res.open = mock.Mock(return_value=True)
    res.isOpen = mock.Mock(return_value=True)
    res.close = mock.Mock(return_value=True)

    # Create a fake driver
    driver = Base_Driver
    driver.open = mock.Mock(return_value=True)
    driver.close = mock.Mock(return_value=True)

    # Inject the fake resource into the fake interface
    interf._resources = {'DEBUG': res}

    # Inject the fake interface into the manager instance
    instr._interfaces['interfaces.i_Debug'] = interf

    # Inject the fake driver into the driver dict
    instr._drivers['drivers.Debug'] = driver

    # Load the driver
    res.loadDriver('drivers.Debug')

    # Make sure the driver was opened
    assert_true(driver.open.called)
    assert_false(driver.close.called)

    res.unloadDriver()
    assert_true(driver.close.called)