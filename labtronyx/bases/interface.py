# Package relative imports
from ..common import events
from ..common.errors import *
from ..common.plugin import PluginBase, PluginAttribute

__all__ = ['InterfaceBase']


class InterfaceBase(PluginBase):
    """
    Interface Base Class

    :param manager:         InstrumentManager instance
    :type manager:          labtronyx.manager.InstrumentManager
    :param logger:          Logger instance
    :type logger:           logging.Logger
    """
    pluginType = 'interface'

    interfaceName = PluginAttribute(attrType=str, required=True)
    enumerable = PluginAttribute(attrType=bool, defaultValue=False)
    
    def __init__(self, manager, **kwargs):
        PluginBase.__init__(self, **kwargs)

        self._manager = manager

    @property
    def manager(self):
        return self._manager

    @property
    def resources(self):
        """
        Dictionary of resource objects by UUID

        :rtype: dict{str: labtronyx.bases.resource.ResourceBase}
        """
        return {plug_uuid: plugCls for plug_uuid, plugCls
                in self.manager.plugin_manager.getPluginInstancesByType('resource').items()
                if plugCls.interfaceName == self.interfaceName}

    def getProperties(self):
        """
        Get the interface properties

        :rtype: dict[str:object]
        """
        def_props = super(InterfaceBase, self).getProperties()
        def_props.update({
            'interfaceName': self.interfaceName,
            'resources': self.resources.keys()
        })
        return def_props

    def refresh(self):
        """
        Macro for interfaces that support enumeration. Calls `enumerate` then `prune` to get an updated list of
        resources available to the interface
        """
        self.enumerate()
        self.prune()

    # ==========================================================================
    # Interface Methods
    # ==========================================================================

    def open(self):
        """
        Interface Initialization
        
        Make any system driver calls necessary to initialize communication. If any kind of exception occurs that will
        inhibit communication, this function should return False to indicate an error to the InstrumentManager.

        This function is meant to be implemented by subclasses.
        
        :returns: True if ready, False if error occurred
        :rtype: bool
        """
        return True
    
    def close(self):
        """
        Interface clean-up
        
        Make any system driver calls necessary to clean-up interface operations. This function should explicitly free
        any system resources to prevent locking errors. Subclasses should be sure to call :func:`InterfaceBase.close` to
        ensure that instantiated resources are freed.

        :rtype: bool
        """
        for res_uuid, res_obj in self.resources.items():
            res_obj.close()

            self.manager.plugin_manager.destroyPluginInstance(res_uuid)

        return True

    # ===========================================================================
    # Optional Functions
    # ===========================================================================

    def enumerate(self):
        """
        Refreshes the resource list by enumerating all of the available devices on the interface.
        """
        pass

    def prune(self):
        """
        Clear out any resources that are no longer known to the interface
        """
        pass

    def getResource(self, resID):
        """
        Get a resource that may not be previously known to the interface. Attempts to open the resource using the given
        identifier. A `ResourceUnavailable` exception will be raised if the resource could not be located or opened.

        :param resID:   Resource Identifier
        :type resID:    str
        :return:        object
        :raises:        ResourceUnavailable
        """
        raise NotImplementedError