import importlib
import re
import time
import visa

import controllers

class c_VISA(controllers.c_Base):
    """
    VISA Controller
    
    Wraps PyVISA. Requires a VISA driver to be installed on the system.
    
    __Vendors dictionary:
    -KEY is a Regex Expression to match the *IDN? string returned from the device
    -VALUE is the vendor of the device that matches the Regex Expression
    
    TODO: 
    """
    
    __Vendors = [(r'(?:TEKTRONIX),([\w\d.]+),[\w\d.]+,[\w\d.]+', 'Tektronix'),
                 (r'(?:Agilent Technologies),([\w\d.]+),[\w\d.]+,[\w\d.]+', 'Agilent'),
                 (r'(?:AGILENT TECHNOLOGIES),([\w\d.]+),[\w\d.]+,[\w\d.]+', 'Agilent'),
                 (r'(?:BK PRECISION),\s*([\w\d.]+),\s*[\w\d.]+,\s*[\w\d\-.]+', 'BK Precision'),
                 (r'(?:CHROMA),\s*([\w\d\-.]+),\s*[\w\d.]+,\s*[\w\d.]+', 'Chroma'),
                 (r'([\w\d\s]+),\s*[\w\d.]+,\s*[\w\d.]+', 'Unknown')]
    
    # Dict: ResID -> r_VISA Object
    resources = {}
            
    def refresh(self):
        if self.__resource_manager is not None:
            try:
                res_list = self.__resource_manager.list_resources()
                
                # Check for new resources
                for res in res_list:
                    if res not in self.resources.keys():
                        try:
                            new_resource = r_VISA(res, self, self.__resource_manager)
                            
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
            self.__resource_manager = visa.ResourceManager()
            
            self.startThread()
            return True
        
        except:
            self.logger.exception("Failed to initialize VISA Controller")
            self.stopThread()
        
            return False
        
    def close(self):
        """
        Stops the VISA Controller. Stops the controller thread and frees all
        resources associated with the controller.
        """
        # Stop Controller Thread
        self.stopThread()
        
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
    """
    
    type = "VISA"
        
    def __init__(self, resID, controller, resource_manager):
        controllers.r_Base.__init__(self, resID, controller)
        
        self.resource_manager = resource_manager

        try:
            self.logger.info("Identified new VISA Resource: %s", resID)
            self.instrument = resource_manager.open_resource(resID)
            self.identity = self.instrument.ask("*IDN?").strip(',')
            
            if type(self.identity) == list and len(self.identity) == 4:
                self.VID, self.PID, self.serial, self.firmware = self.identity
                self.logger.info("Vendor: %s", self.VID)
                self.logger.info("Model:  %s", self.PID)
                self.logger.info("Serial: %s", self.serial)
                self.logger.info("F/W:    %s", self.firmware)
                
            else:
                # Resource provided a non-standard identify response
                # Screw you BK Precision
                # TODO: What should we do when a non-standard identify is received?
                pass
            
        except visa.VisaIOError as e:
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
    