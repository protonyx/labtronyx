import importlib

import controllers

class c_VISA(controllers.c_Base):
    """
    VISA Controller
    
    Wraps PyVISA. Requires a VISA driver to be installed on the system.
    
    __Vendors dictionary:
    -KEY is the contents of the first comma-seperated segment of the identification string
    -VALUE is a tuple with the human readable vendor string and a lambda expression to extract the model information from the identification string
    
    TODO: Make the key a RegEx expression to match. The scanner will try to match the first expression and use it to decode the identify
    """
    
    __Vendors = {'Agilent Technologies': ('Agilent', lambda x: x[1]),
                 'TEKTRONIX':            ('Tektronix', lambda x: x[1])
                }
    
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
                        
                        instrument = self.__rm.get_instrument(res, timeout=0.5)
                        resp = instrument.ask("*IDN?").strip()

                        # Decode Identify
                        ident = resp.split(',')
                        key = c_VISA.__Vendors[ident[0]]
                        vendor = key[0]
                        deviceModel = key[1](ident)
                        
                        mid = (vendor, deviceModel)
                        
                        self.logger.info("Found VISA Device: %s %s" % mid)
                        
                        self.resources[res] = mid
                        self.instruments[res] = instrument
                    
                    except visa.VisaIOError:
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
            