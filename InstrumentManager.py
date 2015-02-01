# Python Dependencies
import os, sys
import time
import socket
import uuid
import copy
import importlib, inspect
import logging, logging.handlers

import common
import common.rpc as rpc

class InstrumentManager(rpc.RpcBase):
    
    models = {} # Module name -> Model info
    
    controllers = {} # Controller name -> controller object
    
    resources = {} # UUID -> Resource Object
    properties = {} # UUID -> Property Dictionary
    
    def __loadControllers(self):
        """
        Scan the controllers folder and instantiate each controller found
        
        This function is only run on startup
        """
        self.logger.info("Loading Controllers...")
        
        # Clear the controller dictionary to free resources
        self.controllers = {}
        
        # Scan for controllers
        cont_dir = os.path.join(self.rootPath, 'controllers')
        allcont = os.walk(cont_dir)
        for dir in allcont:
            if len(dir[2]) > 0:
                # Directory is not empty
                if '__init__.py' in dir[2]: # Must be a module
                    for file in dir[2]:
                        # Iterate through each file
                        if file[-3:] == '.py' and '__init__' not in file:
                            # Instantiate each controller and add to controller list
                            # Get relative path
                            className = file.replace('.py', '')
                            
                            # Get module name from relative path
                            contModule = self.__pathToModelName(dir[0]) + '.' + className
                            
                            self.logger.debug('Loading controller: %s', contModule)
                            
                            try:
                                # Attempt to import the controller module
                                testModule = importlib.import_module(contModule)
                                
                                # Instantiate the controller with a link to the model dictionary
                                testClass = getattr(testModule, className)(self)
                                
                                if testClass.open() == True:
                                    self.controllers[className] = testClass
                                    
                                else:
                                    self.logger.warning('Controller %s failed to initialize', contModule)
                                    testClass.close()
                    
                            except AttributeError as e:
                                self.logger.error('Controller %s does not have a class %s', contModule, className)
                                
                            except Exception as e:
                                self.logger.exception("Unable to load controller %s: %s", contModule, str(e))
                                
                
    def __loadModels(self):
        # Clear the model map dictionary
        self.models.clear()
        
        # Build model map dictionary
        model_dir = os.path.join(self.rootPath, 'models')
        allmodels = os.walk(model_dir)
        for dir in allmodels:
            # Verify valid directory
            if len(dir[2]) == 0:
                # Directory is empty, move on
                continue
            
            elif '__init__.py' not in dir[2]:
                # Directory must be a python module
                # TODO: Create an __init__.py file if one does not exist
                self.logger.warning('Non-module model found: %s', dir[0])
                continue
            
            for file in dir[2]:
                # Iterate through each file
                if file[-3:] == '.py' and '__init__' not in file:
                    # Get module name from relative path     
                    className = file.replace('.py', '')
                    modelModule = self.__pathToModelName(dir[0]) + '.' + className

                    # Attempt to load the model
                    try:
                        testModule = importlib.import_module(modelModule)
                        self.logger.debug('Loading model: %s', modelModule)
                        
                        # Check to make sure the correct class exists
                        testClass = getattr(testModule, className) # Will raise exception if doesn't exist
                        
                        model_info = copy.deepcopy(testClass.info)
                        self.models[modelModule] = model_info
                    
                    except Exception as e:
                        self.logger.exception('Unable to load model %s: %s', modelModule, str(e))
                        continue
                    
                    #===========================================================
                    # except AttributeError:
                    #     self.logger.error('Model %s does not have a class %s', modelModule, className)
                    #     continue
                    #===========================================================
                                
    def __pathToModelName(self, path):
        # Get module name from relative path
        com_pre = os.path.commonprefix([self.rootPath, path])
        r_path = path.replace(com_pre + os.path.sep, '')
        
        modulePath = r_path.replace(os.path.sep, '.')
        return modulePath
    
    def _notify_new_resource(self):
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

    def _run(self):
        """
        Main InstrumentManager logic. Blocks until stopped.
        """
        common_globals = common.ICF_Common()
        self.rootPath = common_globals.getRootPath()
        self.config = common_globals.getConfig()
        self.logger = common_globals.getLogger()
        
        # Check command line arguments
        #=======================================================================
        # try:
        #     opts, args = getopt.getopt(sys.argv[1:], "d")
        #     for opt, arg in opts:
        #         if opt == "-d":
        #             self.logger.info("Starting in Debug mode")
        #             global _debug
        #             _debug = 1
        # except:
        #     pass
        #=======================================================================
        
        # Make sure another manager is not running
        if not self.rpc_test(port=self.config.managerPort):
            
            # Configure RPC Identity
            self._setHELOResponse('InstrumentManager/%s' % self.config.version)
            
            self.logger.info("Instrument Manager Started")
            self.logger.info("Version: %s", self.config.version)
            
            # Build the model dictionary
            self.__loadModels()
            
            #from pprint import pprint
            #pprint(self.models)
            
            # Load controllers
            self.__loadControllers()
            
            # Start RPC server
            # This operation will timeout after 2 seconds. If that happens,
            # this process should exit
            self.logger.info("Starting RPC Server...")
            self.rpc_start(port=self.config.managerPort)
            
            # Main thread will now close
            # TODO: Should the main thread be doing something?
            
    def stop(self):
        """
        Stop the InstrumentManager instance. Attempts to shutdown and free
        all resources.
        """
        for dev in self.devices.values():
            if hasattr(dev, 'rpc_stop'):
                dev.rpc_stop()
                
        for cont in self.controllers.values():
            cont.close()
                
        self.rpc_stop()
            
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
        pass
    
    def disableController(self, controller):
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
                
                self.properties[res_uuid].setdefault('deviceType', 'Generic')
                self.properties[res_uuid].setdefault('deviceVendor', 'Generic')
                self.properties[res_uuid].setdefault('deviceModel', 'Device')
                self.properties[res_uuid].setdefault('deviceSerial', 'Unknown')
                self.properties[res_uuid].setdefault('deviceFirmware', 'Unknown')
                
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
    
    def destroyResource(self, controller, res_uuid):
        """
        Manually destroy a resource within a controller
        
        .. note::
        
            This will return False if manually destroying resources is not supported.
            To check if the controller supports manual resource management,
            use :func:`InstrumentManager.canEditResources`
        
        :param controller: Controller name
        :type controller: str
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: bool - True if successful, False otherwise
        """
        if controller in self.controllers:
            try:
                return controller.destroyResource(res_uuid)
            
            except NotImplementedError:
                return False

    #===========================================================================
    # Model Operations
    #===========================================================================
                
    def getModels(self):
        return self.models
    
if __name__ == "__main__":
    # If InstrumentManager is run in interactive mode, just call run
    man = InstrumentManager()
    man._run()