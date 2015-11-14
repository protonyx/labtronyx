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
import labtronyx
from labtronyx.common import plugin

import time

import visa
import pyvisa
import pyvisa.constants
import pyvisa.resources


class i_VISA(labtronyx.InterfaceBase):
    """
    VISA Controller
    
    Wraps PyVISA. Requires a VISA driver to be installed on the system.
    """
    author = 'KKENNEDY'
    version = '1.0'
    interfaceName = 'VISA'
    enumerable = True

    def __init__(self, manager, **kwargs):
        # Allow the use of a custom library for testing
        self._lib = kwargs.pop('library', '')

        super(i_VISA, self).__init__(manager, **kwargs)

        # Instance variables
        self.__resource_manager = None

    def open(self):
        """
        Initialize the VISA Interface. Instantiates a VISA Resource Manager.

        :returns: True if successful, False if an error occurred
        """
        try:
            # Load the VISA Resource Manager
            self.__resource_manager = visa.ResourceManager(self._lib)

            # Announce details about the VISA driver
            import pyvisa.util
            self.logger.debug("PyVISA Debug information\n%s", pyvisa.util.get_debug_info(False))

            return True

        except OSError as e:
            # No VISA library on the computer
            self.logger.error("No VISA Library found on the computer")

        except Exception as e:
            self.logger.exception("Failed to initialize VISA Interface")

        return False

    def enumerate(self):
        """
        Identify all devices known to the VISA driver and create resource objects for valid resources
        """
        if self.__resource_manager is None:
            raise labtronyx.InterfaceError("Interface not open")

        self.logger.debug("Enumerating VISA interface")

        try:
            new_res_list = [res for res in self.__resource_manager.list_resources() if res not in self.resources_by_id]

            # Check for new resources
            for resID in new_res_list:
                try:
                    self.openResource(resID)

                except labtronyx.ResourceUnavailable:
                    pass

        except visa.VisaIOError as e:
            # Exception thrown when there are no resources
            self.logger.exception('VISA Exception during enumeration')

    def prune(self):
        """
        Close any resources that are no longer known to the VISA interface
        """
        if self.__resource_manager is None:
            raise labtronyx.InterfaceError("Interface not open")

        try:
            # Get a fresh list of resources
            res_list = self.__resource_manager.list_resources()
        except visa.VisaIOError:
            # Exception thrown when there are no resources
            res_list = []

        for res_uuid, res_obj in self.resources.items():
            resID = res_obj.resID

            if resID not in res_list:
                res_obj.close()

                self.manager.plugin_manager.destroyPluginInstance(res_uuid)
                self.manager._publishEvent(labtronyx.EventCodes.resource.destroyed, res_obj.uuid)

    @property
    def resources(self):
        return self.manager.plugin_manager.getPluginInstancesByBaseClass(r_VISA)

    @property
    def resources_by_id(self):
        return {res_obj.resID: res_obj for res_uuid, res_obj in self.resources.items()}

    @property
    def resource_manager(self):
        return self.__resource_manager

    def openResource(self, resID):
        """
        Attempt to open a VISA instrument. If successful, a VISA resource is added to the list of known resources and
        the object is returned.

        :return:        object
        :raises:        labtronyx.ResourceUnavailable
        :raises:        labtronyx.InterfaceError
        """
        # Instantiate the resource object
        res_obj = self.manager.plugin_manager.createPluginInstance(r_VISA.fqn,
                                                                   manager=self.manager,
                                                                   resID=resID,
                                                                   logger=self.logger
                                                                   )

        # Signal new resource event
        self.manager._publishEvent(labtronyx.EventCodes.resource.created, res_obj.uuid)

        return res_obj

    def getResource(self, resID):
        return self.openResource(resID)


