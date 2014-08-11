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
    
    def __init__(self, uuid, controller, resID, **kwargs):
        common.rpc.RpcBase.__init__(self)
        common.IC_Common.__init__(self, **kwargs)
        
        self.uuid = uuid
        self.controller = controller
        self.resID = resID
        
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
        return self.__class__.__name__

    def getIdentity(self):
        """
        Returns the Model identity information that is assigned when the
        InstrumentManager loads the Model and attaches it to a resource
        
        :returns: tuple - (Resource UUID, Controller Name, Resource ID)
        """
        return (self.uuid, self.controller.getControllerName(), self.resID)
    
    def getProperties(self):
        return { 'uuid': self.uuid,
                 'controller': self.controller.getControllerName(),
                 'resourceID': self.resID,
                 'modelName': self.getModelName(),
                 'port': self.rpc_getPort(),
                 'deviceType': self.deviceType,
                 'deviceVendor': 'Generic',
                 'deviceModel': 'Device',
                 'deviceSerial': 'Unknown',
                 'deviceFirmware': 'Unknown'
                }


