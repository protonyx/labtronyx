"""
Plugin Architecture based on Yapsy

Yapsy was developed by Thibauld Nion (Copyright (c) 2007-2015, Thibauld Nion)

"""
import os
import logging
import inspect
import uuid

__all__ = ['PluginBase', 'PluginAttribute', 'PluginParameter', 'PluginDependency']


class _PluginManager(object):
    """
    Plugin Manager to search and categorize plugins

    Plugins are objects. They are distributed in modules
    """
    def __init__(self):
        self.__logger = logging

        # Instance variables
        self._search_dirs = []
        self._plugins_classes = {}
        self._plugins_instances = {}

    @property
    def logger(self):
        return self.__logger

    @logger.setter
    def logger(self, new_value):
        self.__logger = new_value

    @property
    def directories(self):
        return self._search_dirs

    @property
    def plugins(self):
        return self._plugins_classes

    def search(self, dir):
        """
        Search for plugins in directory `dir`. If directory has already been searched, it will not be searched again
        to prevent re-importing modules.
        """
        if dir not in self._search_dirs:
            self.locatePlugins(dir)
            self._search_dirs.append(dir)

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
        pkg_iter = list(pkgutil.iter_modules(path=[plugin_path]))

        if len(pkg_iter) == 0:
            self.logger.info("No Python package found at path: %s", plugin_path)
            return

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
                        if plugin_cls not in self._plugins_classes.values():
                            fq_name = plugin_name + '.' + name
                            plugin_cls.fqn = fq_name

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
        return {pluginName:pluginCls.getClassAttributes() for pluginName, pluginCls in self._plugins_classes.items()}

    def getPluginsByBaseClass(self, base_class):
        """
        Get a dictionary of plugin classes that subclass the given base class

        :param base_class:  Plugin Base Class
        :type base_class:   type(PluginBase)
        :rtype:             dict{str: type(base_class)}
        """
        return {k: v for k, v in self._plugins_classes.items() if issubclass(v, base_class) and v != base_class}

    def getPluginsByType(self, plugin_type):
        return {k: v for k, v in self._plugins_classes.items() if v.pluginType == plugin_type}

    def getPlugin(self, plugin_fqn):
        """
        Get the plugin class for a plugin with a given name

        :param plugin_fqn:  Plugin Fully Qualified Name
        :type plugin_fqn:   str
        :rtype:             type(PluginBase)
        :raises:            KeyError
        """
        if plugin_fqn in self._plugins_classes:
            return self._plugins_classes.get(plugin_fqn)
        else:
            raise KeyError("Plugin not found")

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
            plugin_cls._validateClassAttributes()

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
        :raises:                KeyError
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

    def destroyAllPluginInstances(self):
        for plugin_uuid in self._plugins_instances.keys():
            del self._plugins_instances[plugin_uuid]

    def getPluginInstance(self, plugin_uuid):
        """
        Get plugin instance by UUID

        :param plugin_uuid:     Plugin Instance UUID
        :type plugin_uuid:      str
        :rtype:                 PluginBase
        :raises:                KeyError
        """
        if plugin_uuid in self._plugins_instances:
            return self._plugins_instances.get(plugin_uuid)
        else:
            raise KeyError("Plugin instance does not exist")

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

    def getPluginInstancesByType(self, plugin_type):
        """
        Get plugin instances by the plugin attribute `pluginType`

        :param plugin_type:     Plugin type
        :type plugin_type:      str
        :rtype:                 dict[str:BasePlugin]
        """
        return {k: v for k, v in self._plugins_instances.items() if v.pluginType == plugin_type}

    def searchPluginInstances(self, **search_params):
        """
        Search for plugin instances that have attributes, parameters or properties that match the key-value pairs in
        `search_params`. Iterates through all plugin instances.

        :return: dict of Plugins that match search parameters
        :rtype: dict{str: PluginBase}
        """
        matching_plugins = {}

        for plugin_uuid, pluginObj in self._plugins_instances.items():
            plug_props = pluginObj.getProperties()
            plug_props.update(pluginObj.getAttributes())

            match = True
            for k, v in search_params.items():
                if plug_props.get(k) != v:
                    match = False
                    break

            if match:
                matching_plugins[plugin_uuid] = pluginObj

        return matching_plugins


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


class PluginParameter(PluginAttribute):
    def __init__(self, attrType=str, required=False, defaultValue=None, description=''):
        super(PluginParameter, self).__init__(attrType, required, defaultValue)
        self.description = description

    def getDict(self):
        return {
            'description': self.description,
            'required':    self.required
        }


class PluginDependency(object):
    def __init__(self, **kwargs):
        self.attrs = kwargs


