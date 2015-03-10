import uuid
import time
import threading
import importlib
import sys

import common
import common.rpc as rpc

class Base_Resource(object):
    type = "Generic"
    
    def __init__(self, resID, interface, **kwargs):
        
        common_globals = common.ICF_Common()
        self.config = common_globals.getConfig()
        self.logger = common_globals.getLogger()
        
        self.__uuid = str(uuid.uuid4())
        self.__resID = resID
        self.__interface = interface
        self.__groupTag = kwargs.get('groupTag', '')
        self.__status = 'INIT'
        
        self.driver = None
        
        # Start RPC Server
        self.rpc_server = rpc.RpcServer(name='%s-%s' % (interface.getInterfaceName(), resID),
                                        logger=self.logger)
        self.rpc_server.registerObject(self)
        
    def getUUID(self):
        return self.__uuid
    
    def getResourceID(self):
        return self.__resID
    
    def getGroupTag(self):
        return self.__groupTag
    
    def getResourceType(self):
        return self.type
    
    def getResourceStatus(self):
        return self.__status
    
    def setResourceStatus(self, new_status):
        self.__status = new_status
        
        self.rpc_server.notifyClients('event_status_change')
    
    def getInterfaceName(self):
        """
        Returns the Resource's Controller class name
        
        :returns: str
        """
        return self.__interface.getInterfaceName()
    
    def getPort(self):
        # Start the RPC server if it isn't already started
        if self.rpc_server.rpc_isRunning():
            return self.rpc_server.rpc_getPort()
    
    def getProperties(self):
        res_prop = {
            'uuid': self.getUUID(),
            'interface': self.getInterfaceName(),
            'resourceID': self.getResourceID(),
            'resourceType': self.getResourceType(),
            'groupTag': self.getGroupTag(),
            'status': self.getResourceStatus(),
            'port': self.getPort()
            }
        
        # Append Model properties if a Model is loaded
        if self.driver is not None:
            driver_prop = self.driver.getProperties()
            
            driver_prop['driver'] = self.driver.getDriverName()
            
            res_prop.update(driver_prop)
        
        return res_prop
    
    #===========================================================================
    # Resource State
    #===========================================================================
    
    def isOpen(self):
        raise NotImplementedError
        
    def open(self):
        """
        Open the resource
        
        :returns: True if open was successful, False otherwise
        """
        raise NotImplementedError
    
    def close(self):
        """
        Close the resource
        
        :returns: True if close was successful, False otherwise
        """
        raise NotImplementedError
    
    def lock(self):
        raise NotImplementedError
    
    def unlock(self):
        raise NotImplementedError
    
    #===========================================================================
    # Data Transmission
    #===========================================================================
    
    def write(self, data):
        raise NotImplementedError
    
    def read(self):
        raise NotImplementedError
    
    def query(self):
        raise NotImplementedError
    
    #===========================================================================
    # Models
    #===========================================================================
    
    def hasModel(self):
        return self.model is not None
    
    def loadModel(self, modelName):
        """
        Load a Model. A Model name can be specified to load a specific model,
        even if it may not be compatible with this resource. Reloads model
        when importing, in case an update has occured.
        
        Example::
        
            instr.loadModel('Tektronix.Oscilloscope.m_DigitalPhosphor')
        
        :param modelName: Module name of the desired Model
        :type modelName: str
        :returns: True if successful, False otherwise
        """
        try:
            # Check if the specified model is valid
            testModule = importlib.import_module(modelName)
            reload(testModule) # Reload the module in case anything has changed
            
            className = modelName.split('.')[-1]
            testClass = getattr(testModule, className)
            
            self.model = testClass(self)
            self.model._onLoad()
            
            # RPC register object
            self.rpc_server.registerObject(self.model)
            self.rpc_server.notifyClients('event_model_loaded')
            
            return True

        except:

            self.logger.exception('Failed to load model: %s', modelName)
            return False
    
    def unloadModel(self):
        """
        If a Model is currently loaded for the resource, unload the resource.
        
        :returns: True if successful, False otherwise
        """
        if self.model is not None:
            try:
                self.model._onUnload()
                # RPC unregister object
                
                self.rpc_server.unregisterObject(self.model)
                self.rpc_server.notifyClients('event_model_unloaded')
                
            except:
                self.logger.exception('Exception while unloading model')
                
            del self.model
            self.model = None
                
            return True
        
        else:
            return False
