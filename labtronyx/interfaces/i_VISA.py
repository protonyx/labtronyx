"""
VISA Interface module for Labtronyx

:codeauthor: Kevin Kennedy
"""

from traceback import format_exc

import visa
import pyvisa

from labtronyx.bases.interface import Base_Interface
from labtronyx.bases.resource import Base_Resource
from labtronyx.common.errors import *
import labtronyx.common as common


class i_VISA(Base_Interface):
    """
    VISA Controller
    
    Wraps PyVISA. Requires a VISA driver to be installed on the system.
    """

    info = {}

    resource_manager = None

    def __init__(self, manager, **kwargs):
        # Allow the use of a custom library for testing
        self._lib = kwargs.pop('library', '')

        Base_Interface.__init__(self, manager, **kwargs)

    def open(self):
        """
        Initialize the VISA Controller. Instantiates a VISA Resource Manager
        and starts the controller thread.

        :returns: True if successful, False if an error occurred
        """
        try:
            # Load the VISA Resource Manager
            self.resource_manager = visa.ResourceManager(self._lib)

            # Announce details about the VISA driver
            debug_info = self.resource_manager.visalib.get_debug_info()

            # Enumerate all of the connected instruments
            self.enumerate()

            return True

        except Exception as e:
            self.logger.exception("Failed to initialize VISA Controller")

            return False

    def close(self):
        """
        Stops the VISA Interface. Frees all resources associated with the interface.
        """
        for resObj in self._resources.values():
            try:
                resObj.close()
            except visa.VisaIOError:
                pass
            except visa.InvalidSession:
                pass

        self._resources.clear()

        return True

    def enumerate(self):
        """
        Identify all devices known to the VISA driver and create resource objects for valid resources
        """
        if self.resource_manager is not None:
            try:
                res_list = self.resource_manager.list_resources()

                # Check for new resources
                for res in res_list:
                    if res not in self._resources.keys():
                        try:
                            instrument = self.resource_manager.open_resource(res)

                            # Instantiate the resource object
                            new_resource = r_VISA(manager=self.manager,
                                                  interface=self,
                                                  resID=res,
                                                  visa_instrument=instrument,
                                                  logger=self.logger)

                            self._resources[res] = new_resource

                            # Signal new resource event
                            self.manager._event_signal(common.constants.ResourceEvents.created)

                        except visa.VisaIOError as e:
                            if e.abbreviation in ["VI_ERROR_RSRC_BUSY",
                                                  "VI_ERROR_RSRC_NFOUND",
                                                  "VI_ERROR_TMO",
                                                  "VI_ERROR_INV_RSRC_NAME"]: # Returned by TekVISA
                                # Ignore these errors and move on
                                pass

                            else:
                                self.logger.exception("Unable to open VISA resource, unhandled error: %s" % e.abbreviation)

            except visa.VisaIOError as e:
                # Exception thrown when there are no resources
                # TODO: only catch the specific error
                res_list = []

            except:
                self.logger.exception("Unhandled VISA Exception while enumerating resources")
                raise

    def prune(self):
        """
        Close any resources that are no longer known to the VISA driver
        """
        if self.resource_manager is not None:
            try:
                # Get a fresh list of resources
                res_list = self.resource_manager.list_resources()

                # Check for new resources
                for res in self._resources:
                    if res not in res_list:
                        resource = self._resources.get(res)

                        resource.close()

            except visa.VisaIOError:
                # Exception thrown when there are no resources
                pass

            except:
                self.logger.exception("Unhandled VISA Exception while pruning resources")
                raise

