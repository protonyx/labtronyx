"""
Getting Started
---------------

Interfaces are responsible for discovering and instantiating resource objects. They may also handle low-level operating
system interactions. This may include calls to hardware via driver stacks, or calls to other Python libraries.
Resources do not have an inherent dependency on the interface that instantiates it.

All interfaces are subclasses of :class:`labtronyx.InterfaceBase`::

    import labtronyx

    class INTERFACE_CLASS_NAME(labtronyx.InterfaceBase):
        pass

Required Attributes
-------------------

Interfaces require some attributes to be defined

   * `interfaceName` - str that names the interface.
   * `enumerable` - True if the interface supports resource enumeration. If False, the interface should implement the
     :func:`openResource` method to manually open a resource given a string identifier.
"""
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
        Make any system driver calls necessary to initialize communication. This method must not raise any exceptions.

        This function is meant to be implemented by subclasses.
        
        :returns: True if ready, False if error occurred
        :rtype: bool
        """
        return True
    
    def close(self):
        """
        Destroy all resource objects owned by the interface.

        May be extended by subclasses if any additional work is necessary to clean-up interface operations.

        :returns: True if successful, False otherwise
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