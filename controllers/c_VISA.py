import importlib
import re
import time
import visa

import controllers

class c_VISA(controllers.c_Base):
    """
    VISA Controller
    
    Wraps PyVISA. Requires a VISA driver to be installed on the system.
    """
    
    # Dict: ResID -> r_VISA Object
    resources = {}
    
    resource_manager = None
            
    def refresh(self):
        if self.resource_manager is not None:
            try:
                res_list = self.resource_manager.list_resources()
                
                # Check for new resources
                for res in res_list:
                    if res not in self.resources.keys():
                        try:
                            new_resource = r_VISA(res, self, 
                                                  models=self.manager.getModels())
                            
                            self.resources[res] = new_resource
                            
                            self.manager._notify_new_resource()
                        
                        except:
                            self.logger.exception("Unhandled VISA Exception occurred while creating new resource: %s", res)
            
            except visa.VisaIOError:
                # Exception thrown when there are no resources
                res_list = []
                
    #===========================================================================
    # Required API Function Definitions
    #===========================================================================
    
    def open(self):
        """
        Initialize the VISA Controller. Instantiates a VISA Resource Manager
        and starts the controller thread.
        
        Return True if success, False if an error occurred
        """
        try:
            # Load the VISA Resource Manager
            self.resource_manager = visa.ResourceManager()
            
            return True
        
        except:
            self.logger.exception("Failed to initialize VISA Controller")
        
            return False
        
    def close(self):
        """
        Stops the VISA Controller. Stops the controller thread and frees all
        resources associated with the controller.
        """
        # TODO: Free all resources associated with the controller
        
        return True
    
    def getResources(self):
        return self.resources
            
class r_VISA(controllers.r_Base):
    """
    VISA Resource Base class.
    
    Wraps PyVISA Resource Class
    
    All VISA complient devices will adhere to the IEEE 488.2 standard
    for responses to the *IDN? query. The expected format is:
    <Manufacturer>,<Model>,<Serial>,<Firmware>
    
    BK Precision has a non-standard format for some of their instruments:
    <Model>,<Firmware>,<Serial>
    
    Models derived from a VISA resource do not need to provide values for the
    following property attributes as they are derived from the identification
    string:
        * deviceVendor
        * deviceModel
        * deviceSerial
        * deviceFirmware
    """
    
    type = "VISA"
        
    def __init__(self, resID, controller, **kwargs):
        controllers.r_Base.__init__(self, resID, controller, **kwargs)
        
        self.resource_manager = visa.ResourceManager()
        self.model_list = kwargs.get('models')

        try:
            self.logger.info("Created VISA Resource: %s", resID)
            self.instrument = self.resource_manager.open_resource(resID,
                                                                  open_timeout=0.5)
            
            self.identify()
            self.status = 'READY'
            
            self.loadModel()
            
            
        except visa.VisaIOError as e:
            self.VID = ''
            self.PID = ''
            self.firmware = ''
            self.serial = ''
            
            if e.abbreviation == "VI_ERROR_RSRC_BUSY":
                self.locked = True
                self.logger.info("Unable to Identify, resource is busy")
            elif e.abbreviation == "VI_ERROR_RSRC_NFOUND":
                pass
            else:
                self.logger.exception("Unknown VISA Exception")
        
    #===========================================================================
    # Resource State
    #===========================================================================
    
    def identify(self):
        self.open()
        
        self.identity = self.instrument.query("*IDN?").strip().split(',')
            
        if len(self.identity) == 4:
            self.VID, self.PID, self.serial, self.firmware = self.identity
            self.logger.info("Vendor: %s", self.VID)
            self.logger.info("Model:  %s", self.PID)
            self.logger.info("Serial: %s", self.serial)
            self.logger.info("F/W:    %s", self.firmware)
        
        elif len(self.identity) == 3:
            # Resource provided a non-standard identify response
            # Screw you BK Precision for making me do this
            self.VID = ''
            self.PID, self.firmware, self.serial = self.identity
            self.logger.info("Model:  %s", self.PID)
            self.logger.info("Serial: %s", self.serial)
            self.logger.info("F/W:    %s", self.firmware)
            
        else:
            self.VID = ''
            self.PID = ''
            self.firmware = ''
            self.serial = ''
            self.logger.error('Unable to identify VISA device: %s', resID)
            
        self.close()
        
    def open(self):
        self.instrument.open()
    
    def close(self):
        self.instrument.close()
        
    def lock(self):
        self.instrument.lock()
        
    def unlock(self):
        self.instrument.unlock()
        
    #===========================================================================
    # Data Transmission
    #===========================================================================
    
    def write(self, data):
        return self.instrument.write(data)
    
    def read(self):
        return self.instrument.read()
    
    def query(self, data):
        return self.instrument.query(data)
    
    def getProperties(self):
        def_prop = controllers.r_Base.getProperties(self)
        
        VISA_prop = {'deviceVendor':     self.VID,
                     'deviceModel':      self.PID,
                     'deviceSerial':     self.serial,
                     'deviceFirmware':   self.firmware
                     }
        
        def_prop.update(VISA_prop)
        
        return def_prop
                
    
    #===========================================================================
    # Models
    #===========================================================================
    
    def loadModel(self, modelName=None):
        """
        Load a Model. VISA supports enumeration and will thus search for a
        compatible model. A Model name can be specified to load a specific model,
        even if it may not be compatible with this resource. Reloads model
        when importing, in case an update has occured. If more than one 
        compatible model is found, no model will be loaded
        
        `modelName` must be an importable module on the remote system. The
        base folder used to locate the module is the `models` folder.
        
        On startup, the resource will attempt to load a valid Model 
        automatically. This function only needs to be called to
        override the default model. :func:`unloadModel` must be called before
        loading a new model for a resource.
        
        :returns: True if successful, False otherwise
        """
        if modelName is None:
            # Search for a compatible model
            validModels = []
            
            # Iterate through all Models to find compatible Models
            for modelModule, modelInfo in self.model_list.items():
                try:
                    for resType in modelInfo.get('validResourceTypes'):
                        if resType in ['VISA', 'visa']:
                            if (self.VID in modelInfo.get('VISA_compatibleManufacturers') and
                                self.PID in modelInfo.get('VISA_compatibleModels')):
                                validModels.append(modelModule)
                            
                except:
                    continue
                
            # Only auto-load a model if a single model was found
            if len(validModels) == 1:
                controllers.r_Base.loadModel(validModels[0])
                
                return True
            
            return False
                
        else:
            return controllers.r_Base.loadModel(self, modelName)
    
