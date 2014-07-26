# Python Dependencies
import os, sys
import time
import socket
import uuid
import importlib, inspect
import logging, logging.handlers

import rpc

sys.path.append("..")

class InstrumentManager(rpc.RpcBase):
    """
    InstrumentManager manages controllers and instruments (models)
    
    Since InstrumentManagers tend to lock system resources, only one should be 
    running at a time. If an attempt is made to start the manager RPC server, 
    and the port is already locked, it will fail right away, assuming that an 
    instance of InstrumentManager is already running on the system. In this 
    case, InstrumentControl provides an easy way to connect to a running 
    manager instance using an RPC client.
    
    Controllers are like interfaces. They dictate how to talk to devices.
    
    Models are like drivers, and devices are instances of a model
    
    Methods that are generally useful and will be used the most:
    -getResources
    -loadDevice
    -unloadDevice
    -scan
    
    To identify a model to load we need:
    - Vendor
    - Product ID (Usually a model number)
    - Controller (models must specify compatible controllers)
    
    When a model is loaded, it is provided:
    - A reference to the controller object
    - A ResourceID to govern communications to the controller
    """
    
    VERSION = '0.1dev'
    
    models = {} # Lookup table of available model drivers
    
    controllers = {} # Controller name -> controller object
    resources = {} # UUID -> (Controller, ResID)
    devices = {} # UUID -> model object
        
    def __loadConfig(self, configFile):
        # Get the root path
        can_path = os.path.dirname(os.path.realpath(__file__)) # Resolves symbolic links
        rootPath = os.path.abspath(os.path.join(can_path, os.pardir))
        configPath = os.path.join(rootPath, 'config')
        configFile = os.path.join(configPath, 'default.py')
        
        try:
            import imp
            cFile = imp.load_source('default', configFile)
            self.config = cFile.Config()
            
        except Exception as e:
            print("FATAL ERROR: Unable to import config file")
            sys.exit()
            
        # Set the root path
        self.config.rootPath = rootPath
        
        # Set the version as a global variable
        self.config.version = self.VERSION
        
    def __configureLogger(self):
        self.logger = logging.getLogger(__name__)
        formatter = logging.Formatter(self.config.logFormat)
                
         # Configure logging level
        self.logger.setLevel(self.config.logLevel_console)
            
        # Logging Handler configuration, only done once
        if self.logger.handlers == []:
            # Console Log Handler
            lh_console = logging.StreamHandler(sys.stdout)
            lh_console.setFormatter(formatter)
            lh_console.setLevel(self.config.logLevel_console)
            self.logger.addHandler(lh_console)
            
            # File Log Handler
            if self.config.logToFile:
                if not os.path.exists(self.config.logPath):
                    os.makedirs(self.config.logPath)
                
                self.logFilename = os.path.normpath(os.path.join(self.config.logPath, 'InstrControl_Manager.log'))
                #===============================================================
                # if self.config.logFilename == None:
                #     self.logFilename = os.path.normpath(os.path.join(self.config.logPath, 'InstrControl_Manager.log'))
                # else:
                #     self.logFilename = os.path.normpath(os.path.join(self.config.logPath, self.config.logFilename))
                #===============================================================
                    
                fh = logging.handlers.RotatingFileHandler(self.logFilename, backupCount=self.config.logBackups)
                fh.setLevel(self.config.logLevel_file)
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)  
                fh.doRollover()
    
    def __loadControllers(self):
        """
        Scan the controllers folder and instantiate each controller found
        
        Care should be taken in invoking this method, it will release all 
        currently loaded controllers, which will subsequently close and release 
        all currently loaded models. Perhaps this should only be allowed
        to run when no models are running...
        
        This function should only be run on startup
        
        """
        self.logger.info("Loading Controllers...")
        
        # Clear the controller dictionary to free resources
        self.controllers = {}
        
        # Scan for controllers
        cont_dir = os.path.join(self.config.rootPath, 'controllers')
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
                            
                            testModule = importlib.import_module(contModule)
                            try:
                                # Instantiate the controller with a link to the model dictionary
                                testClass = getattr(testModule, className)(models=self.models[className], logger=self.logger)
                                
                                if testClass._open():
                                    self.controllers[className] = testClass
                            
                            except KeyError:
                                # No models loaded have support for that controller
                                pass
                            except AttributeError:
                                self.logger.error('Controller %s does not have a class %s', contModule, className)
                            except:
                                self.logger.exception("Failed to load controller: %s" % contModule)
                                
                
    def __loadModels(self):
        """
        Scan models folder and build a lookup table for each device model, since this does not
        instantiate any of the models, it can be done even if devices are open.
        
        Models: { Controller -> { VendorID -> { (moduleName, className) -> [ ProductID ] } } }
        """
        self.logger.info('Loading Models...')
        # Clear the model map dictionary
        self.models = {} 
        
        # Build model map dictionary
        model_dir = os.path.join(self.config.rootPath, 'models')
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
                    
                    except Exception as e:
                        self.logger.error('Unable to load module %s: %s', modelModule, str(e))
                        continue
                    
                    #===========================================================
                    # except AttributeError:
                    #     self.logger.error('Model %s does not have a class %s', modelModule, className)
                    #     continue
                    #===========================================================
                        
                    # Verify the model
                    try:
                        # Instantiate without calling __init__()
                        # TODO: Perhaps this should be done with inspect
                        #=======================================================
                        # class Empty(object):
                        #     pass
                        # instClass = Empty()
                        # instClass.__class__ = testClass
                        #=======================================================
                        
                        validControllers = testClass.validControllers
                        validVIDs = testClass.validVIDs
                        validPIDs = testClass.validPIDs
                        
                        for cont in validControllers:
                            if cont not in self.models:
                                self.models[cont] = {}
                                
                            for vid in validVIDs:
                                if vid not in self.models[cont]:
                                    self.models[cont][vid] = {}
                                    
                                moduleInfo = (modelModule, className)
                                    
                                self.models[cont][vid][moduleInfo] = validPIDs
                                
                    except Exception as e:
                        self.logger.error('Unable to load module %s: %s', modelModule, str(e))
                        continue
                                
    def __pathToModelName(self, path):
        # Get module name from relative path
        com_pre = os.path.commonprefix([self.config.rootPath, path])
        r_path = path.replace(com_pre + "\\", '')
        
        modulePath = r_path.replace("\\", '.')
        return modulePath

    def run(self):
        """
        Manager startup routine
        """
        # Load the config file
        self.__loadConfig('default')
        
        # Make sure another manager is not running
        if not self.rpc_test(port=self.config.managerPort):
            
            # Configure RPC Identity
            self._setHELOResponse('InstrumentManager/%s' % self.VERSION)

            # Configure Logger
            self.__configureLogger()
            
            self.logger.info("Instrument Manager Started")
            self.logger.info("Version: %s", self.VERSION)
            
            # Build the model dictionary
            self.__loadModels()
            
            # Load controllers
            self.__loadControllers()
            
            # Scan devices
            self.refresh()
            
            # Start RPC server
            # This operation will timeout after 2 seconds. If that happens,
            # this process should exit
            self.logger.info("Starting RPC Server...")
            self.rpc_start(port=self.config.managerPort)
                
            try:
                if self.is_alive():
                    # Running as a subprocess
                    # Spin to keep the process running, otherwise the interpreter
                    # will stop, even with the rpc server running in the background
                    while self.rpc_isRunning():
                        # Do something to keep process alive
                        time.sleep(1.0)
                        
            except:
                pass
                
        #=======================================================================
        # elif self.e_startedAsProcess:
        #     # If another instance was running, this process will die
        #     sys.exit()
        #     
        # while self.rpc_isRunning():
        #     # Stay alive!
        #     time.sleep(1.0)
        # 
        # if self.e_startedAsProcess:
        #     sys.exit()
        #=======================================================================
        
    def getProperties(self):
        """
        return the properties dictionary for Instrument Manager
        """
        pass
        
    #===========================================================================
    # Mass Controller Operations
    #===========================================================================
    
    def getControllers(self):
        """
        Get a list of loaded controllers
        """
        return self.controllers.keys()
    
    def getResources(self, controller=None, **kwargs):
        """
        Returns a list of resources in one or all controllers
        """
        return self.resources
        #=======================================================================
        # ret = {}
        # 
        # if controller is None:
        #     for c_name in self.controllers:
        #         res = self.getResources(c_name)
        #         
        #         if type(res) == dict:
        #             ret.update(res)
        #         
        # elif controller in self.controllers.keys():
        #     c_obj = self.controllers.get(controller)
        #     
        #     return c_obj.getResources()
        # 
        # return ret
        #=======================================================================
    
    def getResourceModelName(self, res_uuid):
        """
        Returns a dictionary of model names for all resources
        
        If a resource does not have a model loaded, the value will be None
        """
        dev = self.devices.get(res_uuid, None)
        
        if dev is not None:
            return dev.getModelName()
            
        else:
            return None
    
    def getResourcePort(self, res_uuid):
        """
        Get the port number for a 
        """
        dev = self.devices.get(res_uuid, None)
        
        if dev is not None:
            # Start the RPC server if it isn't already started
            # TODO: Should the RPC server be started explicitly?
            try:
                if dev.rpc_start():
                    return dev.rpc_getPort()
            
            except:
                pass

        return None
    
    def scan(self):
        """
        1. Refreshes all controller resources
        2. Orphaned models will be marked as dead
        3. Attempt to load models for new resources
        """
        pass
    
    def refresh(self, controller=None):
        """
        Iterate through all open controllers and refresh all resources
        """
        if len(self.controllers) == 0:
            self.logger.error("No controllers are initialized")
            
        elif controller is None:
            self.logger.info("Refreshing resources...")
            
            for c_name in self.controllers:
                self.refresh(c_name)
                
            self.logger.info("Refresh finished")
            
        elif controller in self.controllers.keys():
                self.logger.debug('Refreshing %s', controller)
                c_obj = self.controllers.get(controller)
                
                try:
                    c_obj.refresh()
                    
                    # Housekeeping
                    # Resources: { UUID -> (Controller, ResID) }
                    new_res = c_obj.getResources() # { ResID -> (VID, PID) }
                    
                    # Create new resources
                    for resID, resTup in new_res.items():
                        int_res_id = (controller, resID)
                        
                        if int_res_id not in self.resources.values():
                            new_uuid = str(uuid.uuid4())
                            self.logger.debug('Res: %s Assigned UUID: %s', resID, new_uuid)
                            
                            self.resources[new_uuid] = int_res_id
                            (VID, PID) = resTup
                            
                            # Get a list of compatible models
                            validModels = self.getValidModels(controller, VID, PID)
                            
                            # Attempt to load a model
                            if type(validModels) is list and len(validModels) > 0:
                                # TODO: Intelligently load a model or fail if multiple valid models are found
                                moduleName, className = validModels[0] 
                                self.loadModel(new_uuid, moduleName, className)
                    
                    # Purge unavailable resources
                    # TODO: Should a model be unloaded if there are connections?
                    #       Should we be able to reconnect to an instrument later?
                    for res_uuid, res_tup in self.resources.items():
                        res_id = res_tup[1]
                        
                        if res_id not in new_res.keys():
                            self.unloadModel(res_uuid)
                            self.resources.pop(res_uuid)
                    
                except NotImplementedError:
                    pass
        
    #===========================================================================
    # Individual Controller Operations
    #
    # API Interfaces
    #===========================================================================
    
    def canEditResources(self, controller):
        if controller in self.controllers:
            try:
                return controller.canEditResources()
            
            except NotImplementedError:
                return False
    
    def addResource(self, controller, VID, PID):
       if controller in self.controllers:
            try:
                return controller.addResource(VID, PID)
            
            except NotImplementedError:
                return False
    
    def destroyResource(self, controller, ResUUID):
        if controller in self.controllers:
            try:
                return controller.destroyResource(ResUUID)
            
            except NotImplementedError:
                return False

    #===========================================================================
    # Model Operations
    #===========================================================================
    
    def getValidModels(self, controller, VID, PID):
        """
        Returns a list of models that are considered valid for a given resource
        
        Parameters:
        - Controller: str
        - VID: str
        - PID: str
        
        Returns:
        - ModelNames: list of tuples (ModuleName, ClassName)
        
        Models: { Controller -> { VendorID -> { modelName -> [ ProductID ] } } }
        """
        ret = []
        
        mod_cont = self.models.get(controller, {})
        mod_vid = mod_cont.get(VID, {})
        for moduleInfo, PID_List in mod_vid.items():
            if PID in PID_List:
                ret.append(moduleInfo)
            
        return ret
                
    
    def loadModel(self, uuid, modelName=None, className=None):
        """
        Attempts to automatically load a model given a resource UUID.
        
        If modelName is specified (must be a valid package reference), that
        model will be loaded without any kind of compatibility checking. If
        an exception is thrown, the model will not be loaded.
        
        Returns:
            True if success, False if failure
        """
        if uuid in self.resources.keys():
            (controller, resID) = self.resources.get(uuid)
            
            try:
                if modelName is None:
                    # Try to find a suitable model
                    # Get the controller object
                    cont_obj = self.controllers.get(controller)
                    
                    # Try to find a compatible model
                    (VID, PID) = cont_obj.getModelID(resID)
                    validModels = self.getValidModels(controller, VID, PID)
                    
                    if type(validModels) is list and len(validModels) == 1:
                        moduleName, className = validModels[0] 
                        loadModel(uuid, moduleName, className)
                        return True
                    
                    else:
                        # More than one valid model exists or none found
                        return False
                
                else:
                    # Check if the specified model is valid
                    testModule = importlib.import_module(modelName)
                    testClass = getattr(testModule, className)
                    
                    # Load the model and store it
                    cont_obj = self.controllers.get(controller, None)
                    model_obj = testClass(uuid, cont_obj, resID, logger=self.logger)
                    
                    try:
                        model_obj.onLoad()
            
                    except NotImplementedError:
                        pass
        
                    self.devices[uuid] = model_obj
                    self.logger.debug('Loaded model for %s', resID)
                    
                    return True
                
            except:
                self.logger.exception('Failed to load model for %s', resID)
                return False
                
        else:
            return False
            
        #=======================================================================
        #      
        #     else:
        #         self.logger.error("No VISA model could be found for %s", deviceModel)
        #          
        # except NotImplementedError:
        #     self.logger.error("A model call was attempted, but the function was not implemented as required. Check model: %s", moduleName) 
        #      
        # except AttributeError:
        #     self.logger.error("Model %s could not be instantiated", moduleName)
        #           
        # except KeyError:
        #     self.logger.exception("VISA Resources were opened incorrectly")
        #      
        # except:
        #     self.logger.exception("An unhandled exception occurred during VISA device enumeration")
        #      
        # return False
        #=======================================================================
    
    def unloadModel(self, uuid):
        """
        Unloads the model only, doesn't change anything about a resource
        """
        dev = self.devices.pop(uuid, None)
        
        if dev is not None:
            try:
                dev.onUnload()
            
            except NotImplementedError:
                pass
            
            self.logger.info('Unloaded model for UUID %s', uuid)
            
            del dev
            
            return True
        
        return False
    
if __name__ == "__main__":
    man = InstrumentManager()
    man.run()