import logging

class Base_Interface(object):
    """
    Interface Base Class
    """

    # TODO: Interface will have hooks into the persistence config to "remember" how a particular device is configured
    # when the program is run in the future.
    
    def __init__(self, manager, **kwargs):
        """
        :param manager: Reference to the InstrumentManager instance
        :type manager: InstrumentManager object
        """
        self._manager = manager

        self.logger = kwargs.get('logger', logging)

        # Instance variables
        self._resources = {}

    @property
    def manager(self):
        return self._manager

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def resources(self):
        return self._resources
            
    # ==========================================================================
    # Interface Methods
    # ==========================================================================

    def getInterfaceName(self):
        return self.__class__.__name__

    def getResources(self):
        return self._resources

    # Inheriting classes must implement these functions:
    def open(self):
        """
        Interface Initialization
        
        Make any system driver calls necessary to initialize communication. If
        any kind of exception occurs that will inhibit communication, this
        function should return False to indicate an error to the 
        InstrumentManager.
        
        Any exceptions raised will be caught by the InstrumentManager, and it
        will be assumed that the interface failed to initialize. A subsequent
        call to :func:`close` will be made in this case.
        
        :returns: bool - True if ready, False if error occurred
        """
        raise NotImplementedError
    
    def close(self):
        """
        Interface clean-up
        
        Make any system driver calls necessary to clean-up interface
        operations. This function should explicitly free any system resources
        to prevent locking errors.
        
        Any exceptions raised will be caught by the InstrumentManager.
        """
        raise NotImplementedError

    def enumerate(self):
        """
        Refreshes the resource list by enumerating all of the available devices on the interface.
        """
        raise NotImplementedError

    def refresh(self):
        """
        Alias for enumerate
        """
        return self.enumerate()

    def getResource(self, resID):
        """

        :param resID: Resource Identifier
        :type resID: str
        :return:
        """
        raise NotImplementedError