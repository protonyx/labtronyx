import unittest
from nose.tools import * # PEP8 asserts

import mock

import labtronyx
from labtronyx.bases import ResourceBase, DriverBase, InterfaceBase


def test_resources():
    instr = labtronyx.InstrumentManager()

    for res_uuid, resCls in instr.plugin_manager.getPluginsByBaseClass(ResourceBase).items():
        yield check_resource_api, resCls


def check_resource_api(resCls):
    assert_true(resCls._validateClassAttributes())


def test_resource_integration():
    manager = labtronyx.InstrumentManager()

    # Create a fake interface, imitating the interface API
    interf = InterfaceBase(manager=manager)
    interf.interfaceName = 'Test'

    # Create a fake resource
    res = ResourceBase(manager=manager,
                       interface=interf,
                       resID='DEBUG')

    manager.plugin_manager._plugins_instances[interf.uuid] = interf
    manager.plugin_manager._plugins_instances[res.uuid] = res

    dev = manager.findInstruments(resourceID='DEBUG')
    assert_equal(len(dev), 1)