from Base_Interface import Base_Interface, InterfaceError, InterfaceTimeout
from Base_Resource import Base_Resource, ResourceNotOpen

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
                            instrument = self.resource_manager.open_resource(res,
                                                                  open_timeout=0.1)
                            
                            new_resource = r_VISA(res, self, 
                                                  drivers=self.manager.getDrivers(),
                                                  instrument=instrument,
                                                  logger=self.logger,
                                                  config=self.config,
                                                  enableRpc=self.manager.enableRpc)
                            
                            self.resources[res] = new_resource
                            
                            self.manager._cb_new_resource()
                        
                        except visa.VisaIOError as e:
                            if e.abbreviation in ["VI_ERROR_RSRC_BUSY", 
                                                  "VI_ERROR_RSRC_NFOUND",
                                                  "VI_ERROR_TMO"]:
                                pass
                                
                            else:
                                self.logger.exception("Unknown VISA Exception")
                        
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
        
        :returns: True if successful, False if an error occurred
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
            resObj.stop()
        
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
        self.instrument = kwargs.get('instrument')
        
        #self.instrument.timeout = 1000
        
        self.identify()
        
        self.logger.debug("Created VISA Resource: %s", resID)
        self.logger.debug("Vendor: %s", self.VID)
        self.logger.debug("Model:  %s", self.PID)
        self.logger.debug("Serial: %s", self.serial)
        self.logger.debug("F/W:    %s", self.firmware)
        
        self.close()
        
        self.loadDriver()
                
    def getProperties(self):
        def_prop = Base_Resource.getProperties(self)
        
        def_prop.setdefault('deviceVendor', self.getVISA_vendor())
        def_prop.setdefault('deviceModel', self.getVISA_model())
        def_prop.setdefault('deviceSerial', self.getVISA_serial())
        def_prop.setdefault('deviceFirmware', self.getVISA_firmware())
        
        return def_prop
    
    def refresh(self):
        self.identify()
        
        if self.driver is None:
            # Attempt to automatically load a driver
            self.loadDriver()
        
    #===========================================================================
    # VISA Specific
    #===========================================================================
    
    def identify(self):
        start_state = self.isOpen()
        start_timeout = self.instrument.timeout
        if not start_state:
            self.open()
            
        #self.instrument.timeout = 500
        
        try:
            self.identity = self.query("*IDN?").strip().split(',')
        except Exception as e:
            self.identity = []
            
        if len(self.identity) >= 4:
            self.VID = self.identity[0].strip()
            self.PID = self.identity[1].strip()
            self.serial = self.identity[2].strip()
            self.firmware = self.identity[4].strip()
        
        elif len(self.identity) == 3:
            # Resource provided a non-standard identify response
            # Screw you BK Precision for making me do this
            self.VID = ''
            self.PID, self.firmware, self.serial = self.identity
            
        else:
            self.VID = ''
            self.PID = ''
            self.firmware = ''
            self.serial = ''
            self.logger.error('Unable to identify VISA device')
            
        self.instrument.timeout = start_timeout
            
        if start_state == False:
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
        
    def isOpen(self):
        import pyvisa
        
        try:
            sess = self.instrument.session
            return True
        
        except pyvisa.errors.InvalidSession:
            return False
    
    def close(self):
        self.instrument.close()
        
    def lock(self):
        self.instrument.lock()
        
    def unlock(self):
        self.instrument.unlock()
        
    #===========================================================================
    # Configuration
    #===========================================================================
    
    def configure(self, **kwargs):
        """
        Configure Serial port parameters for the resource.
        
        :param baudrate: Serial - Baudrate. Default 9600
        :param timeout: Read timeout
        :param bytesize: Serial - Number of bits per frame. Default 8.
        :param parity: Serial - Parity
        :param stopbits: Serial - Number of stop bits
        :param termination: Write termination
        """
        if 'baudrate' in kwargs:
            self.instrument.baud_rate = int(kwargs.get('baudrate'))
            
        if 'bytesize' in kwargs:
            self.instrument.data_bits = int(kwargs.get('bytesize'))
            
        if 'parity' in kwargs:
            import pyvisa.constants as pvc
            parity_convert = {
                'N': pvc.Parity.none,
                'E': pvc.Parity.even,
                'M': pvc.Parity.mark,
                'O': pvc.Parity.odd,
                'S': pvc.Parity.space}
            self.instrument.parity = parity_convert.get(kwargs.get('parity'))
            
        if 'stopbits' in kwargs:
            self.instrument.stopbits = int(kwargs.get('stopbits'))
            
        if 'termination' in kwargs:
            self.instrument.write_termination = kwargs.get('termination')
            
    def getConfiguration(self):
        ret = {}
        ret['baudrate'] = self.instrument.baud_rate
        ret['bytesize'] = self.instrument.data_bits
        ret['parity'] = self.instrument.parity
        ret['stopbits'] = self.instrument.stopbits
        ret['termination'] = self.instrument.write_termination
        return ret
        
    #===========================================================================
    # Data Transmission
    #===========================================================================
    
    def write(self, data):
        """
        Send String data to the instrument. Includes termination
        character.
        
        Raises exception if the resource is not ready. 
        
        To get the error condition, call `getResourceError`
        
        :param data: Data to send
        :type data: str
        :raises: ResourceNotOpen
        """
        try:
            self.logger.debug("VISA Write: %s", data)
            self.instrument.write(data)
        
        except visa.InvalidSession:
            raise ResourceNotOpen
                
    def write_raw(self, data):
        """
        Send Binary-encoded data to the instrument. Termination character is
        not included
        
        :param data: Data to send
        :type data: str
        :raises: ResourceNotReady
        """
        self.checkResourceStatus()
        
        try:
            self.instrument.write_raw(data)
        
        except visa.InvalidSession:
            raise ResourceNotOpen
        
    def read(self, termination=None, encoding=None):
        """
        Read ASCII-formatted data from the instrument.
        
        Reading stops when the device stops sending, or the termination 
        characters sequence was detected.
        
        All line-ending characters are stripped from the end of the string.
        
        :param termination: Line termination
        :type termination: str
        :param encoding: Encoding
        :type encoding: Unknown
        """
        try:
            return self.instrument.read(termination, encoding)
        
        except visa.InvalidSession:
            raise ResourceNotOpen
    
    def read_raw(self, size=None):
        """
        Read Binary-encoded data from the instrument.
        
        No termination characters are stripped.
        
        :param size: Number of bytes to read
        :type size: int
        """
        ret = bytes()

        # There is a bug in PyVISA that forces a low-level call (hgrecco/pyvisa #93)
        with self.instrument.ignore_warning(visa.constants.VI_SUCCESS_MAX_CNT):
            if size is None:
                num_bytes = self.instrument.bytes_in_buffer
                chunk, status = self.instrument.visalib.read(self.instrument.session, num_bytes)
                ret += chunk

            else:
                while len(ret) < size:
                    chunk, status = self.instrument.visalib.read(self.instrument.session, size - len(ret))
                    ret += chunk
                    
        return ret
    
    def query(self, data, delay=None):
        """
        Retreive ASCII-encoded data from the device given a prompt.
        
        A combination of write(data) and read()
        
        :param data: Data to send
        :type data: str
        :param delay: delay (in seconds) between write and read operations.
        :type delay: float
        :returns: str
        """
        try:
            self.logger.debug("VISA Query: %s" % data)
            return self.instrument.query(data)
        
        except visa.InvalidSession:
            raise ResourceNotOpen
                
    def inWaiting(self):
        """
        Return the number of bytes in the receive buffer
        
        :returns: int
        """
        return self.instrument.bytes_in_buffer
    
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
    
