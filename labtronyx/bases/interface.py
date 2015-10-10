import logging

from labtronyx.common.plugin import PluginBase

class Base_Interface(PluginBase):
    """
    Interface Base Class
    """

    info = {}
    
    def __init__(self, manager, **kwargs):
        """
        :param manager: Reference to the InstrumentManager instance
        :type manager: InstrumentManager object
        """
        PluginBase.__init__(self)

        self._manager = manager

        self.logger = kwargs.get('logger', logging)

        # Instance variables
        self._resources = {}

    @property
    def manager(self):
        return self._manager

    @property
    def resources(self):
        return self._resources

    @property
    def name(self):
        """
        Returns the interface name as defined by the `interfaceName` attribute in the info dictionary

        :return: str
        """
        if hasattr(self, 'info'):
            return self.info.get('interfaceName')
        else:
            return self.__class__.__name__

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