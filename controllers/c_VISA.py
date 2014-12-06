import importlib
import re

import controllers

try:
    import visa
except:
    pass

class c_VISA(controllers.c_Base):
    """
    VISA Controller
    
    Wraps PyVISA. Requires a VISA driver to be installed on the system.
    
    __Vendors dictionary:
    -KEY is a Regex Expression to match the *IDN? string returned from the device
    -VALUE is the vendor of the device that matches the Regex Expression
    """
    
    __Vendors = [(r'(?:TEKTRONIX),([\w\d.]+),[\w\d.]+,[\w\d.]+', 'Tektronix'),
                 (r'(?:Agilent Technologies),([\w\d.]+),[\w\d.]+,[\w\d.]+', 'Aglient'),
                 (r'(?:BK PRECISION),\s*([\w\d.]+),\s*[\w\d.]+,\s*[\w\d\-.]+', 'BK Precision'),
                 (r'(?:CHROMA),\s*([\w\d\-.]+),\s*[\w\d.]+,\s*[\w\d.]+', 'Chroma'),
                 (r'([\w\d\s]+),\s*[\w\d.]+,\s*[\w\d.]+', 'Unknown')]
    
    # Dict: ResID -> (VID, PID)
    resources = {}
    # Dict: ResID -> PyVISA Instrument Object
    instruments = {}
    
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

            # Load the VISA Resource Manager
            self.__rm = visa.ResourceManager()
            self.logger.debug(str(self.__rm))
            
            self.refresh()
            
            return True
            
        except:
            self.__rm = None
            self.logger.exception("Failed to initialize VISA interface")
            return False
        
        # Setup vendor map dictionary
        # Maps the first chunk of an identify to a function
        
    def close(self):
        return True
    
    def refresh(self):
        """
        Refresh the VISA Resource list
        """
        if self.__rm is not None:
            self.logger.info("Refreshing VISA Resource list")
            try:
                res_list = self.__rm.list_resources()
            
            except visa.VisaIOError:
                # Exception thrown when there are no resources
                res_list = []
                
            # Add new resources
            for res in res_list:
                if res not in self.resources.keys():
                    try:
                        self.logger.info("Identifying VISA Resource: %s", res)
                        
                        instrument = self.__rm.open_resource(res)
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
                        self.instruments[res] = instrument
                    
                    except visa.VisaIOError as e:
                        self.logger.debug("VISA Device I/O Error, ignoring device.")
                    
                    except:  
                        self.logger.exception("Unhandled VISA Exception occurred")
            
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
    
    def _getInstrument(self, res_id):
        """
        Instruments are maintained by calling refresh()
        """
        return self.instruments.get(res_id, None)