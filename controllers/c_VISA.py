import importlib
import controllers
import visa


class c_VISA(controllers.c_Base):
    """
    Wrapper for PyVISA
    
    __Vendors dictionary:
    -KEY is the contents of the first comma-seperated segment of the identification string
    -VALUE is a tuple with the human readable vendor string and a lambda expression to extract the model information from the identification string
    
    TODO: Make the key a RegEx expression to match. The scanner will try to match the first expression and use it to decode the identify
    """
    
    __Vendors = {'Agilent Technologies': ('Agilent', lambda x: x[1]),
                 'TEKTRONIX':            ('Tektronix', lambda x: x[1])
                }
    
    # TODO: Make controller resources simpler, push model creation onto manager
    # Dict: ResID -> (VID, PID)
    resources = {}
    # Dict: ResID -> PyVISA Instrument Object
    instruments = {}
    
    def open(self):
        """
        Initialize the interface
        
        Use self.logger to log events and errors
        
        Return True if success, False if an error occurred
        """
        
        try:
            # Load the VISA Resource Manager
            self.__rm = visa.ResourceManager()
            self.logger.debug(str(self.__rm))
            
            return self.refresh()
            
        except:
            self.__rm = None
            self.logger.error("Failed to initialize VISA interface")
            return False
        
        # Setup vendor map dictionary
        # Maps the first chunk of an identify to a function
        
    def __identifyInstrument(self, instrument):
        """
        Attempts to identify a resource
        
        Parameters:
        - VISAInstrument
        
        Returns:
        - Tuple (VID, PID) for model identification
        """
        # Attempt to identify
        resp = instrument.ask("*IDN?").strip()

        # Decode Identify
        ident = resp.split(',')
        key = c_VISA.__Vendors[ident[0]]
        vendor = key[0]
        deviceModel = key[1](ident)
        
        #=======================================================================
        # self.resources[res] = {'identity': resp,
        #                        'object': None,
        #                        'instrument': instrument,
        #                        'vendor': vendor,
        #                        'model': deviceModel,
        #                        'uuid': str(uuid.uuid1())}
        #=======================================================================
        
        return (vendor, deviceModel)
    
    def refresh(self):
        """
        Refresh the VISA Resource list
        
        TODO: Implement
        """
        if self.__rm is not None:
            self.logger.info("Refreshing VISA Resource list")
            res_list = self.__rm.list_resources()
            
            # Add new resources
            for res in res_list:
                if res not in self.resources.keys():
                    try:
                        self.logger.info("Identifying VISA Resource: %s", res)
                        
                        instrument = self.__rm.get_instrument(res, timeout=0.5)
                        mid = self.__identifyInstrument(instrument)
                        
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
    
    #===========================================================================
    # def scan(self):
    #     try:
    #         for device in self.resources:
    #             if self.resources[device]['object'] is None:
    #                 # Attempt to identify the device
    #                 self.load(resource=device)
    #                 
    #     except:
    #         self.logger.exception('Exception occurred during VISA scan')
    #         return False
    #     
    #     return True
    #===========================================================================
    
    #===========================================================================
    # def load(self, **kwargs):
    #     """
    #     Enumerate the VISA Resource and attempt to find a suitable driver
    #     
    #     Parameters:
    #     Required:
    #         - resource string
    #         
    #     Optional:
    #         - model (if you want to override the default)
    #     """
    #     
    #     try:
    #         res_str = kwargs.get('resource')
    #         
    #         # Lookup the device model number in the model map dictionary
    #         deviceModel = self.resources[res_str]['model']
    #         
    #         if deviceModel in self.models:
    #             # Get VISA Instrument
    #             instrument = self.resources[res_str]['instrument']
    #         
    #             moduleName, className = self.models[deviceModel]
    #             
    #             testModule = importlib.import_module(moduleName)
    #             testClass = getattr(testModule, className)
    #             
    #             # Instantiate the model and get the serial number
    #             testModel = testClass(VISAInstrument=instrument, controller=self, logger=self.logger)
    #             
    #             self.resources[res_str]['serial'] = testModel.getSerialNumber()
    #             self.resources[res_str]['firmware'] = testModel.getFirmwareRev()
    #             
    #             self.logger.debug("Serial Number: %s", str(self.resources[res_str]['serial']))
    #             self.logger.debug("Firmware Rev: %s", str(self.resources[res_str]['firmware']))
    #             self.logger.debug("Driver Model: %s", moduleName)
    #             
    #             # Add instantiated model to return list
    #             self.resources[res_str]['object'] = testModel
    #             
    #             return True
    #         
    #         else:
    #             self.logger.error("No VISA model could be found for %s", deviceModel)
    #             
    #     except NotImplementedError:
    #         self.logger.error("A model call was attempted, but the function was not implemented as required. Check model: %s", moduleName) 
    #         
    #     except AttributeError:
    #         self.logger.error("Model %s could not be instantiated", moduleName)
    #              
    #     except KeyError:
    #         self.logger.exception("VISA Resources were opened incorrectly")
    #         
    #     except:
    #         self.logger.exception("An unhandled exception occurred during VISA device enumeration")
    #         
    #     return False
    # 
    # def unload(self):
    #     # TODO
    #     pass
    #===========================================================================
    
    def getModelID(self, res_id):
        """
        Return the ModelID information given a resource ID
        """
        return self.resources.get(res_id, None)
        
    def getResources(self):
        return self.resources
    
    def _getInstrument(self, res_id):
        """
        Instruments are maintained by calling refresh()
        """
        return self.instruments.get(res_id, None)
    
    def getResources_old(self):
        """
        Returns: list of dict with keys:
        - 'id': How the resource will be identified when a load call is made
        - 'uuid': A UUID string for reference only
        - 'controller': The module name for the controller
        - 'driver': The module name for the currently loaded model, None if not loaded
        - 'port': If RPC Server port, if it is running
        - 'deviceVendor': The device vendor
        - 'deviceModel': The device model number
        - 'deviceSerial': The device serial number
        - 'deviceFirmware': The device firmware revision
        - 'deviceType': The device type from the model
        """
        ret = []
        
        for res, val in self.resources.items():
            # These are always local resources
            temp = {}
            temp['id'] = res
            temp['uuid'] = val['uuid']
            temp['driver'] = None
            
            if val['object'] is not None:
                temp['controller'] = self.__class__.__name__
                temp['driver'] = val['object'].getModelName()
                
                try:
                    temp['port'] = val['object'].rpc_getPort()
                except:
                    temp['port'] = None
                    
                temp['deviceVendor'] = val['object'].getVendor()
                temp['deviceModel'] = val['object'].getModelNumber()
                temp['deviceSerial'] = val['object'].getSerialNumber()
                temp['deviceFirmware'] = val['object'].getFirmwareRev()
                temp['deviceType'] = val['object'].getDeviceType()
                
            ret.append(temp)
            
        return ret
    
    #===========================================================================
    # def _getModels(self):
    #     """
    #     Returns a list of model objects
    #     """
    #     ret = []
    #     
    #     for res in self.resources:
    #         if hasattr(self.resources, 'object') and res['object'] != None:
    #             ret.append(res['object'])
    #             
    #     return ret
    #===========================================================================
                
    def close(self):
        """
        Perform housekeeping tasks and call any close functions to OS APIs
        
        Return anything, it doesn't really matter
        """
        return True