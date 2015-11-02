"""
Plugin Architecture based on Yapsy

Yapsy was developed by Thibauld Nion (Copyright (c) 2007-2015, Thibauld Nion)

"""
import os
import logging
import inspect


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
        self._plugins = {}
        self._plugins_disabled = {}

    @property
    def directories(self):
        return self._directories

    @property
    def categories(self):
        return self._category_filter

    def search(self):
        """
        Search all directories for plugins
        """
        for dir in self._directories:
            if type(dir) == str:
                self.locatePlugins(dir)
            else:
                self.locatePlugins(dir)

    def locatePlugins(self, plugin_path, recursive=True, prefix=''):
        """
        Locate and catalog all valid plugins within a python package at the given path.

        :param plugin_path:     Path to search
        :type plugin_path:      str
        :param recursive:       Scan subpackages recursively
        :type recursive:        bool
        """
        # Use pkgutil to support compiled and frozen modules as plugins
        import pkgutil

        # Ensure absolute path
        plugin_path = os.path.abspath(plugin_path)

        # Create an iterator
        pkg_iter = pkgutil.iter_modules(path=[plugin_path])

        for importer, modname, ispkg in pkg_iter:
            if ispkg and recursive:
                self.locatePlugins(os.path.join(plugin_path, modname), recursive, prefix=prefix+modname+'.')

            else:
                try:
                    plugin_name = prefix + modname

                    # Attempt plugin import
                    mod_imp = importer.find_module(modname)
                    mod = mod_imp.load_module(modname)

                    # Extract valid plugins from module
                    new_plugs = self.extractPlugins(mod)

                    for name, plugin_cls in new_plugs.items():
                        fq_name = plugin_name + '.' + name

                        if plugin_cls not in self._plugins.values():
                            self._plugins[fq_name] = plugin_cls

                            self.logger.debug("Found plugin: %s", fq_name)

                except ImportError:
                    self.logger.error("Unable to import: %s", modname)

                except Exception as e:
                    self.logger.exception("Exception during plugin load")

    def getAllPlugins(self):
        """
        Get a dictionary of all catalogued plugins

        :rtype: dict
        """
        return self._plugins

    def disablePlugin(self, plugin_name):
        if plugin_name in self._plugins:
            self._plugins_disabled[plugin_name] = self._plugins.pop(plugin_name)

    def getDisabledPlugins(self):
        return self._plugins_disabled

    def getPluginsByCategory(self, category):
        """
        Get a dictionary of catalogued plugins that subclass a category type

        :param category:    Plugin category
        :type category:     str
        :rtype:             dict
        """
        category_base_class = self._category_filter.get(category)

        if category_base_class is None:
            return {}

        # Rather than maintain another dictionary of categorized plugins, lets just do a search now
        return {k:v for k,v in self._plugins.items() if issubclass(v, category_base_class)}

    def getPlugin(self, plugin_name):
        """
        Get the plugin class for a plugin with a given name

        :param plugin_name: Plugin name
        :type plugin_name:  str
        :rtype:             class
        """
        return self._plugins.get(plugin_name)

    def getPluginInfo(self, plugin_name):
        """
        Get the plugin attributes for a plugin with a given name

        :param plugin_name: Plugin name
        :type plugin_name:  str
        :rtype:             dict
        """
        return self._plugins.get(plugin_name).getAttributes()

    def getPluginPath(self, plugin_name):
        """
        Get the file system path for the plugin with a given name

        :param plugin_name: Plugin name
        :type plugin_name:  str
        :returns:           Path to plugin module
        :rtype:             str
        """
        plugin_cls = self._plugins.get(plugin_name)
        return inspect.getfile(plugin_cls)

    def isValidPlugin(self, plugin_cls):
        """
        Used by `extractPlugins` to check if a class contained within a module is a usable plugin.

        :param plugin_cls:  Plugin class
        :type plugin_cls:   class
        :return:
        """
        if not issubclass(plugin_cls, PluginBase):
            return False

        # Check that the class is not one of the base plugin classes
        if plugin_cls in self._category_filter.values():
            return False

        return True

    def extractPlugins(self, plugin_module):
        """
        Extract all valid plugins from a module. Returns a dictionary of plugins found in the module

        :param plugin_module:   Python Module
        :type plugin_module:    module
        :return:                dict
        """
        return {name:cls for name,cls in inspect.getmembers(plugin_module, inspect.isclass) if self.isValidPlugin(cls)}

    def validatePlugin(self, plugin_name):
        """
        Validate plugin attributes for a plugin with the given name

        :param plugin_name:     Plugin name
        :type plugin_name:      str
        """
        plugin_cls = self.getPlugin(plugin_name)

        try:
            plugin_cls._validateAttributes()

        except AssertionError as e:
            self.logger.error("Plugin %s error: %s", plugin_name, e.message)
            return False

        return True


class PluginAttribute(object):
    def __init__(self, attrType=str, required=False, defaultValue=None):
        self.attrType = attrType
        self.required = required
        self.defaultValue = defaultValue

    def validate(self, value):
        if self.required and value is None:
            raise AssertionError("is required")

        if type(value) != self.attrType:
            raise AssertionError("must be of type %s" % self.attrType)


class PluginBase(object):
    """
    Base class for plugins
    """
    # Attributes
    author = PluginAttribute(attrType=str, required=False, defaultValue="")
    version = PluginAttribute(attrType=str, required=False, defaultValue="Unknown")

    def __init__(self, **kwargs):
        # Set all class-level attributes on the new instance. This is mostly to resolve default values
        attrs = self.getAttributes()

        for attr_name, attr_val in attrs.items():
            setattr(self, attr_name, attr_val)

        self.logger = kwargs.get('logger', logging)

    @classmethod
    def _getAttributeClasses(cls):
        import inspect
        parent_classes = inspect.getmro(cls)

        attrs = {}
        # Traverse inheritance tree in reverse so that overrides work properly
        for parent in reversed(parent_classes):
            attrs.update(dict(inspect.getmembers(parent, lambda obj: issubclass(type(obj), PluginAttribute))))

        return attrs

    @classmethod
    def getAttributes(cls):
        attrs = cls._getAttributeClasses()
        attr_vals = {}

        for attr_name, attr_obj in attrs.items():
            attr_value = getattr(cls, attr_name, None)

            if issubclass(type(attr_value), PluginAttribute):
                # Not provided, use the default if not required
                if attr_obj.required:
                    attr_value = None
                else:
                    attr_value = attr_obj.defaultValue

            attr_vals[attr_name] = attr_value

        return attr_vals

    @classmethod
    def _validateAttributes(cls):
        attr_vals = cls.getAttributes()

        for attr_name, attr_obj in cls._getAttributeClasses().items():
            try:
                attr_obj.validate(attr_vals.get(attr_name))

            except AssertionError as e:
                raise AssertionError("Plugin attribute %s %s" % (attr_name, e.message))

        return True