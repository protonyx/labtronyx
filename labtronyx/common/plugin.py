"""
Plugin Architecture based on Yapsy

Yapsy was developed by Thibauld Nion (Copyright (c) 2007-2015, Thibauld Nion)

"""
import os
import logging
import inspect
import uuid


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
        self._plugins_classes = {}
        self._plugins_instances = {}

    @property
    def directories(self):
        return self._directories

    @property
    def categories(self):
        return self._category_filter

    @property
    def plugins(self):
        return self._plugins_classes

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
                        plugin_cls.fqn = fq_name

                        if plugin_cls not in self._plugins_classes.values():
                            self._plugins_classes[fq_name] = plugin_cls

                            self.logger.debug("Found plugin: %s", fq_name)

                except ImportError:
                    self.logger.error("Unable to import: %s", modname)

                except Exception as e:
                    self.logger.exception("Exception during plugin load")



    def getAllPlugins(self):
        """
        Get a dictionary of all catalogued plugins

        :rtype:                 dict[str:PluginBase]
        """
        return self._plugins_classes

    def getAllPluginInfo(self):
        """
        Get a dictionary with the attributes from all cataloged plugins
        :rtype:             dict[str:dict]
        """
        return {pluginName:pluginCls.getAttributes() for pluginName, pluginCls in self._plugins_classes.items()}

    def getPluginsByBaseClass(self, base_class):
        """
        Get a dictionary of plugin classes that subclass the given base class
        :param base_class:  Plugin Base Class
        :type base_class:   type(PluginBase)
        :rtype:             dict{str: type(base_class)}
        """
        return {k: v for k, v in self._plugins_classes.items() if issubclass(v, base_class)}

    def getPluginsByCategory(self, category):
        """
        Get a dictionary of catalogued plugins that subclass a category type

        :param category:    Plugin category
        :type category:     str
        :rtype:             dict{str: type(PluginBase)}
        """
        category_base_class = self._category_filter.get(category)

        if category_base_class is None:
            return {}

        return self.getPluginsByBaseClass(category_base_class)

    def getPluginsByType(self, plugin_type):
        return {k: v for k, v in self._plugins_classes.items() if v.pluginType == plugin_type}

    def getPlugin(self, plugin_name):
        """
        Get the plugin class for a plugin with a given name

        :param plugin_name: Plugin name
        :type plugin_name:  str
        :rtype:             type(PluginBase)
        """
        return self._plugins_classes.get(plugin_name)

    def getPluginInfo(self, plugin_name):
        """
        Get the plugin attributes for a plugin with a given name

        :param plugin_name: Plugin name
        :type plugin_name:  str
        :rtype:             dict
        """
        return self._plugins_classes.get(plugin_name).getAttributes()

    def getPluginPath(self, plugin_name):
        """
        Get the file system path for the plugin with a given name

        :param plugin_name: Plugin name
        :type plugin_name:  str
        :returns:           Path to plugin module
        :rtype:             str
        """
        plugin_cls = self._plugins_classes.get(plugin_name)
        return inspect.getfile(plugin_cls)

    def isValidPlugin(self, plugin_cls):
        """
        Used by `extractPlugins` to check if a class contained within a module is a usable plugin.

        :param plugin_cls:  Plugin class
        :type plugin_cls:   class
        :rtype:             bool
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
        :rtype:                 bool
        """
        plugin_cls = self.getPlugin(plugin_name)

        try:
            plugin_cls._validateAttributes()

        except AssertionError as e:
            self.logger.error("Plugin %s error: %s", plugin_name, e.message)
            return False

        return True

    def createPluginInstance(self, plugin_name, **kwargs):
        """
        Factory method to create a plugin instance

        :param plugin_name:     Fully qualified plugin name
        :type plugin_name:      str
        :return:                Plugin instance
        :rtype:                 PluginBase
        """
        plugCls = self.getPlugin(plugin_name)
        plugInst = plugCls(**kwargs)

        self._plugins_instances[plugInst.uuid] = plugInst
        return plugInst

    def destroyPluginInstance(self, plugin_uuid):
        """
        Destroy a plugin instance

        :param plugin_uuid:     Plugin Instance UUID
        :type plugin_uuid:      str
        :return:                True if successful, False otherwise
        :rtype:                 bool
        """
        if plugin_uuid in self._plugins_instances:
            del self._plugins_instances[plugin_uuid]
            return True

        else:
            return False

    def getPluginInstances(self, plugin_name):
        """
        Get plugin instances by fully qualified plugin name

        :param plugin_name:     Fully qualified plugin name
        :type plugin_name:      str
        :return:                List of Plugin instances
        :rtype:                 list[PluginBase]
        """
        return [plugCls for plug_uuid, plugCls in self._plugins_instances.items() if plugCls.fqn == plugin_name]

    def getPluginInstancesByBaseClass(self, base_class):
        """
        Get a dictionary of plugin instances that subclass the given base class

        :param base_class:  Plugin Base Class
        :type base_class:   type(PluginBase)
        :rtype:             dict{str: type(base_class)}
        """
        return {k: v for k, v in self._plugins_instances.items() if issubclass(type(v), base_class)}

    def getPluginInstancesByCategory(self, category):
        """
        Get plugin instances by the plugin category

        :param category:        Plugin category
        :type category:         str
        :rtype:                 dict[str:BasePlugin]
        """
        category_base_class = self._category_filter.get(category, PluginBase)

        return self.getPluginInstancesByBaseClass(category_base_class)

    def getPluginInstancesByType(self, plugin_type):
        """
        Get plugin instances by the plugin attribute `pluginType`

        :param plugin_type:     Plugin type
        :type plugin_type:      str
        :rtype:                 dict[str:BasePlugin]
        """
        return {k: v for k, v in self._plugins_instances.items() if v.pluginType == plugin_type}


