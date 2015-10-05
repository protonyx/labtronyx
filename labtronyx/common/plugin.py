"""
Plugin Architecture based on Yapsy

Yapsy was developed by Thibauld Nion (Copyright (c) 2007-2015, Thibauld Nion)

"""
import os
import logging

class PluginBase(object):
    """
    Base class for plugins
    """
    pass

class PluginManager(object):
    """
    Plugin Manager to search and categorize plugins

    Plugins are objects. They are distributed in modules
    """
    def __init__(self,
                 directories=None,
                 categories=None,
                 logger=None):

        if directories is None:
            directories = []
        self._directories = directories

        if categories is None:
            categories = {'': PluginBase}
        self._category_filter = categories

        if logger is None:
            self.logger = logging
        else:
            self.logger = logger

        # Instance variables
        self._plugin_modules = {}
        self._plugins = {}

    def search(self):
        for dir in self._directories:
            if type(dir) == str:
                self.locatePlugins(dir)
            else:
                self.locatePlugins(dir)

    def locatePlugins(self, package, recursive=True, prefix=''):
        """
        Get all valid plugins in a python package.

        :param package: path to plugin package
        :return:
        """
        # Use pkgutil to support compiled and frozen modules as plugins
        import pkgutil

        # Ensure absolute path
        package = os.path.abspath(package)

        # Create an iterator
        pkg_iter = pkgutil.iter_modules(path=[package])

        for importer, modname, ispkg in pkg_iter:
            if ispkg and recursive:
                self.locatePlugins(os.path.join(package, modname), recursive, prefix=prefix+modname+'.')

            else:
                # Attempt plugin import
                try:
                    plugin_name = prefix + modname
                    mod_imp = importer.find_module(modname)
                    mod = mod_imp.load_module(modname)

                    # Search for valid plugins within the module
                    if self.isValidPlugin(mod) and mod not in self._plugins:
                        self._plugin_modules[plugin_name] = mod

                        self.logger.debug("Loaded plugin module: %s", plugin_name)

                        # Extract valid plugins from module
                        self.extractPlugins(plugin_name)

                    else:
                        self.logger.debug("Skipped invalid plugin module: %s", plugin_name)

                except Exception as e:
                    self.logger.error("Unable to import: %s", modname)

    def getAllPlugins(self):
        return self._plugins.values()

    def getPluginsByCategory(self, category):
        # Rather than maintain another dictionary of categorized plugins, lets just do a search now
        category_bc = self._category_filter.get(category)

        if category_bc is None:
            return {}

        return {k:v for k,v in self._plugins.items() if issubclass(v, category_bc)}

    def getPlugin(self, plugin_name):
        return self._plugins.get(plugin_name)

    def getPluginInfo(self, plugin_name):
        return self._plugins.get(plugin_name).info

    def isValidPlugin(self, module):
        """
        Valid plugins:

           - Have a module-level `info` dictionary
           - Have a class that extends BasePlugin

        :param module:
        :return:
        """
        import inspect

        # Plugin must have an info dictionary
        if not hasattr(module, 'info'):
            module.info = {}
            # self.logger.debug("Plugin missing info dict: %s", module.__name__)
            # return False

        # Check if at least one class in the module extends PluginBase
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, PluginBase):
                return True

        return False

    def extractPlugins(self, plugin_module):
        """
        Extract all valid plugins from a plugin module

        :param plugin_module: name of plugin module
        :type plugin_module: str
        :return:
        """
        if plugin_module not in self._plugin_modules:
            raise KeyError("Plugin not found")

        module = self._plugin_modules.get(plugin_module)

        import inspect

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, PluginBase):
                # Check that the class is not one of the base plugin classes
                if obj not in self._category_filter.values() and obj not in self._plugins.values():
                    fq_plug_name = plugin_module + '.' + name

                    # Store the class (not an instance) in the plugin store
                    self._plugins[fq_plug_name] = obj

                    self.logger.debug("Loaded plugin: %s", fq_plug_name)