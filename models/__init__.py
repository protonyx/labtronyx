"""
Test
"""

import common
import common.rpc

import sys
import importlib
import logging

import views

class m_Base(common.rpc.RpcBase, common.IC_Common):
    
    deviceType = 'Generic'
    view = None
    
    # Model Lookup
    validControllers = []
    validVIDs = []
    validPIDs = []
    
    def __init__(self, uuid, controller, resID, VID, PID, **kwargs):
        common.rpc.RpcBase.__init__(self)
        common.IC_Common.__init__(self, **kwargs)
        
        self.uuid = uuid
        self.controller = controller
        self.resID = resID
        self.VID = VID
        self.PID = PID
        
        # Check for logger
        self.logger = kwargs.get('Logger', logging)
            
    #===========================================================================
    # Virtual Functions
    #===========================================================================
        
    def _onLoad(self):
        """
        Called shortly after a Model is instantiated. Since Models can be run
        in a new thread, all member attributes in __init__ must be pickleable.
        If there are attributes that cannot be picked, load them here.
        """
        raise NotImplementedError
    
    def _onUnload(self):
        """
        Called when a Model is unloaded by the InstrumentManager. After this
        function is called, all reference will be nulled, and the object will
        be marked for Garbage Collection. This function should ensure that no
        object references are orphaned.
        """
        raise NotImplementedError
    
    #===========================================================================
    # Inherited Functions
    #===========================================================================
    
    def getModelName(self):
        """
        Returns the Model class name
        
        :returns: str
        """
        return self.__class__.__name__
    
    def getUUID(self):
        """
        Returns the Resource UUID that is provided to the Model
        
        :returns: str
        """
        return self.uuid
    
    def getControllerName(self):
        """
        Returns the Model's Controller class name
        
        :returns: str
        """
        return self.controller.getControllerName()
    
    def getResourceID(self):
        """
        Returns the Model Resource ID that identifies the resource to the
        Controller
        
        :returns: str
        """
        return self.resID

    def getVendorID(self):
        return ''
    
    def getProductID(self):
        return ''
    
    def getProperties(self):
        return {}
