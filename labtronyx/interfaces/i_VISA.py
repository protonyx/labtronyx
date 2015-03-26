from Base_Interface import Base_Interface
from Base_Resource import Base_Resource

import importlib
import re
import time
import visa

import common.resource_status as resource_status

class i_VISA(Base_Interface):
    """
    VISA Controller
    
    Wraps PyVISA. Requires a VISA driver to be installed on the system.
    """
    
    REFRESH_RATE = 5.0 # Seconds
    
    info = {
        # Interface Author
        'author':               'KKENNEDY',
        # Interface Version
        'version':              '1.0',
        # Revision date
        'date':                 '2015-03-06'
    }
    
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
                                                  drivers=self.manager.getDrivers())
                            
                            self.resources[res] = new_resource
                            
                            self.manager._cb_new_resource()
                        
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
        for resObj in self.resources.values():
            resObj.killResource()
        
        self.resources.clear()
        
        return True
    
    def getResources(self):
        return self.resources
            
class r_VISA(Base_Resource):
    """
    VISA Resource Base class.
    
    Wraps PyVISA Resource Class
    
    All VISA complient devices will adhere to the IEEE 488.2 standard
    for responses to the '*IDN?' query. The expected format is:
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
        
    def __init__(self, resID, interface, **kwargs):
        Base_Resource.__init__(self, resID, interface, **kwargs)
        
        self.resource_manager = visa.ResourceManager()
        self.driver_list = kwargs.get('drivers', {})

        try:
            self.logger.info("Created VISA Resource: %s", resID)
            self.instrument = self.resource_manager.open_resource(resID,
                                                                  open_timeout=0.5)
            self.setResourceStatus(resource_status.READY)
            
            self.identify()
            
            # Attempt to automatically load a driver
            self.loadDriver()
            
        except visa.VisaIOError as e:
            self.VID = ''
            self.PID = ''
            self.firmware = ''
            self.serial = ''
            
            self.setResourceStatus(resource_status.ERROR)
            
            if e.abbreviation == "VI_ERROR_RSRC_BUSY":
                self.locked = True
                self.logger.info("Unable to Identify, resource is busy")
                self.setResourceError(resource_status.ERROR_BUSY)
                
            elif e.abbreviation == "VI_ERROR_TMO":
                self.logger.info("Unable to Identify, resource did not respond")
                self.setResourceError(resource_status.ERROR_NOTFOUND)
                
            elif e.abbreviation == "VI_ERROR_RSRC_NFOUND":
                self.logger.info("Unable to connect, resource was not found")
                self.setResourceError(resource_status.ERROR_NOTFOUND)
                
            else:
                self.logger.exception("Unknown VISA Exception")
                self.setResourceError(resource_status.ERROR_UNKNOWN)
                
    def getProperties(self):
        def_prop = Base_Resource.getProperties(self)
        
        def_prop.setdefault('deviceVendor', self.getVISA_vendor())
        def_prop.setdefault('deviceModel', self.getVISA_model())
        def_prop.setdefault('deviceSerial', self.getVISA_serial())
        def_prop.setdefault('deviceFirmware', self.getVISA_firmware())
        
        return def_prop
        
    #===========================================================================
    # VISA Specific
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
        
    def getVISA_vendor(self):
        return self.VID
    
    def getVISA_model(self):
        return self.PID
    
    def getVISA_serial(self):
        return self.serial
    
    def getVISA_firmware(self):
        return self.firmware
        
    #===========================================================================
    # Resource State
    #===========================================================================
        
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
        """
        Send data to the instrument. Raises exception if the resource is not
        ready. To get the error condition, call `getResourceError`
        
        :param data: Data to send
        :type data: str
        :raises: ResourceNotReady
        """
        self.checkResourceStatus()
        
        for attempt in range(2):
            try:
                return self.instrument.write(data)
            except visa.InvalidSession:
                self.open()
    
    def read(self):
        self.checkResourceStatus()
        
        return self.instrument.read()
    
    def query(self, data):
        self.checkResourceStatus()
        
        return self.instrument.query(data)
    
    #===========================================================================
    # Drivers
    #===========================================================================
    
    def loadDriver(self, driverName=None):
        """
        Load a Model. VISA supports enumeration and will thus search for a
        compatible model. A Model name can be specified to load a specific model,
        even if it may not be compatible with this resource. Reloads model
        when importing, in case an update has occured. If more than one 
        compatible model is found, no model will be loaded
        
        `driverName` must be an importable module on the remote system. The
        base folder used to locate the module is the `models` folder.
        
        On startup, the resource will attempt to load a valid Model 
        automatically. This function only needs to be called to
        override the default model. :func:`unloadModel` must be called before
        loading a new model for a resource.
        
        :returns: True if successful, False otherwise
        """
        if driverName is None:
            # Search for a compatible model
            validModels = []
            
            # Iterate through all Models to find compatible Models
            for modelModule, modelInfo in self.driver_list.items():
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
                Base_Resource.loadDriver(self, validModels[0])
                
                return True
            
            return False
                
        else:
            return Base_Resource.loadDriver(self, driverName)
    