class PluginAttribute(object):
    def __init__(self, attrType=str, required=False, defaultValue=None):
        self.attrType = attrType
        self.required = required
        self.defaultValue = defaultValue

    def validate(self, value):
        if self.required and value is None:
            raise ValueError("is required")

        if type(value) != self.attrType:
            # Can we cast?
            try:
                self.attrType(value)

            except:
                raise TypeError("must be of type %s" % self.attrType)


class PluginBase(object):
    """
    Base class for plugins
    """
    _fqn = ''

    # Attributes
    author = PluginAttribute(attrType=str, required=False, defaultValue="")
    version = PluginAttribute(attrType=str, required=False, defaultValue="Unknown")
    pluginType = PluginAttribute(attrType=str, required=True)

    def __init__(self, **kwargs):
        # Set all class-level attributes on the new instance. This is mostly to resolve default values
        attrs = self.getAttributes()

        for attr_name, attr_val in attrs.items():
            setattr(self, attr_name, attr_val)

        # Assign each plugin instance a universally unique identifier
        self._uuid = str(uuid.uuid4())
        self.logger = kwargs.get('logger', logging)

        if self._fqn == '':
            self._fqn = self.__class__.__module__ + '.' + self.__class__.__name__

    @property
    def fqn(self):
        return self._fqn

    @fqn.setter
    def fqn(self, new_value):
        self._fqn = new_value

    @property
    def uuid(self):
        return self._uuid

    @classmethod
    def _getClassAttributesByBase(cls, base_class):
        parent_classes = inspect.getmro(cls)

        attrs = {}
        # Traverse inheritance tree in reverse so that overrides work properly
        for parent in reversed(parent_classes):
            attrs.update(dict(inspect.getmembers(parent, lambda obj: issubclass(type(obj), base_class))))

        return attrs

    @classmethod
    def _getPluginAttributeClasses(cls):
        return cls._getClassAttributesByBase(PluginAttribute)

    @classmethod
    def getAttributes(cls):
        attrs = cls._getPluginAttributeClasses()
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

        for attr_name, attr_obj in cls._getPluginAttributeClasses().items():
            try:
                attr_obj.validate(attr_vals.get(attr_name))

            except Exception as e:
                e.message = "Plugin attribute %s: %s" % (attr_name, e.message)
                raise e

        return True

    @property
    def properties(self):
        return self.getProperties()

    def getProperties(self):
        """
        Get plugin instance properties

        :rtype:     dict[str:object]
        """
        return {
            'uuid': self.uuid,
            'fqn': self.fqn,
            'pluginType': self.pluginType
        }