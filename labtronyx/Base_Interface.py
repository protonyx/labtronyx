import uuid
import time
import threading
import importlib
import sys

import common
import common.rpc as rpc

class Base_Interface(object):
    """
    Interface Base Class
    """
    
    REFRESH_RATE = 1.0 # Seconds

    # TODO: Interface will have hooks into the persistence config to "remember" how
    #       a particular device is configured when the program is run in the future.
    
    def __init__(self, manager, **kwargs):
        """
        :param manager: Reference to the InstrumentManager instance
        :type manager: InstrumentManager object
        """
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')
        
        self.resources = {}
        self.manager = manager
        
        self.e_alive = threading.Event()
        self.e_alive.set()
            
        self.__interface_thread = threading.Thread(name=self.getInterfaceName(), target=self.run)
        self.__interface_thread.start()
        
    #===========================================================================
    # Interface Thread
    #===========================================================================
    
    def run(self):
        """
        Interface thread
        """
        while(self.e_alive.isSet()):
            
            self.refresh()
            
            time.sleep(self.REFRESH_RATE)
            
    def stop(self):
        self.e_alive.clear()
        self.__interface_thread.join()
            
    #===========================================================================
    # Interface Methods
    #===========================================================================

    def getInterfaceName(self):
        return self.__class__.__name__

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

    def getResources(self):
        """
        Get the dictionary of resources by ID.
        
        :returns: dict
        """
        raise NotImplementedError

    def refresh(self):
        """
        Refreshes the resource list. This function is called regularly by the
        controller thread.
        """
        raise NotImplementedError
    
    def addResource(self, ResID, VID, PID):
        """
        Manually add a resource to the controller
        
        :param ResID: Resource Identifier
        :type ResID: str
        :param VID: Vendor Identifier
        :type VID: str
        :param PID: Product Identifier
        :type PID: str
        :returns: bool - True if successful, False otherwise
        """
        raise NotImplementedError
    
    def destroyResource(self, ResID):
        """
        Remove a manually added resource
        
        :param ResID: Resource Identifier
        :type ResID: str
        :returns: bool - True if successful, False otherwise
        """
        raise NotImplementedError

class InterfaceError(RuntimeError):
    pass

class InterfaceTimeout(RuntimeError):
    pass
