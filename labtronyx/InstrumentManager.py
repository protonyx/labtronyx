import os, sys
import time
import socket
import uuid
import copy
import importlib, inspect
import logging, logging.handlers

class InstrumentManager(object):
    
    drivers = {} # Module name -> Model info

    interfaces = {} # Controller name -> controller object
    resources = {} # UUID -> Resource Object
    properties = {} # UUID -> Property Dictionary
    
    def __init__(self):
        self.rootPath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir)))
        
        if not self.rootPath in sys.path:
            sys.path.append(self.rootPath)
        
        import common
        common_globals = common.ICF_Common()
        self.config = common_globals.getConfig()
        self.logger = common_globals.getLogger()
        
        self.logger.info(self.config.longname)
        self.logger.info("InstrumentManager, Version: %s", self.config.version)
        
        try:
            import common.rpc as rpc
            self.rpc_server = rpc.RpcServer(name='InstrumentManager-RPC-Server', 
                                            port=self.config.managerPort,
                                            logger=self.logger)
            self.rpc_server.registerObject(self)
            
            # Load Interfaces
            import interfaces
            interface_info = interfaces.getAllInterfaces()
            
            for interf in interface_info.keys():
                self.logger.debug("Found Interface: %s", interf)
                self.enableInterface(interf)
        
            # Load Drivers
            import drivers
            self.drivers = drivers.getAllDrivers()
            
            for driver in self.drivers.keys():
                self.logger.debug("Found Driver: %s", driver)
            
            
            
        except rpc.RpcServerPortInUse:
            self.logger.error("RPC Port in use, shutting down...")
    

    def _cb_new_resource(self):
        """
        Notify InstrumentManager of the creation of a new resource. Called by
        controllers
        """
        for interface in self.interfaces.values():
            int_res = interface.getResources()
            for resID, res_obj in int_res.items():
            
                res_uuid = res_obj.getUUID()
        
                if res_uuid not in self.resources:
                    self.resources[res_uuid] = res_obj
                    
                    self.refreshResources()
                    
        self.rpc_server.notifyClients('event_new_resource')

    def stop(self):
        """
        Stop the InstrumentManager instance. Attempts to shutdown and free
        all resources.
        """
        for res in self.resources:
            try:
                res.close()
            except:
                pass
                
        for interface in self.interfaces:
            self.disableInterface(interface)
                
        # Stop the InstrumentManager RPC Server
        self.rpc_server.rpc_stop()
            
    def getVersion(self):
        """
        Get the InstrumentManager version
        
        :returns: str
        """
        return self.config.version
        
    #===========================================================================
    # Interface Operations
    #===========================================================================
    
    def getInterfaces(self):
        """
        Get a list of controllers known to InstrumentManager
        
        :returns: list
        """
        return self.interfaces.keys()
    
    def enableInterface(self, interface):
        if interface not in self.interfaces:
            try:
                interfaceModule = importlib.import_module(interface)
                className = interface.split('.')[-1]
                interfaceClass = getattr(interfaceModule, className)
                inter = interfaceClass(self)
                inter.open()
                self.logger.info("Started Interface: %s" % interface)
                self.interfaces[interface] = inter
            except:
                self.logger.exception("Exception during interface open")
                
        else:
            raise RuntimeError("Interface is already running!")
    
    def disableInterface(self, interface):
        if interface in self.interfaces:
            try:
                inter = self.interfaces.get(interface)
                inter.close()
                self.logger.info("Stopped Interface: %s" % interface)
                self.interfaces.remove(inter)
            except:
                self.logger.exception("Exception during interface close")
                
        else:
            raise RuntimeError("Interface is not running!")
        
    #===========================================================================
    # Resource Operations
    #===========================================================================
    
    def getResources(self, res_uuid=None):
        """
        Get information about all resources. If Resource UUID is provided, a
        dictionary with all resources will be returned, nested by UUID
        
        :param res_uuid: Unique Resource Identifier (UUID) (Optional)
        :type res_uuid: str
        :returns: dict
        """
        if res_uuid is None:
            return self.properties
        
        else:
            return self.properties.get(res_uuid, {})
    
    def refreshResources(self):
        """
        Refresh the properties dictionary for all resources.
        
        :returns: True if successful, False if an error occured
        """
        try:
            for res_uuid, res in self.resources.items():
                self.properties[res_uuid] = res.getProperties()
                
                self.properties[res_uuid].setdefault('deviceType', '')
                self.properties[res_uuid].setdefault('deviceVendor', '')
                self.properties[res_uuid].setdefault('deviceModel', '')
                self.properties[res_uuid].setdefault('deviceSerial', '')
                self.properties[res_uuid].setdefault('deviceFirmware', '')
                
            return True
        
        except:
            self.logger.exception("Unhandled exception while refreshing resources")
            return False
    
    def addResource(self, controller, ResID):
        """
        Manually add a resource to a controller. Not supported by all controllers
        
        .. note::
        
            This will return False if manually adding resources is not supported.
            To check if the controller supports manual resource management,
            use :func:`InstrumentManager.canEditResources`
        
        :param controller: Controller name
        :type controller: str
        :param ResID: Resource Identifier
        :type ResID: str
        :returns: bool - True if successful, False otherwise
        """
        if interface in self.interfaces:
            try:
                int_obj = self.interfaces.get(interface)
                return int_obj.addResource(ResID)
            
            except NotImplementedError:
                return False
            
            except AttributeError:
                return False
        
        return False

    #===========================================================================
    # Driver Operations
    #===========================================================================
                
    def getDrivers(self):
        return self.drivers
    
if __name__ == "__main__":
    # If InstrumentManager is run in interactive mode, just call run
    man = InstrumentManager()