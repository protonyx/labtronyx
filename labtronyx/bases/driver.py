import logging

from labtronyx.common.plugin import PluginBase

class Base_Driver(PluginBase):
    """
    Driver Base Class
    """
    
    info = {}
    
    def __init__(self, resource, **kwargs):
        """
        :param resource: Reference to the associated resource instance
        :type resource: object
        """
        PluginBase.__init__(self)

        self._resource = resource

        self.logger = kwargs.get('logger', logging)

        # Instance variables
        self._name = self.__class__.__module__ + '.' + self.__class__.__name__

    def __getattr__(self, name):
        if hasattr(self._resource, name):
            return getattr(self._resource, name)
        else:
            raise AttributeError

    @property
    def resource(self):
        return self._resource

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
            
    # ===========================================================================
    # Optional Functions
    # ===========================================================================
        
    def open(self):
        """
        Prepare the device to receive commands. Called after the resource is opened, so any calls to resource functions
        should work.

        This function can be used to configure the device for remote control, reset the device, etc.
        """
        return True
    
    def close(self):
        """
        Prepare the device to close. Called before the resource is closed, so any calls to resource functions should
        work.
        """
        return True
    
    def getProperties(self):
        return {}