class PluginBase(object):
    """
    Base class for plugins
    """
    _fqn = ''

    # Attributes
    author = PluginAttribute(attrType=str, required=False, defaultValue="")
    version = PluginAttribute(attrType=str, required=False, defaultValue="Unknown")
    pluginType = PluginAttribute(attrType=str, required=True)

    def __init__(self, check_dependencies=True, **kwargs):
        # Assign each plugin instance a universally unique identifier
        self._uuid = str(uuid.uuid4())
        self.__logger = kwargs.get('logger', logging)

        if self._fqn == '':
            self._fqn = self.__class__.__module__ + '.' + self.__class__.__name__

        self._resolveAttributes(**kwargs)

        self._resolveDependencies(check_dependencies)

    @property
    def fqn(self):
        return self._fqn

    @fqn.setter
    def fqn(self, new_value):
        self._fqn = new_value

    @property
    def uuid(self):
        return self._uuid

    @property
    def logger(self):
        return self.__logger

    @classmethod
    def _getClassAttributesByBase(cls, base_class):
        parent_classes = inspect.getmro(cls)

        attrs = {}
        # Traverse inheritance tree in reverse so that overrides work properly
        for parent in reversed(parent_classes):
            attrs.update(dict(inspect.getmembers(parent, lambda obj: issubclass(type(obj), base_class))))

        return attrs

    @classmethod
    def _getClassAttributeValue(cls, attr_name):
        attr_value = getattr(cls, attr_name)

        if issubclass(type(attr_value), PluginAttribute):
            # Not provided, use the default if not required
            if attr_value.required:
                attr_value = None
            else:
                attr_value = attr_value.defaultValue

        return attr_value

    @classmethod
    def _validateClassAttributes(cls):
        """
        Validate PluginAttributes defined for the class. Ignores PluginParameter attributes, as they are meant to be
        defined at plugin instantiation

        :return:    True if successful
        :rtype:     bool
        :raises:    Exception
        """
        for attr_name, attr_obj in cls._getClassAttributesByBase(PluginAttribute).items():
            if not issubclass(type(attr_obj), PluginParameter):
                # Plugin parameters are validated at the instance level, not the class
                try:
                    attr_val = cls._getClassAttributeValue(attr_name)

                    attr_obj.validate(attr_val)

                except Exception as e:
                    e.message = "Plugin attribute %s: %s" % (attr_name, e.message)
                    raise e

        return True

    @classmethod
    def getClassAttributes(cls):
        """
        Get values for all overridden PluginAttribute object defined at the class level. Excludes PluginParameter
        objects

        :rtype: dict
        """
        attrs = cls._getClassAttributesByBase(PluginAttribute)
        return {attr_name: cls._getClassAttributeValue(attr_name) for attr_name, attr_obj in attrs.items()
                if not issubclass(type(attr_obj), PluginParameter)}

    def _getAttributeValue(self, attr_name):
        attr_value = getattr(self, attr_name)

        if issubclass(type(attr_value), PluginAttribute):
            # Not provided, use the default if not required
            if attr_value.required:
                attr_value = None
            else:
                attr_value = attr_value.defaultValue

        return attr_value

    @property
    def attributes(self):
        return self.getAttributes()

    def _getAttributesByBase(self, base_class):
        attrs = self._getClassAttributesByBase(base_class)
        return {attr_name: self._getAttributeValue(attr_name) for attr_name in attrs}

    def getAttributes(self):
        """
        Get values for all overridden PluginAttribute objects defined at the instance level. PluginParameter
        attributes are overridden by instance parameters.

        :rtype: dict
        """
        return self._getAttributesByBase(PluginAttribute)

    def getParameters(self):
        """
        Get values for all overridden PluginParameter objects in the instance.

        :rtype: dict
        """
        return self._getAttributesByBase(PluginParameter)

    def _resolveAttributes(self, **kwargs):
        """
        Called on plugin instantiation to resolve all PluginAttribute objects on the instance. If an attribute is not
        overridden, the default value is used.
        """
        # Set all class-level attributes on the new instance. This is mostly to resolve default values
        attrs = self.getAttributes()

        for attr_name, attr_val in attrs.items():
            if attr_name in kwargs:
                setattr(self, attr_name, kwargs.get(attr_name))
            else:
                setattr(self, attr_name, attr_val)

    def _validateAttributes(self):
        """
        Validate PluginAttributes defined for the class.

        :return:    True if successful
        :rtype:     bool
        :raises:    Exception
        """
        for attr_name, attr_obj in self._getClassAttributesByBase(PluginAttribute).items():
            try:
                attr_val = self._getAttributeValue(attr_name)

                attr_obj.validate(attr_val)

            except Exception as e:
                e.message = "Plugin attribute %s: %s" % (attr_name, e.message)
                raise e

        return True

    def _resolveDependencies(self, check_dependencies):
        """
        Implements the dependency injection pattern to allow dependencies to be resolved at runtime without needing
        to pass objects when instantiating plugins

        :param check_dependencies:  Raise RuntimeError if dependency does not resolve to a single object
        """
        global plugin_manager
        assert(isinstance(plugin_manager, _PluginManager))

        for attr_name, dep_obj in self._getClassAttributesByBase(PluginDependency).items():
            matching_plugs = plugin_manager.searchPluginInstances(**dep_obj.attrs)

            if len(matching_plugs) == 1:
                setattr(self, attr_name, matching_plugs.values()[0])

            else:
                if check_dependencies:
                    raise RuntimeError("Unable to resolve plugin dependency: %s, %d matches found" % (attr_name,
                                                                                                  len(matching_plugs)))

                else:
                    setattr(self, attr_name, matching_plugs.values())

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

plugin_manager = _PluginManager()
