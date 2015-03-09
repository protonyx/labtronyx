# Python Dependencies
import os, sys
import time
import socket
import uuid
import copy
import importlib, inspect
import logging, logging.handlers

sys.path.append("..")
import common
import common.rpc as rpc

sys.path.append(".")
import models
import controllers

class InstrumentManager(object):
    
    models = {} # Module name -> Model info
    
    controllers = {} # Controller name -> controller object
    resources = {} # UUID -> Resource Object
    properties = {} # UUID -> Property Dictionary
    
    def __init__(self):
        common_globals = common.ICF_Common()
        self.rootPath = common_globals.getRootPath()
        self.config = common_globals.getConfig()
        self.logger = common_globals.getLogger()
        
        self.logger.info("Instrument Control and Automation Framework")
        self.logger.info("InstrumentManager, Version: %s", self.config.version)
        
        try:
            self.rpc_server = rpc.RpcServer(name='InstrumentManager-RPC-Server', 
                                            port=self.config.managerPort,
                                            logger=self.logger)
            self.rpc_server.registerObject(self)
            
            # Load Interfaces
            self.interfaces = controllers.getAllInterfaces()
            
            for interf in self.interfaces.keys():
                self.logger.debug("Found Interface: %s", interf)
        
            # Load Drivers
            self.drivers = models.getAllDrivers()
            
            for driver in self.drivers.keys():
                self.logger.debug("Found Driver: %s", driver)
            
            
            
        except rpc.RpcServerPortInUse:
            self.logger.error("RPC Port in use, shutting down...")
    

    def _cb_new_resource(self):
        """
        Notify InstrumentManager of the creation of a new resource. Called by
        controllers
        """
        for cont in self.controllers.values():
            cont_res = cont.getResources()
            for resID, res_obj in cont_res.items():
            
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
                
        for cont in self.controllers:
            try:
                cont.close()
            except:
                pass
                
        # Stop the InstrumentManager RPC Server
        self.rpc_server.rpc_stop()
            
    def getVersion(self):
        """
        Get the InstrumentManager version
        
        :returns: str
        """
        return self.config.version
        
    #===========================================================================
    # Controller Operations
    #===========================================================================
    
    def getControllers(self):
        """
        Get a list of controllers known to InstrumentManager
        
        :returns: list
        """
        return self.controllers.keys()
    
    def enableController(self, controller):
        # TODO: Implement this
        pass
    
    def disableController(self, controller):
        # TODO: Implement this
        pass
        
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
        if controller in self.controllers:
            try:
                cont_obj = self.controllers.get(controller)
                return cont_obj.addResource(ResID)
            
            except NotImplementedError:
                return False
            
            except AttributeError:
                return False
        
        return False

    #===========================================================================
    # Model Operations
    #===========================================================================
                
    def getModels(self):
        return self.models
    
if __name__ == "__main__":
    # If InstrumentManager is run in interactive mode, just call run
    man = InstrumentManager()