import unittest
from nose.tools import * # PEP8 asserts

import mock

import labtronyx
from labtronyx.bases import ResourceBase, DriverBase, InterfaceBase


def test_drivers():
    manager = labtronyx.InstrumentManager()

    for driver_uuid, driverCls in manager.plugin_manager.getPluginsByBaseClass(DriverBase).items():
        yield check_driver_api, driverCls


def check_driver_api(driverCls):
    if 'VISA' in driverCls.compatibleInterfaces:
        check_visa_api(driverCls)


def check_visa_api(driverCls):
    assert_true(driverCls._validateClassAttributes())
    assert_true(hasattr(driverCls, 'VISA_validResource'))
    assert_equal(type(driverCls.VISA_validResource(['','','',''])), bool)


def test_driver_integration():
    manager = labtronyx.InstrumentManager()

    # Create a fake interface, imitating the interface API
    interf = InterfaceBase(manager=manager)
    interf.info = dict(instrumentName='Debug')
    interf.open = mock.Mock(return_value=True)
    interf.close = mock.Mock(return_value=True)

    # Create a fake resource
    res = ResourceBase(manager=manager, interface=interf, resID='DEBUG')
    res.open = mock.Mock(return_value=True)
    res.isOpen = mock.Mock(return_value=True)
    res.close = mock.Mock(return_value=True)

    # Create a fake driver
    driver = DriverBase
    driver.open = mock.Mock(return_value=True)
    driver.close = mock.Mock(return_value=True)

    # Inject the fake resource into the fake interface
    interf._resources = {'DEBUG': res}

    # Inject the fake plugins into the manager
    manager.plugin_manager._plugins_instances[interf.uuid] = interf
    manager.plugin_manager._plugins_classes['drivers.Debug'] = driver

    # Load the driver
    res.loadDriver('drivers.Debug')

    # Make sure the driver was opened
    assert_true(driver.open.called)
    assert_false(driver.close.called)

    res.unloadDriver()
    assert_true(driver.close.called)