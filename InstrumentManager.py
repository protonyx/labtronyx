# Python Dependencies
import os, sys
import time
import socket
import uuid
import importlib, inspect
import logging, logging.handlers

import common.rpc as rpc

class InstrumentManager(rpc.RpcBase):
    
    VERSION = '0.1dev'
    
    models = {} # Lookup table of available model drivers
    
    controllers = {} # Controller name -> controller object
    resources = {} # UUID -> (Controller, ResID, VID, PID)
    devices = {} # UUID -> model object
        
    def __loadConfig(self, configFile):
        # Get the root path
        can_path = os.path.dirname(os.path.realpath(__file__)) # Resolves symbolic links
        
        self.rootPath = os.path.abspath(can_path)
        self.configPath = os.path.join(self.rootPath, 'config')
        self.configFile = os.path.join(self.configPath, '%s.py' % configFile)
        
        try:
            import imp
            cFile = imp.load_source('config', self.configFile)
            self.config = cFile.Config()
            
        except Exception as e:
            print("FATAL ERROR: Unable to import config file")
            sys.exit()
        
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
        com_pre = os.path.commonprefix([self.rootPath, path])
        r_path = path.replace(com_pre + "\\", '')
        
        modulePath = r_path.replace("\\", '.')
        return modulePath

    def _run(self):
        """
        Main InstrumentManager logic. Blocks until stopped.
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
        
    def getProperties(self):
        """
        Get the properties dictionary for InstrumentManager
        
        :returns: dict
        """
        return {'Version': self.VERSION}
        
    #===========================================================================
    # Mass Controller Operations
    #===========================================================================
    
    def getControllers(self):
        """
        Get a list of controllers known to InstrumentManager
        
        :returns: list
        """
        return self.controllers.keys()
    
    def getResources(self):
        """
        Get all resources for all controllers.
        
        Resources are nested by controller name
        
        :returns: dict
        """
        return self.resources
    
    def getModels(self):
        """
        Get a listing of all Models loaded
        
        :returns: tuple - (`ModelName`, `Port`)
        """
        ret = {}
        
        for res_uuid, dev in self.devices.items():
            ret[res_uuid] = (dev.getModelName(), dev.rpc_getPort())
            
        return ret
    
    def getModelName(self, res_uuid):
        """
        Get the class name for the model loaded for a given resource

        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: str or None if no model loaded
        """
        dev = self.devices.get(res_uuid, None)
        
        if dev is not None:
            return dev.getModelName()
            
        else:
            return None
    
    def getModelPort(self, res_uuid):
        """
        Get the RPC Port for the model loaded for a given resource

        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: int or None if no model loaded
        """
        dev = self.devices.get(res_uuid, None)
        
        if dev is not None:
            
            try:
                # Start the RPC server if it isn't already started
                if not dev.rpc_isRunning():
                    dev.rpc_start()    
                
                return dev.rpc_getPort()
            
            except:
                pass

        return None
    
    def refresh(self, controller=None):
        """
        Refresh all resources for a given controller. If `controller` is None, 
        all controllers will be refreshed
        
        :param controller: Controller to refresh
        :type controller: str
        :returns: None
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
                    # Signal the controller to refresh resources
                    c_obj.refresh()
                    
                    # Get updated list of resources
                    new_res = c_obj.getResources() # { ResID -> (VID, PID) }
                    
                    # Create new resources
                    for resID, resTup in new_res.items():
                        int_res_id = (controller, resID) + resTup
                        
                        if int_res_id not in self.resources.values():
                            new_uuid = str(uuid.uuid4())
                            self.logger.debug('Res: %s Assigned UUID: %s', resID, new_uuid)
                            
                            self.resources[new_uuid] = int_res_id
                            
                            # Attempt to auto-load a Model
                            self.loadModel(new_uuid)
                            
                            #===================================================
                            # (VID, PID) = resTup
                            # 
                            # # Get a list of compatible models
                            # validModels = self.getValidModels(controller, VID, PID)
                            # 
                            # 
                            # if type(validModels) is list and len(validModels) > 0:
                            #     # TODO: Intelligently load a model or fail if multiple valid models are found
                            #     moduleName, className = validModels[0] 
                            #===================================================
                                
                    
                    # Purge unavailable resources
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
        """
        Check if a controller supports manually adding or removing resources.
        
        :param controller: Controller name
        :type controller: str
        :returns: bool - True if supported, False otherwise
        """
        if controller in self.controllers:
            try:
                return controller.canEditResources()
            
            except NotImplementedError:
                return False
    
    def addResource(self, controller, ResID, VID=None, PID=None):
        """
        Manually add a resource to a controller. VID and PID must be provided
        in order to correctly identify an appropriate model to load for the
        new resource.
        
        .. note::
        
            This will return False if manually adding resources is not supported.
            To check if the controller supports manual resource management,
            use :func:`InstrumentManager.canEditResources`
        
        :param controller: Controller name
        :type controller: str
        :param ResID: Resource Identifier
        :type ResID: str
        :param VID: Vendor Identifier
        :type VID: str
        :param PID: Product Identifier
        :type PID: str
        :returns: bool - True if successful, False otherwise
        """
        if controller in self.controllers:
            try:
                return controller.addResource(ResID, VID, PID)
            
            except NotImplementedError:
                return False
            
            except AttributeError:
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
    
    def getValidModels(self, controller, VID, PID):
        """
        Get a list of models that are considered valid for a given `controller`,
        Vendor Identifier (`VID`) and Product Identifier (`PID`) combination
        
        :param controller: Controller name
        :type controller: str
        :param VID: Vendor Identifier
        :type VID: str
        :param PID: Product Identifier
        :type PID: str
        
        :returns: list of tuples (ModuleName, ClassName)
        """
        # Models: { Controller -> { VendorID -> { modelName -> [ ProductID ] } } }
        ret = []
        
        mod_cont = self.models.get(controller, {})
        mod_vid = mod_cont.get(VID, {})
        for moduleInfo, PID_List in mod_vid.items():
            if PID in PID_List:
                ret.append(moduleInfo)
            
        return ret
                
    
    def loadModel(self, res_uuid, modelName=None, className=None):
        """
        Load a model given a resource UUID. A model will be selected
        automatically. To load a specific model, provide `modelName` 
        (importable python module) and `className`
        
        .. note::
        
            If modelName is specified, that model will be loaded without any 
            kind of compatibility checking. If an exception is thrown during 
            instantiation, the model will not be loaded.
            
        Example::
        
            manager.loadModel('360ba14f-19be-11e4-95bf-a0481c94faff', 'Tektronix.Oscilloscope.m_DigitalPhosphor', 'm_DigitalPhosphor')
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :param modelName: Model package (Python module)
        :type modelName: str
        :param className: Class Name
        :type className: str
        :returns: bool - True if successful, False otherwise
        """
        if res_uuid in self.resources.keys():
            (controller, res_uuid, VID, PID) = self.resources.get(res_uuid)
                
            # Auto
            if modelName is None:
                # Try to find a suitable model
                validModels = self.getValidModels(controller, VID, PID)
                
                if type(validModels) is list and len(validModels) == 1:
                    moduleName, className = validModels[0] 
                    res = self.loadModel(res_uuid, moduleName, className)
                    return res
                
                else:
                    # More than one valid model exists or none found
                    return False
                
            else:
                    
                try:
                    # Check if the specified model is valid
                    testModule = importlib.import_module(modelName)
                    testClass = getattr(testModule, className)
                    
                    # Load the model and store it
                    cont_obj = self.controllers.get(controller, None)
                    model_obj = testClass(res_uuid, cont_obj, res_uuid, Logger=self.logger)
                
                    model_obj._onLoad()
                    
                    # Start the model RPC server
                    model_obj.rpc_start()
                    
                    self.devices[res_uuid] = model_obj
                    self.logger.debug('Loaded model for %s', res_uuid)
                    
                    return True
                
                except AttributeError:
                    self.logger.exception('Model failed to load for %s', res_uuid)
                    return False
        
                except:
                    model_obj.rpc_stop()
                    model_obj._onUnload()
    
                    self.logger.exception('Model failed to load for %s', res_uuid)
                    return False
                
        else:
            return False
    
    def unloadModel(self, res_uuid):
        """
        Unloads the model for a given resource. 
                
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: bool - True if successful, False otherwise
        """
        dev = self.devices.pop(res_uuid, None)
        
        if dev is not None:
            try:
                dev.rpc_stop()
                
                dev.onUnload()
            
            except NotImplementedError:
                pass
            
            self.logger.info('Unloaded model for UUID %s', res_uuid)
            
            del dev
            
            return True
        
        return False
    
if __name__ == "__main__":
    # If InstrumentManager is run in interactive mode, just call run
    man = InstrumentManager()
    man._run()