class r_VISA(labtronyx.ResourceBase):
    """
    VISA Resource Base class.
    
    Wraps PyVISA Resource Class
    
    All VISA compliant devices will adhere to the IEEE 488.2 standard
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
    CONFIG_KEYS = ['timeout', 'chunk_size', 'encoding', 'query_delay', 'read_termination', 'write_termination',
        'baud_rate', 'break_length', 'data_bits', 'discard_null', 'parity', 'stop_bits', 'allow_dma', 'send_end']

    RES_TYPES = {
        pyvisa.constants.InterfaceType.gpib:    "GPIB",
        pyvisa.constants.InterfaceType.vxi:     "VXI",
        pyvisa.constants.InterfaceType.asrl:    "Serial",
        pyvisa.constants.InterfaceType.pxi:     "PXI",
        pyvisa.constants.InterfaceType.tcpip:   "TCPIP",
        pyvisa.constants.InterfaceType.usb:     "USB",
        pyvisa.constants.InterfaceType.firewire: "Firewire"
    }

    interfaceName = 'VISA'
    interface = plugin.PluginDependency(pluginType='interface', interfaceName='VISA')

    def __init__(self, manager, resID, **kwargs):
        assert(isinstance(manager, labtronyx.InstrumentManager))

        super(r_VISA, self).__init__(manager, resID, **kwargs)

        # Ensure dependency was resolved correctly
        if not isinstance(self.interface, i_VISA):
            raise labtronyx.InterfaceError("VISA Interface is not enabled")

        # Ensure resource doesn't already exist
        if len(manager.plugin_manager.searchPluginInstances(pluginType='resource', interfaceName='VISA',
                                                            resID=resID)) > 0:
            raise labtronyx.InterfaceError("Resource already exists")

        try:
            self.instrument = self.interface.resource_manager.open_resource(resID)

            self.logger.debug("Created VISA resource: %s", resID)

            # Instance variables
            self._identity = []
            self._conf = { # Default configuration
                          'read_termination': '\r',
                          'write_termination': '\r\n',
                          'timeout': 2000
                          }
            self._resourceType = self.RES_TYPES.get(self.instrument.interface_type, 'VISA')

            # Instrument is created in the open state, but we do not want to lock the VISA instrument
            self.close()

            # Set a flag to initialize the resource when it is used
            self.ready = False

        # except AttributeError:
        #     raise labtronyx.ResourceUnavailable('Invalid VISA Resource Identifier: %s' % resID)

        except visa.VisaIOError as e:
            if e.abbreviation in ["VI_ERROR_RSRC_BUSY",
                                  "VI_ERROR_RSRC_NFOUND",
                                  "VI_ERROR_TMO",
                                  "VI_ERROR_INV_RSRC_NAME"]:  # Returned by TekVISA

                raise labtronyx.ResourceUnavailable('VISA Resource Error: %s' % e.abbreviation)

            else:
                raise labtronyx.InterfaceError('VISA Interface Error: %s' % e.abbreviation)

    def getProperties(self):
        """
        Get the property dictionary for the VISA resource.

        :rtype: dict[str:object]
        """
        if not self.ready:
            self.identify()

        def_prop = labtronyx.ResourceBase.getProperties(self)
        def_prop.update({
            'resourceType': self._resourceType
        })

        # Set some default search parameters if driver has not already defined
        def_prop.setdefault('deviceVendor', self._VISA_vendor)
        def_prop.setdefault('deviceModel', self._VISA_model)
        def_prop.setdefault('deviceSerial', self._VISA_serial)
        def_prop.setdefault('deviceFirmware', self._VISA_firmware)

        return def_prop

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
        self._VISA_vendor = ''
        self._VISA_model = ''
        self._VISA_firmware = ''
        self._VISA_serial = ''

        try:
            # Set the timeout really low
            start_timeout = self.instrument.timeout
            self.instrument.timeout = 250
            #self.instrument.

            scpi_ident = self.query("*IDN?")
            self._identity = scpi_ident.strip().split(',')

            # Set the timeout back to what it was
            self.instrument.timeout = start_timeout

            if len(self._identity) >= 4:
                self._VISA_vendor = self._identity[0].strip()
                self._VISA_model = self._identity[1].strip()
                self._VISA_serial = self._identity[2].strip()
                self._VISA_firmware = self._identity[3].strip()

                self.logger.debug("Identified VISA Resource: %s", self.resID)
                self.logger.debug("Vendor: %s", self._VISA_vendor)
                self.logger.debug("Model:  %s", self._VISA_model)
                self.logger.debug("Serial: %s", self._VISA_serial)
                self.logger.debug("F/W:    %s", self._VISA_firmware)

            else:
                self.logger.debug("VISA Resource responded to identify in non-standard way: %s", scpi_ident)

        except labtronyx.InterfaceTimeout:
            self.logger.debug("Resource did not respond to Identify: %s", self.resID)

        # Attempt to find a suitable driver if one is not already loaded
        if self._driver is None:
            self.loadDriver()

        if start_state == False:
            self.close()

        self.ready = True

    def getIdentity(self, section=None):
        """
        Get the comma-delimited identity string returned from `*IDN?` command on resource enumeration

        :param section: Section of comma-split identity
        :type section:  int
        :rtype:         str
        """
        if not self.ready:
            self.identify()

        if section is None:
            return self._identity
        elif len(self._identity) > section:
            return self._identity[section]
        else:
            return ''

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
        :raises:        labtronyx.ResourceUnavailable
        """
        try:
            self.instrument.open()

            # Restore instrument context
            self.configure()

        except visa.VisaIOError as e:
            raise labtronyx.ResourceUnavailable('VISA resource error: %s' % e.abbreviation)

        # Call the base resource open function to call driver hooks
        return labtronyx.ResourceBase.open(self)

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
            # Close the driver
            labtronyx.ResourceBase.close(self)

            try:
                # Close the instrument
                self.instrument.close()

            except visa.VisaIOError as e:
                self.logger.exception('VISA resource error on close: %s', e.abbreviation)
                return False

            except:
                return False

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
        :raises:            labtronyx.ResourceNotOpen
        :raises:            labtronyx.InterfaceError
        """
        try:
            self.instrument.write(data)

            self.logger.debug("VISA Write: %s", data)

        except visa.InvalidSession:
            raise labtronyx.ResourceNotOpen()

        except visa.VisaIOError as e:
            raise labtronyx.InterfaceError(e.description)

    def write_raw(self, data):
        """
        Send Binary-encoded data to the instrument without modification
        
        :param data:        Data to send
        :type data:         str
        :raises:            labtronyx.ResourceNotOpen
        :raises:            labtronyx.InterfaceError
        """
        try:
            self.instrument.write_raw(data)

            self.logger.debug("VISA Write: %s", data)

        except visa.InvalidSession:
            raise labtronyx.ResourceNotOpen()

        except visa.VisaIOError as e:
            raise labtronyx.InterfaceError(e.description)

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
        :raises:            labtronyx.ResourceNotOpen
        :raises:            labtronyx.InterfaceTimeout
        :raises:            labtronyx.InterfaceError
        """
        try:
            data = self.instrument.read(termination, encoding)

            self.logger.debug("VISA Read: %s", data)

            return data

        except visa.InvalidSession:
            raise labtronyx.ResourceNotOpen()

        except visa.VisaIOError as e:
            if e.abbreviation in ["VI_ERROR_TMO"]:
                raise labtronyx.InterfaceTimeout(e.description)
            else:
                raise labtronyx.InterfaceError(e.description)

    def read_raw(self, size=None):
        """
        Read Binary-encoded data directly from the instrument.
        
        :param size:        Number of bytes to read
        :type size:         int
        :raises:            labtronyx.ResourceNotOpen
        :raises:            labtronyx.InterfaceTimeout
        :raises:            labtronyx.InterfaceError
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
            raise labtronyx.ResourceNotOpen

        except visa.VisaIOError as e:
            if e.abbreviation in ["VI_ERROR_TMO"]:
                raise labtronyx.InterfaceTimeout(e.description)
            else:
                raise labtronyx.InterfaceError(e.description)

    def query(self, data, delay=None):
        """
        Retrieve ASCII-encoded data from the device given a prompt.
        
        A combination of write(data) and read()
        
        :param data:        Data to send
        :type data:         str
        :param delay:       delay (in seconds) between write and read operations.
        :type delay:        float
        :returns:           str
        :raises:            labtronyx.ResourceNotOpen
        :raises:            labtronyx.InterfaceTimeout
        :raises:            labtronyx.InterfaceError
        """
        try:
            ret_data = self.instrument.query(data)

            self.logger.debug("VISA Query: %s returned: %s", data, ret_data)

            return ret_data

        except visa.InvalidSession:
            raise labtronyx.ResourceNotOpen

        except visa.VisaIOError as e:
            if e.abbreviation in ["VI_ERROR_TMO"]:
                raise labtronyx.InterfaceTimeout(e.description)
            else:
                raise labtronyx.InterfaceError(e.description)

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
            driverClasses = self.manager.plugin_manager.getPluginsByType('driver')
            validDrivers = []

            # Iterate through all driver classes to find compatible driver
            for driver_fqn, driverCls in driverClasses.items():
                try:
                    if driverCls.VISA_validResource(self._identity):
                        validDrivers.append(driver_fqn)
                        self.logger.debug("Found match: %s", driver_fqn)
                except:
                    pass

            # Only auto-load a model if a single model was found
            if len(validDrivers) == 1:
                labtronyx.ResourceBase.loadDriver(self, validDrivers[0], force)
                return True

            else:
                self.logger.debug("Unable to load driver, more than one match found")
                return False

        else:
            return labtronyx.ResourceBase.loadDriver(self, driverName, force)