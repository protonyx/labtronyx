import unittest
from nose.tools import * # PEP8 asserts

from labtronyx.common.plugin import PluginBase, PluginAttribute, PluginParameter

class plugin_test_class_required(PluginBase):
    pluginType = 'test'
    required_attribute = PluginAttribute(attrType=str, required=True)

class plugin_test_class_parameters(PluginBase):
    pluginType = 'test'
    required_param = PluginParameter(attrType=str, required=True)

def test_plugin_class_attributes():
    test_plugin = plugin_test_class_required()

    assert_raises(ValueError, test_plugin._validateClassAttributes)

    test_plugin._resolveAttributes(required_attributes="thing")
    assert_raises(ValueError, test_plugin._validateClassAttributes)

def test_plugin_parameters():
    test_plugin = plugin_test_class_parameters()

    assert_true(test_plugin._validateClassAttributes())
    assert_raises(ValueError, test_plugin._validateAttributes)

    test_plugin._resolveAttributes(required_param="thing")
    assert_true(test_plugin._validateAttributes())