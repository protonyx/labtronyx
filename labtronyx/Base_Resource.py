import uuid
import time
import threading
import importlib
import sys
import socket

import common
import common.rpc as rpc

import common.resource_status as resource_status

class Base_Resource(object):
    type = "Generic"
    
    def __init__(self, resID, interface, **kwargs):
        
        self.config = kwargs.get('config')
        self.logger = kwargs.get('logger')
        
        self.__uuid = str(uuid.uuid4())
        self.__resID = resID
        self.__interface = interface
        self.__groupTag = kwargs.get('groupTag', '')
        self.__status = 'INIT'
        
        self.__lock = None
        
        self.driver = None
        
        if kwargs.get('enableRpc', True):
            self.start()
            
    def __del__(self):
        self.stop()
        
    def __getattr__(self, name):
        if self.driver is not None:
            if hasattr(self.driver, name):
                return getattr(self.driver, name)
            else:
                raise AttributeError
            
        else:
            raise AttributeError
        
    def start(self):
        """
        Start the RPC Server
        """
        self.rpc_server = rpc.RpcServer(name='RPC-%s' % (self.__resID),
                                        logger=self.logger)
        self.rpc_server.registerObject(self)
        
    def stop(self):
        """
        Stop the RPC Server
        """
        if hasattr(self, 'rpc_server'):
            self.rpc_server.rpc_stop()
        
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
        
        if hasattr(self, 'rpc_server'):
            self.rpc_server.notifyClients('event_status_change')
        
    def getResourceError(self):
        return self.__error
    
    def setResourceError(self, error):
        self.__error = error
        
        if hasattr(self, 'rpc_server'):
            self.rpc_server.notifyClients('event_resource_error')
    
    def getInterfaceName(self):
        """
        Returns the Resource's Controller class name
        
        :returns: str
        """
        return self.__interface.getInterfaceName()
    
    def getPort(self):
        # Start the RPC server if it isn't already started
        if hasattr(self, 'rpc_server') and self.rpc_server.rpc_isRunning():
            return self.rpc_server.rpc_getPort()
    
    def getProperties(self):
        driver_prop = {}
        
        # Append Driver properties if a Driver is loaded
        if self.driver is not None:
            driver_prop = self.driver.getProperties()
            
            driver_prop['driver'] = self.driver.getDriverName()
        
        res_prop = {
            'uuid': self.getUUID(),
            'interface': self.getInterfaceName(),
            'resourceID': self.getResourceID(),
            'resourceType': self.getResourceType(),
            'groupTag': self.getGroupTag(),
            'status': self.getResourceStatus()
            }
        
        if hasattr(self, 'rpc_server') and self.rpc_server.rpc_isRunning():
            res_prop['address'] = socket.gethostbyname(socket.gethostname())
            res_prop['hostname'] = socket.gethostname()
            res_prop['port'] = self.rpc_server.rpc_getPort()
          
        driver_prop.update(res_prop)
        
        return driver_prop
    
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
    
    def checkResourceStatus(self):
        """
        Raise an error if the resource is not ready. Used in resources that
        sub-class Base_Resource to prevent attempted data transfer when the
        resource is in a bad state.
        
        :raises: common.resource_status.ResourceNotReady()
        """
        if self.getResourceStatus() != resource_status.READY:
            raise resource_status.ResourceNotReady()
        
    def refresh(self):
        """
        Refresh the resource
        """
        raise NotImplementedError
    
    #===========================================================================
    # Data Transmission
    #===========================================================================
    
    def write(self, data):
        raise NotImplementedError
    
    def read(self):
        raise NotImplementedError
    
    def query(self, data):
        raise NotImplementedError

    #===========================================================================
    # Driver
    #===========================================================================
    
    def hasDriver(self):
        return self.driver is not None
    
    def loadDriver(self, driverName):
        """
        Load a Driver for a resource. A driver name can be specified to load a 
        specific module, even if it may not be compatible with this resource. 
        Reloads driver when importing, in case an update has occured.
        
        Example::
        
            instr.loadDriver('Tektronix.Oscilloscope.m_DigitalPhosphor')
        
        :param driverName: Module name of the desired Model
        :type driverName: str
        :returns: True if successful, False otherwise
        """
        try:
            # Check if the specified model is valid
            testModule = importlib.import_module(driverName)
            reload(testModule) # Reload the module in case anything has changed
            
            className = driverName.split('.')[-1]
            testClass = getattr(testModule, className)
            
            self.driver = testClass(self, logger=self.logger, config=self.config)
            self.driver._onLoad()
            
            # RPC register object
            if hasattr(self, 'rpc_server'):
                self.rpc_server.registerObject(self.driver)
                self.rpc_server.notifyClients('event_driver_loaded')
            
            return True

        except:
            self.logger.exception('Failed to load driver: %s', driverName)
            
            self.unloadDriver()
            
            return False
    
    def unloadDriver(self):
        """
        If a Driver is currently loaded for the resource, unload it.
        
        :returns: True if successful, False otherwise
        """
        if self.driver is not None:
            try:
                self.driver._onUnload()
                
            except:
                self.logger.exception('Exception while unloading driver')
                
            # RPC unregister object    
            if hasattr(self, 'rpc_server'):
                self.rpc_server.unregisterObject(self.driver)
                self.rpc_server.notifyClients('event_driver_unloaded')
                
            del self.driver
            self.driver = None
            
            try:
                self.close()
            except:
                pass
                
            return True
        
        else:
            return False

class ResourceNotOpen(RuntimeError):
    pass
