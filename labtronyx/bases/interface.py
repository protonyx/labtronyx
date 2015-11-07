from labtronyx.common.plugin import PluginBase, PluginAttribute

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

        # Instance variables
        self._resources = {}

    @property
    def manager(self):
        return self._manager

    @property
    def resources(self):
        return self._resources

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
        try:
            self.enumerate()
        except NotImplementedError:
            pass

        try:
            self.prune()
        except NotImplementedError:
            pass

    # ==========================================================================
    # Interface Methods
    # ==========================================================================

    def open(self):
        """
        Interface Initialization
        
        Make any system driver calls necessary to initialize communication. If any kind of exception occurs that will
        inhibit communication, this function should return False to indicate an error to the InstrumentManager.
        
        :returns: True if ready, False if error occurred
        """
        raise NotImplementedError
    
    def close(self):
        """
        Interface clean-up
        
        Make any system driver calls necessary to clean-up interface operations. This function should explicitly free
        any system resources to prevent locking errors.
        """
        raise NotImplementedError

    # ===========================================================================
    # Optional Functions
    # ===========================================================================

    def enumerate(self):
        """
        Refreshes the resource list by enumerating all of the available devices on the interface.
        """
        raise NotImplementedError

    def prune(self):
        """
        Clear out any resources that are no longer known to the interface
        """
        raise NotImplementedError

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