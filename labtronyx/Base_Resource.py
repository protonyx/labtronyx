import uuid
import time
import threading
import importlib
import sys

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
        
        # Start RPC Server
        self.rpc_server = rpc.RpcServer(name='%s-%s' % (interface.getInterfaceName(), resID),
                                        logger=self.logger)
        self.rpc_server.registerObject(self)
        
    def __del__(self):
        self.killResource()
        
    def killResource(self):
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
        
        self.rpc_server.notifyClients('event_status_change')
        
    def getResourceError(self):
        return self.__error
    
    def setResourceError(self, error):
        self.__error = error
        
        self.rpc_server.notifyClients('event_resource_error')
    
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
        
        if self.rpc_server.rpc_isRunning():
            res_prop['address'] = self.rpc_server.rpc_getAddress()
            res_prop['hostname'] = self.rpc_server.rpc_getHostname()
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
    # Resource Locking
    #===========================================================================
    
    def lock(self):
        """
        Lock the resource for exclusive access to the IP Address of the active
        RPC connection
        
        :returns: True if successful, False otherwise
        """
        conn = self.rpc_server.getActiveConnection()
        
        if self.__lock == None:
            try:
                address, _ = self.conn.getsockname()
                self.__lock = address
                self.logger.debug("Connection [%s] aquired resource lock", address)
                return True
            except:
                return False
        
        else:
            return False
    
    def unlock(self):
        """
        Unlock the resource for general access. Must be called from the IP
        Address of the connection currently holding the lock.
        
        :returns: True if successful, False otherwise
        """
        conn = self.rpc_server.getActiveConnection()
        
        try:
            address, _ = self.conn.getsockname()
            
            if self.__lock == address:
                self.__lock = None
                self.logger.debug("Connection [%s] released resource lock", address)
                return True
        
            else:
                return False
        except:
            return False
        
    def force_unlock(self):
        """
        Force unlocks the resource even if called from an IP Address that does
        not hold the lock
        
        :returns: None
        """
        conn = self.rpc_server.getActiveConnection()
        self.__lock = None
        
        try:
            address, _ = self.conn.getsockname()
            self.logger.debug("Connection [%s] force released resource lock", address)
            
        except:
            pass
    
    def getLockAddress(self):
        """
        Get the IP Address of the connection currently holding the resource
        lock.
        
        :returns: str
        """
        return self.__lock
    
    def hasLock(self):
        """
        Query if the current connection holds the resource lock.
        
        :returns: bool
        """
        conn = self.rpc_server.getActiveConnection()
        
        try:
            address, _ = self.conn.getsockname()
            return (address == self.__lock)
        except:
            return False
    
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
            
            self.driver = testClass(self)
            self.driver._onLoad()
            
            # RPC register object
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