class r_VISA(Base_Resource):
    """
    VISA Resource Base class.
    
    Wraps PyVISA Resource Class
    
    All VISA complient devices will adhere to the IEEE 488.2 standard
    for responses to the '*IDN?' query. The expected format is:
    <Manufacturer>,<Model>,<Serial>,<Firmware>
    
    BK Precision has a non-standard format for some of their instruments:
    <Model>,<Firmware>,<Serial>
    
    Drivers derived from a VISA resource do not need to provide values for the
    following property attributes as they are derived from the identification
    string:
        
       * deviceVendor
       * deviceModel
       * deviceSerial
       * deviceFirmware
    """

    type = "VISA"

    def __init__(self, manager, interface, resID, **kwargs):
        self.instrument = kwargs.pop('visa_instrument')
        self.instrument.read_termination = self._read_termination = kwargs.pop('read_termination', '\r')
        self.instrument.write_termination = self._write_termination = kwargs.pop('write_termination', '\r\n')
        self.instrument.timeout = self._timeout = kwargs.pop('timeout', 2000)

        Base_Resource.__init__(self, manager, interface, resID, **kwargs)

        # Instrument is created in the open state, but we do not want to lock the VISA instrument
        self.close()

        # Set a flag to initialize the resource when it is used
        self.ready = False

    def getProperties(self):
        if not self.ready:
            self.identify()

        def_prop = Base_Resource.getProperties(self)

        def_prop.setdefault('deviceVendor', self.getVISA_vendor())
        def_prop.setdefault('deviceModel', self.getVISA_model())
        def_prop.setdefault('deviceSerial', self.getVISA_serial())
        def_prop.setdefault('deviceFirmware', self.getVISA_firmware())

        return def_prop

    def refresh(self):
        self.identify()

        if self._driver is None:
            # Attempt to automatically load a driver
            self.loadDriver()

    #===========================================================================
    # VISA Specific
    #===========================================================================

    def identify(self):
        """
        Query the resource to find out what instrument it is. Uses the standard SCPI query string `*IDN?`. Will attempt
        to load a driver using the information returned.
        """
        start_state = self.isOpen()
        if not start_state:
            self.open()

        self.logger.debug("Identifying VISA Resource: %s", self.resID)

        # Reset identity data
        self._identity = []

        try:
            # Set the timeout really low
            start_timeout = self.instrument.timeout
            self.instrument.timeout = 100
            #self.instrument.

            scpi_ident = self.query("*IDN?")
            self._identity = scpi_ident.strip().split(',')

            # Set the timeout back to what it was
            self.instrument.timeout = start_timeout

        except InterfaceTimeout:
            self.logger.debug("No response to SCPI Identify")
            self.logger.error('Unable to identify VISA Resource: %s', self.resID)


        if len(self._identity) >= 4:
            self.VID = self._identity[0].strip()
            self.PID = self._identity[1].strip()
            self.serial = self._identity[2].strip()
            self.firmware = self._identity[3].strip()

            self.logger.debug("Identified VISA Resource: %s", self.resID)
            self.logger.debug("Vendor: %s", self.VID)
            self.logger.debug("Model:  %s", self.PID)
            self.logger.debug("Serial: %s", self.serial)
            self.logger.debug("F/W:    %s", self.firmware)

        elif len(self._identity) == 3:
            # Resource provided a non-standard identify response
            # Screw you BK Precision for making me do this
            self.VID = ''
            self.PID, self.firmware, self.serial = self._identity

            self.logger.debug("Identified VISA Resource: %s", self.resID)
            self.logger.debug("Model:  %s", self.PID)
            self.logger.debug("Serial: %s", self.serial)
            self.logger.debug("F/W:    %s", self.firmware)

        else:
            self.VID = ''
            self.PID = ''
            self.firmware = ''
            self.serial = ''


        # Attempt to find a suitable driver if one is not already loaded
        if self._driver is None:
            self.loadDriver()

        if start_state == False:
            self.close()

        self.ready = True

    def getVISA_vendor(self):
        if not self.ready:
            self.identify()

        return self.VID

    def getVISA_model(self):
        if not self.ready:
            self.identify()

        return self.PID

    def getVISA_serial(self):
        if not self.ready:
            self.identify()

        return self.serial

    def getVISA_firmware(self):
        if not self.ready:
            self.identify()

        return self.firmware

    #===========================================================================
    # Resource State
    #===========================================================================

    def open(self):
        """
        Open the resource and prepare to receive commands.

        If an error occurs, call :func:`getError` to get more information about the error

        :returns: True if successful, False otherwise
        """
        try:
            self.instrument.open()

            # Restore instrument context
            self.instrument.read_termination = self._read_termination
            self.instrument.write_termination = self._write_termination
            self.instrument.timeout = self._timeout

            if self._driver is not None:
                try:
                    self._driver.open()
                except NotImplementedError:
                    pass

            return True

        except visa.VisaIOError as e:
            self._error = format_exc()
            return False

    def isOpen(self):
        """
        Query the VISA resource to find if it is open

        :return: bool
        """
        try:
            sess = self.instrument.session
            return True

        except pyvisa.errors.InvalidSession:
            return False

    def close(self):
        """
        Close the resource.

        If an error occurs, call :func:`getError` to get more information about the error

        :returns: True if successful, False otherwise
        """
        try:
            if self._driver is not None:
                try:
                    self._driver.close()
                except NotImplementedError:
                    pass

            # Save instrument context before closing
            self._read_termination = self.instrument.read_termination
            self._write_termination = self.instrument.write_termination
            self._timeout = self.instrument.timeout

            # Close the instrument
            self.instrument.close()
            return True

        except visa.VisaIOError:
            self._error = format_exc()
            return False

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
        # if self.instrument.interface_type == pyvisa.constants.InterfaceType.usb:

        if type(self.instrument) == pyvisa.resources.serial.SerialInstrument:
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

        if type(self.instrument) == pyvisa.resources.serial.SerialInstrument:
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
            self.instrument.write(data)

            self.logger.debug("VISA Write: %s", data)

        except visa.InvalidSession:
            raise ResourceNotOpen()

        except visa.VisaIOError as e:
            raise InterfaceError(e.description)

    def write_raw(self, data):
        """
        Send Binary-encoded data to the instrument. Termination character is
        not included
        
        :param data: Data to send
        :type data: str
        :raises: ResourceNotReady
        """
        try:
            self.instrument.write_raw(data)

        except visa.InvalidSession:
            raise ResourceNotOpen()

        except visa.VisaIOError as e:
            raise InterfaceError(e.description)

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
            data = self.instrument.read(termination, encoding)

            self.logger.debug("VISA Read: %s", data)

            return data

        except visa.InvalidSession:
            raise ResourceNotOpen()

        except visa.VisaIOError as e:
            if e.abbreviation in ["VI_ERROR_TMO"]:
                raise InterfaceTimeout(e.description)
            else:
                raise InterfaceError(e.description)

    def read_raw(self, size=None):
        """
        Read Binary-encoded data from the instrument.
        
        No termination characters are stripped.
        
        :param size: Number of bytes to read
        :type size: int
        """
        ret = bytes()

        try:
            if type(self.instrument) == pyvisa.resources.serial.SerialInstrument:
                # There is a bug in PyVISA that forces a low-level call (hgrecco/pyvisa #93)
                import pyvisa
                with self.instrument.ignore_warning(pyvisa.constants.VI_SUCCESS_MAX_CNT):
                    if size is None:
                        num_bytes = self.instrument.bytes_in_buffer
                        chunk, status = self.instrument.visalib.read(self.instrument.session, num_bytes)
                        ret += chunk

                    else:
                        while len(ret) < size:
                            chunk, status = self.instrument.visalib.read(self.instrument.session, size - len(ret))
                            ret += chunk

                return ret

            else:
                return self.instrument.read_raw()

        except visa.InvalidSession:
            raise ResourceNotOpen

        except visa.VisaIOError as e:
            if e.abbreviation in ["VI_ERROR_TMO"]:
                raise InterfaceTimeout(e.description)
            else:
                raise InterfaceError(e.description)

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
            ret_data = self.instrument.query(data)

            self.logger.debug("VISA Write: %s", data)
            self.logger.debug("VISA Read: %s", ret_data)

            return ret_data

        except visa.InvalidSession:
            raise ResourceNotOpen

        except visa.VisaIOError as e:
            if e.abbreviation in ["VI_ERROR_TMO"]:
                raise InterfaceTimeout(e.description)
            else:
                raise InterfaceError(e.description)

    def inWaiting(self):
        """
        Return the number of bytes in the receive buffer for a Serial VISA
        Instrument. All other VISA instrument types will return 0.
        
        :returns: int
        """
        if type(self.instrument) == pyvisa.resources.serial.SerialInstrument:
            return self.instrument.bytes_in_buffer
        else:
            return 0

    #===========================================================================
    # Drivers
    #===========================================================================

    def loadDriver(self, driverName=None):
        """
        Load a Model. VISA supports enumeration and will thus search for a
        compatible model. A Model name can be specified to load a specific model,
        even if it may not be compatible with this resource. Reloads model
        when importing, in case an update has occurred. If more than one
        compatible model is found, no model will be loaded
        
        `driverName` must be an importable module on the remote system. The
        base folder used to locate the module is the `models` folder.
        
        On startup, the resource will attempt to load a valid Model 
        automatically. This function only needs to be called to
        override the default model. :func:`unloadModel` must be called before
        loading a new model for a resource.
        
        :returns: True if successful, False otherwise
        """
        self.logger.debug("Searching for suitable drivers")

        if driverName is None:
            # Search for a compatible model
            validModels = []

            # Iterate through all Models to find compatible Models
            for modelModule, modelInfo in self.manager.drivers.items():
                try:
                    for resType in modelInfo.get('validResourceTypes'):
                        if resType in ['VISA', 'visa']:
                            if (self.VID in modelInfo.get('VISA_compatibleManufacturers') and
                                self.PID in modelInfo.get('VISA_compatibleModels')):
                                validModels.append(modelModule)
                                self.logger.debug("Found match: %s", modelModule)

                except:
                    continue

            # Only auto-load a model if a single model was found
            if len(validModels) == 1:
                Base_Resource.loadDriver(self, validModels[0])

                return True

            return False

        else:
            return Base_Resource.loadDriver(self, driverName)

