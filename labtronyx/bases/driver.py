import time
import threading

from labtronyx.common.plugin import PluginBase

class Base_Driver(PluginBase):
    """
    Driver Base Class
    """
    
    info = {}
    
    def __init__(self, resource, **kwargs):
        PluginBase.__init__(self)

        self._name = None
        self._resource = resource
        self.logger = kwargs.get('logger')

    def __getattr__(self, name):
        if hasattr(self._resource, name):
            return getattr(self._resource, name)
        else:
            raise AttributeError

    @property
    def resource(self):
        return self._resource

    def get_name(self):
        if self._name is None:
            return self.__class__.__module__ + '.' + self.__class__.__name__
        else:
            return self._name

    def set_name(self, value):
        self._name = value

    name = property(get_name, set_name)
            
    #===========================================================================
    # Virtual Functions
    #===========================================================================
        
    def open(self):
        """
        Prepare the device to receive commands. Called after the resource is opened, so any calls to resource functions
        should work.

        This function can be used to configure the device for remote control, reset the device, etc.
        """
        raise NotImplementedError
    
    def close(self):
        """
        Prepare the device to close. Called before the resource is closed, so any calls to resource functions should
        work.
        """
        raise NotImplementedError
    
    #===========================================================================
    # Inherited Functions
    #===========================================================================
    
    def getDriverName(self):
        """
        Returns the Driver class name
        
        :returns: str
        """
        fqn = self.__class__.__module__

        return fqn
    
        # Truncate class name from module
        #fqn_split = fqn.split('.')
        #return '.'.join(fqn_split[0:-1])
    
    def getResource(self):
        """
        Returns the resource object for interacting with the physical instrument
        
        :returns: object
        """
        return self._resource
    
    def getProperties(self):
        return {}
