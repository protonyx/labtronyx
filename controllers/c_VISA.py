import importlib
import re
import threading
import time

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
    
    e_alive = threading.Event()
    
    #===========================================================================
    # Controller Thread
    #===========================================================================
    
    def __thread_run(self):
        while(self.e_alive.isAlive()):
            
            self.refresh()
            
            time.sleep(60.0)
    
    #===========================================================================
    # Required API Function Definitions
    #===========================================================================
    
    def open(self):
        """
        Initialize the interface
        
        Use self.logger to log events and errors
        
        Return True if success, False if an error occurred
        """
            
        try:
            # Dependency: pyVISA
            import visa
            #visa = importlib.import_module('visa')
            
            # Load the VISA Resource Manager
            self.__resource_manager = visa.ResourceManager()
            
            self.e_alive.set()
            
            self.__controller_thread = threading.Thread(name="c_VISA", target=self.__thread_run)
            self.__controller_thread.run()
            
            return True
            
        except ImportError:
            self.logger.error("PyVISA Dependency Missing")
            
        except:
            self.logger.exception("Failed to initialize VISA Controller")
        
        return False
        
        # Setup vendor map dictionary
        # Maps the first chunk of an identify to a function
        
    def close(self):
        # Stop Controller Thread
        self.e_alive.clear()
        self.__controller_thread.join()
        
        return True
    
    def refresh(self):
        """
        Refresh the VISA Resource list
        """
        import visa 
        
        if self.__resource_manager is not None:
            self.logger.info("Refreshing VISA Resource list")
            try:
                res_list = self.__resource_manager.list_resources()
            
            except visa.VisaIOError:
                # Exception thrown when there are no resources
                res_list = []
                
            # Add new resources
            for res in res_list:
                if res not in self.resources.keys():
                    try:
                        new_resource = r_VISA(res, self.__resource_manager)
                        
                        instrument = self.openResourceObject(res)
                        
                        self.logger.info("Identifying VISA Resource: %s", res)
                        resp = instrument.ask("*IDN?").strip()

                        # Decode Identify
                        ident_vendor = "Unknown"
                        deviceModel = "Unknown"
                        
                        for reg_exp, vendor in self.__Vendors:
                            modelTest = re.findall(reg_exp, resp)
                            if len(modelTest) == 1:
                                ident_vendor = vendor
                                deviceModel = str(modelTest[0]).strip()
                                break
                        
                        mid = (ident_vendor, deviceModel)
                        
                        self.logger.info("Found VISA Device: %s %s" % mid)
                        
                        self.resources[res] = mid
                        self.resourceObjects[res] = instrument
                    
                    except visa.VisaIOError as e:
                        self.logger.debug("VISA Device I/O Error, ignoring device.")
                    
                    except:  
                        self.logger.exception("Unhandled VISA Exception occurred")
                        
                    finally:
                        self.closeResourceObject(res)
            
            # Purge resources that are no longer available
            for res in self.resources.keys():
                if res not in res_list:
                    # Close the resource and mark as disconnected
                    res_obj = self.resources.pop(res)
                    inst_obj = self.instruments.pop(res)
                    del inst_obj

            return True
        
        else:
            return False
        
    def getResources(self):
        return self.resources
    
    #===========================================================================
    # Protected or Private Function Definitions
    #===========================================================================
    
    def openResourceObject(self, resID):
        resource = self.resourceObjects.get(resID, None)
        if resource is not None:
            return resource
        else:
            resource = self.__rm.open_resource(resID)
            self.resourceObjects[resID] = resource
            return resource
        
    def closeResourceObject(self, resID):
        resource = self.resourceObjects.get(resID, None)
        
        if resource is not None:
            resource.close()
            del self.resourceObjects[resID]
            
class r_VISA(controllers.r_Base):
    """
    VISA Resource Base class.
    
    Wraps PyVISA Resource Class
    
    All VISA complient devices will adhere to the IEEE 488.2 standard
    for responses to the *IDN? query. The expected format is:
    <Manufacturer>,<Model>,<Serial>,<Firmware>
    """
    
    type = "VISA"
        
    def __init__(self, resID, resource_manager):
        controllers.r_Base.__init__(self)
        
        self.resID = resID
        self.resource_manager = resource_manager
        self.instrument = resource_manager.open_resource(resID)
        
        self.logger.info("Identifying VISA Resource: %s", res)
        self.identity = self.instrument.ask("*IDN?").strip()
        
        if len(self.identity) == 4:
            vendor, model, serial, firmware = self.identity
            self.logger.info("Vendor: %s", vendor)
            self.logger.info("Model:  %s", model)
            self.logger.info("Serial: %s", serial)
            self.logger.info("F/W:    %s", firmware)
            
        else:
            pass
        
    def open(self):
        pass
    
    def close(self):
        pass
    
    def write(self, data):
        pass
    
    def read(self):
        pass
    
    def query(self):
        pass