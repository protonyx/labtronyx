"""
VISA Interface module for Labtronyx

:codeauthor: Kevin Kennedy

Dependencies
------------

In order to use the VISA interface, a proper VISA driver must be installed.

The latest version of NI-VISA can be downloaded from `nivisa`_ .

.. _nivisa: http://www.ni.com/visa

Install NI-VISA using the instructions and ReadMe file included with the installer. NI-VISA is compatible with Windows,
Mac and Linux.
"""

from traceback import format_exc
import time

import visa
import pyvisa
import pyvisa.constants
import pyvisa.resources

from labtronyx.bases import Base_Interface, Base_Resource
from labtronyx.common.errors import *
import labtronyx.common as common

info = {
    # Interface Author
    'author':               'KKENNEDY',
    # Interface Version
    'version':              '1.0',
    # Revision date
    'date':                 '2015-10-05'
}


class i_VISA(Base_Interface):
    """
    VISA Controller
    
    Wraps PyVISA. Requires a VISA driver to be installed on the system.
    """

    info = {
        # Interface Name
        'interfaceName':    'VISA'
    }

    def __init__(self, manager, **kwargs):
        # Allow the use of a custom library for testing
        self._lib = kwargs.pop('library', '')

        Base_Interface.__init__(self, manager, **kwargs)

        # Instance variables
        self.resource_manager = None

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

        except OSError as e:
            # No VISA library on the computer
            self.logger.error("No VISA Library found on the computer")
            return False

        except Exception as e:
            self.logger.exception("Failed to initialize VISA Interface")
            return False

    def close(self):
        """
        Stops the VISA Interface. Frees all resources associated with the interface.
        """
        for resID, res in self._resources.items():
            try:
                if res.isOpen():
                    res.close()

            except:
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
                            self.getResource(res)

                        except ResourceUnavailable:
                            pass

            except visa.VisaIOError as e:
                # Exception thrown when there are no resources
                # TODO: only catch the specific error
                res_list = []

            except:
                self.logger.exception("Unhandled VISA Exception while enumerating resources")
                raise

    def prune(self):
        """
        Close any resources that are no longer known to the VISA interface
        """
        to_remove = []

        if self.resource_manager is not None:
            try:
                # Get a fresh list of resources
                res_list = self.resource_manager.list_resources()

                for resID in self._resources:
                    if resID not in res_list:
                        # Close this resource and remove from the list
                        resource = self._resources.get(resID)
                        to_remove.append(resID)

                        try:
                            # Resource is gone, so this will probably error
                            resource.close()
                        except:
                            pass

            except visa.VisaIOError:
                # Exception thrown when there are no resources
                pass

            except:
                self.logger.exception("Unhandled VISA Exception while pruning resources")
                raise

            for resID in to_remove:
                del self._resources[resID]

    def getResource(self, resID):
        """
        Attempt to open a VISA instrument. If successful, a VISA resource is added to the list of known resources and
        the object is returned.

        :return:        object
        :raises:        ResourceUnavailable
        :raises:        InterfaceError
        """
        try:
            instrument = self.resource_manager.open_resource(resID)

            # Instantiate the resource object
            new_resource = r_VISA(manager=self.manager,
                                  interface=self,
                                  resID=resID,
                                  visa_instrument=instrument,
                                  logger=self.logger)

            self._resources[resID] = new_resource

            # Signal new resource event
            self.manager._event_signal(common.constants.ResourceEvents.created)

            return new_resource

        except AttributeError:
            raise ResourceUnavailable('Invalid VISA Resource Identifier: %s' % resID)

        except visa.VisaIOError as e:
            if e.abbreviation in ["VI_ERROR_RSRC_BUSY",
                                  "VI_ERROR_RSRC_NFOUND",
                                  "VI_ERROR_TMO",
                                  "VI_ERROR_INV_RSRC_NAME"]: # Returned by TekVISA

                raise ResourceUnavailable('VISA Resource Error: %s' % e.abbreviation)

            else:
                raise InterfaceError('VISA Interface Error: %s' % e.abbreviation)


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

    resourceType = "VISA"

    CONFIG_KEYS = ['timeout', 'chunk_size', 'encoding', 'query_delay', 'read_termination', 'write_termination',
        'baud_rate', 'break_length', 'data_bits', 'discard_null', 'parity', 'stop_bits', 'allow_dma', 'send_end']

    def __init__(self, manager, interface, resID, **kwargs):
        self.instrument = kwargs.pop('visa_instrument')

        Base_Resource.__init__(self, manager, interface, resID, **kwargs)

        # Instance variables
        self._identity = []
        self._conf = { # Default configuration
                      'read_termination': '\r',
                      'write_termination': '\r\n',
                      'timeout': 2000
                      }

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
        """
        Refresh the resource. Attempts to re-identify the instrument and load a driver. If a driver is already loaded,
        it will not be unloaded.
        """
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

    def getIdentity(self):
        """
        Get the comma-delimited identity string returned from `*IDN?` command on resource enumeration

        :return:    str
        """
        return self._identity

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

    def getStatusByte(self):
        """
        Read the Status Byte Register (STB). Interpretation of the status byte varies by instrument

        :return:
        """
        return self.query('*STB?')

    def trigger(self):
        """
        Trigger the instrument using the common trigger command (*TRG). Behavior varies by instrument
        """
        self.write('*TRG')

    def reset(self):
        """
        Reset the instrument. Behavior varies by instrument, typically this will reset the instrument to factory
        default settings.
        """
        self.write('*RST')

    # ===========================================================================
    # Serial Specific
    # ===========================================================================

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

    def lineBreak(self, length):
        """
        Suspends character transmission and places the transmission line in a break state

        :param length:  Length of time to break
        :type length:   int
        """
        if type(self.instrument) == pyvisa.resources.serial.SerialInstrument:
            self.instrument.break_state = pyvisa.constants.LineState.asserted
            time.sleep(length)
            self.instrument.break_state = pyvisa.constants.LineState.unasserted

    # ===========================================================================
    # Resource State
    # ===========================================================================

    def open(self):
        """
        Open the resource and prepare to receive commands. If a driver is loaded, the driver will also be opened

        :returns:       True if successful, False otherwise
        :raises:        ResourceUnavailable
        """
        try:
            self.instrument.open()

            # Restore instrument context
            self.configure()

        except visa.VisaIOError as e:
            raise ResourceUnavailable('VISA resource error: %s' % e.abbreviation)

        # Call the base resource open function to call driver hooks
        return Base_Resource.open(self)

    def isOpen(self):
        """
        Query the VISA resource to find if it is open

        :return: bool
        """
        try:
            sess = self.instrument.session
            return True

        except visa.InvalidSession:
            return False

    def close(self):
        """
        Close the resource. If a driver is loaded, that driver is also closed

        :returns: True if successful, False otherwise
        """
        if self.isOpen():
            try:
                # Close the driver
                Base_Resource.close(self)

                # Close the instrument
                self.instrument.close()

                return True

            except:
                return False

        else:
            return True

    def lock(self):
        self.instrument.lock()

    def unlock(self):
        self.instrument.unlock()

    # ===========================================================================
    # Configuration
    # ===========================================================================

    def configure(self, **kwargs):
        """
        Configure resource parameters to alter transmission characteristics or data interpretation

        All VISA Resources

        :param timeout:             Command timeout
        :type timeout:              float
        :param write_termination:   Write termination
        :type write_termination:    str
        :param read_termination:    Read termination
        :type read_termination:     str
        :param query_delay:         Delay between write and read commands in a query
        :type query_delay:          int

        Serial Resources

        :param baud_rate:           Serial Baudrate. Default 9600
        :type baud_rate:            int
        :param data_bits:           Number of bits per frame. Default 8.
        :type data_bits:            int
        :param parity:              Data frame parity (None, Even, Odd, Mark or Space)
        :type parity:               str
        :param stop_bits:           Number of stop bits. Default 1
        :type stop_bits:            int
        :param break_length:        Duration of the break signal in milliseconds
        :type break_length:         int
        :param discard_null:        Discard NUL characters
        :type discard_null:         bool
        :param send_end:            Assert END during the transfer of the last byte of data in the buffer
        :type send_end:             bool

        Resource type dependent

        :param allow_dma:           Allow DMA transfer
        :type allow_dma:            bool
        :param chunk_size:          Data chunk size
        :type chunk_size:           int
        :param encoding:            Data encoding
        :type encoding:             str
        """

        # Apply any necessary conversions
        if 'timeout' in kwargs:
            # Timeout must be in milliseconds
            timeout = kwargs.get('timeout')
            if type(timeout) == float:
                # assume this is seconds
                timeout = int(timeout * 100)
                kwargs['timeout'] = timeout

        if 'parity' in kwargs:
            import pyvisa.constants as pvc
            parity_convert = {
                'N': pvc.Parity.none,
                'E': pvc.Parity.even,
                'M': pvc.Parity.mark,
                'O': pvc.Parity.odd,
                'S': pvc.Parity.space}
            kwargs['parity'] = parity_convert.get(kwargs.get('parity', 'N'))

        if 'baudrate' in kwargs:
            kwargs['baudrate'] = int(kwargs.get('baudrate'))

        if 'bytesize' in kwargs:
            kwargs['bytesize'] = int(kwargs.get('bytesize'))

        if 'stopbits' in kwargs:
            kwargs['stopbits'] = int(kwargs.get('stopbits'))

        # Save any new configuration keys
        self._conf.update(kwargs)

        # If resource is open, apply configuration
        if self.isOpen():
            for key, value in self._conf.items():
                if hasattr(self.instrument, key):
                    setattr(self.instrument, key, value)
                else:
                    self._conf.pop(key)

    def getConfiguration(self):
        """
        Get the resource configuration

        :return: dict
        """
        ret = {}

        for key in self.CONFIG_KEYS:
            if hasattr(self.instrument, key):
                ret[key] = getattr(self.instrument, key)

        return ret

    # ===========================================================================
    # Data Transmission
    # ===========================================================================

    def write(self, data):
        """
        Send ASCII-encoded data to the instrument. Termination character is appended automatically, according to
        `write_termination` property.
        
        :param data:        Data to send
        :type data:         str
        :raises:            ResourceNotOpen
        :raises:            InterfaceError
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
        Send Binary-encoded data to the instrument without modification
        
        :param data:        Data to send
        :type data:         str
        :raises:            ResourceNotOpen
        :raises:            InterfaceError
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
        
        Reading stops when the device stops sending, or the termination characters sequence was detected. All
        line-ending characters are stripped from the end of the string.
        
        :param termination: Line termination
        :type termination:  str
        :param encoding:    Encoding
        :type encoding:     str
        :return:            str
        :raises:            ResourceNotOpen
        :raises:            InterfaceTimeout
        :raises:            InterfaceError
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
        Read Binary-encoded data directly from the instrument.
        
        :param size:        Number of bytes to read
        :type size:         int
        :raises:            ResourceNotOpen
        :raises:            InterfaceTimeout
        :raises:            InterfaceError
        """
        ret = bytes()

        try:
            if type(self.instrument) == pyvisa.resources.serial.SerialInstrument:
                # There is a bug in PyVISA that forces a low-level call (hgrecco/pyvisa #93)
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
        Retrieve ASCII-encoded data from the device given a prompt.
        
        A combination of write(data) and read()
        
        :param data:        Data to send
        :type data:         str
        :param delay:       delay (in seconds) between write and read operations.
        :type delay:        float
        :returns:           str
        :raises:            ResourceNotOpen
        :raises:            InterfaceTimeout
        :raises:            InterfaceError
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

    # ===========================================================================
    # Drivers
    # ===========================================================================

    def loadDriver(self, driverName=None, force=False):
        """
        Load a Driver.

        VISA supports enumeration and will thus search for a compatible driver. A `driverName` can be specified to load
        a specific driver, even if it may not be compatible with this resource. If more than one compatible driver is
        found, no driver will be loaded.
        
        On startup, the resource will attempt to load a valid driver automatically. This function only needs to be
        called to override the default driver. :func:`unloadDriver` must be called before loading a new driver for a
        resource.

        :param driverName:      Driver name to load
        :type driverName:       str
        :returns:               True if successful, False otherwise
        """
        if driverName is None:
            self.logger.debug("Searching for suitable drivers")

            # Search for a compatible model
            validModels = []

            # Iterate through all driver classes to find compatible driver
            for driver, driverCls in self.manager.drivers.items():
                if hasattr(driverCls, 'VISA_validResource'):
                    if driverCls.VISA_validResource(self._identity):
                        validModels.append(driver)
                        self.logger.debug("Found match: %s", driver)

            # Only auto-load a model if a single model was found
            if len(validModels) == 1:
                Base_Resource.loadDriver(self, validModels[0], force)

                return True

            self.logger.debug("Unable to load driver, more than one match found")
            return False

        else:
            return Base_Resource.loadDriver(self, driverName, force)