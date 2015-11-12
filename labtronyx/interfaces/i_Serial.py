"""
The Serial interface is a wrapper for the pyserial library.
"""

from labtronyx.bases import InterfaceBase, ResourceBase
from labtronyx.common.errors import *
import labtronyx.common as common

import time
import os
import errno

import serial
import serial.tools.list_ports
from serial.serialutil import SerialException


class i_Serial(InterfaceBase):
    """
    Serial Interface

    Wraps PySerial.
    """
    author = 'KKENNEDY'
    version = '1.0'
    interfaceName = 'Serial'
    enumerable = True

    def open(self):
        """
        Open the serial interface and enumerate all system serial ports

        :return:        bool
        """
        self.enumerate()

        return True
    
    def close(self):
        """
        Close all serial resources

        :return:        bool
        """
        for res_uuid, res_obj in self.resources.items():
            res_obj.close()

            self.manager.plugin_manager.destroyPluginInstance(res_uuid)

        return True

    def enumerate(self):
        """
        Scans system for new resources and creates resource objects for them.
        """
        self.logger.debug("Enumerating Serial interface")

        res_list = list(serial.tools.list_ports.comports())

        # Check for new resources
        for resID, _, _ in res_list:
            if resID not in self.resources_by_id:
                try:
                    self.getResource(resID)

                except ResourceUnavailable:
                    pass
            
    def prune(self):
        """
        Remove any resources that are no longer found on the system
        """
        res_list = [resID for resID, _, _ in serial.tools.list_ports.comports()]

        for res_uuid, res_obj in self.resources.items():
            resID = res_obj.resID

            if resID not in res_list:
                res_obj.close()

                self.manager.plugin_manager.destroyPluginInstance(res_uuid)
                self.manager._publishEvent(common.events.EventCodes.resource.destroyed, res_obj.uuid)

    @property
    def resources(self):
        return self.manager.plugin_manager.getPluginInstancesByBaseClass(r_Serial)

    @property
    def resources_by_id(self):
        return {res_obj.resID: res_obj for res_uuid, res_obj in self.resources.items()}

    def getResource(self, resID):
        """
        Attempt to open a Serial instrument. If successful, a serial resource is added to the list of known resources
        and the object is returned.

        :return:        object
        :raises:        ResourceUnavailable
        :raises:        InterfaceError
        """
        if resID in self.resources_by_id:
            raise InterfaceError("Resource instance already exists")

        try:
            instrument = serial.Serial(port=resID, timeout=0)

            res_obj = self.manager.plugin_manager.createPluginInstance(r_Serial.fqn, manager=self.manager,
                                                                       interface=self,
                                                                       resID=resID,
                                                                       instrument=instrument,
                                                                       logger=self.logger
                                                                       )

            # Signal new resource event
            self.manager._publishEvent(common.events.EventCodes.resource.created, res_obj.uuid)

            return res_obj

        except (serial.SerialException, OSError) as e:
            if os.name == 'nt':
                # Windows implementation of PySerial does not set errno correctly
                import ctypes
                e.errno = ctypes.WinError().errno

            if e.errno in [errno.ENOENT, errno.EACCES, errno.EBUSY]:
                raise ResourceUnavailable('Serial resource error: %s' % resID)

            else:
                raise InterfaceError('Serial interface error [%i]: %s' % (e.errno, e.message))

        
class r_Serial(ResourceBase):
    """
    Serial Resource Base class.

    Wraps PySerial

    Resource API is compatible with VISA resources, so any driver written for a VISA resource should also work for
    serial resources in the case that a VISA library is not available.
    """
    
    CR = '\r'
    LF = '\n'
    termination = CR + LF
        
    def __init__(self, manager, interface, resID, instrument, **kwargs):
        ResourceBase.__init__(self, manager, interface, resID, **kwargs)
        
        self.instrument = instrument
        
        self.logger.debug("Created Serial resource: %s", resID)
        
        # Serial port is immediately opened on object creation
        self.close()

    def getProperties(self):
        """
        Get the property dictionary for the Serial resource.

        :rtype: dict[str:object]
        """
        def_prop = super(r_Serial, self).getProperties()
        def_prop.update({
            'resourceType': 'Serial'
        })
        return def_prop
        
    #===========================================================================
    # Resource State
    #===========================================================================
        
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

        except SerialException as e:
            #if e.errno in [errno.EACCES]:
            # Access Denied, the port is probably open somewhere else
            raise ResourceUnavailable('Serial resource error: %s' % e.strerror)

        # Call the base resource open function to call driver hooks
        return ResourceBase.open(self)
        
    def isOpen(self):
        """
        Query the serial resource to find if it is open

        :return: bool
        """
        try:
            return self.instrument._isOpen
        except:
            return False
    
    def close(self):
        """
        Close the resource. If a driver is loaded, that driver is also closed

        :returns: True if successful, False otherwise
        """
        if self.isOpen():
            # Close the driver
            ResourceBase.close(self)

            try:
                # Close the instrument
                self.instrument.close()

            except SerialException:
                return False

        return True

    def lock(self):
        return False

    def unlock(self):
        return False
    
    # ===========================================================================
    # Configuration
    # ===========================================================================
    
    def configure(self, **kwargs):
        """
        Configure Serial port parameters for the resource.

        :param timeout:             Command timeout
        :type timeout:              int
        :param write_termination:   Write termination
        :type write_termination:    str
        :param baud_rate:           Serial Baudrate. Default 9600
        :type baud_rate:            int
        :param data_bits:           Number of bits per frame. Default 8.
        :type data_bits:            int
        :param parity:              Data frame parity (`N`one, `E`ven, `O`dd, `M`ark or `S`pace)
        :type parity:               str
        :param stop_bits:           Number of stop bits. Default 1
        :type stop_bits:            int
        """
        if 'baud_rate' in kwargs:
            self.instrument.setBaudrate(int(kwargs.get('baud_rate')))
            
        if 'timeout' in kwargs:
            self.instrument.setTimeout(float(kwargs.get('timeout')))
            
        if 'data_bits' in kwargs:
            self.instrument.setByteSize(int(kwargs.get('data_bits')))
            
        if 'parity' in kwargs:
            self.instrument.setParity(kwargs.get('parity'))
            
        if 'stop_bits' in kwargs:
            self.instrument.setStopbits(int(kwargs.get('stop_bits')))
            
        if 'write_termination' in kwargs:
            self.termination = kwargs.get('write_termination')
            
    def getConfiguration(self):
        """
        Get the resource configuration

        :return: dict
        """
        settings = self.instrument.getSettingsDict()

        return {
            'baud_rate':    settings.get('baudrate'),
            'data_bits':    settings.get('bytesize'),
            'parity':       settings.get('parity'),
            'stop_bits':    settings.get('stopbits'),
            'write_termination': self.termination,
            'timeout':      settings.get('timeout')
        }
        
    # ===========================================================================
    # Data Transmission
    # ===========================================================================


    
    def write(self, data):
        """
        Send ASCII-encoded data to the instrument. Includes termination character.
        
        Raises exception if the resource is not open
        
        :param data:    Data to send
        :type data:     str
        :raises:        ResourceNotOpen
        :raises:        InterfaceTimeout
        :raises:        InterfaceError
        """
        try:
            self.logger.debug("Serial Write: %s", data)
            self.instrument.write(data + self.termination)
            
        except SerialException as e:
            if e == serial.portNotOpenError:
                raise ResourceNotOpen()

            elif e == serial.writeTimeoutError:
                raise InterfaceTimeout()

            else:
                raise InterfaceError(e.strerror)
            
    def write_raw(self, data):
        """
        Send Binary-encoded data to the instrument. Termination character is
        not included
        
        :param data:    Data to send
        :type data:     str
        :raises:        ResourceNotOpen
        :raises:        InterfaceTimeout
        :raises:        InterfaceError
        """
        try:
            self.instrument.write(data)
            
        except SerialException as e:
            if e == serial.portNotOpenError:
                raise ResourceNotOpen()

            elif e == serial.writeTimeoutError:
                raise InterfaceTimeout()

            else:
                raise InterfaceError(e.strerror)
    
    def read(self, termination=None):
        """
        Read string data from the instrument.
        
        Reading stops when the device stops sending, or the termination 
        characters sequence was detected.
        
        All line-ending characters are stripped from the end of the string.

        :raises:        ResourceNotOpen
        """
        try:
            ret = ''
            
            if termination is None:
                bytes_waiting = self.instrument.inWaiting()
                ret += self.instrument.read(bytes_waiting)
            
            else:
                ret += self.instrument.read(1)
                while ret[-1] != self.termination[-1] or self.instrument.inWaiting() == 0:
                    ret += self.instrument.read(1)
                ret = ret[:-len(self.termination)]
        
            return ret
        
        except SerialException as e:
            if e == serial.portNotOpenError:
                raise ResourceNotOpen()
            else:
                raise InterfaceError(e.strerror)
    
    def read_raw(self, size=None):
        """
        Read Binary-encoded data from the instrument.
        
        No termination characters are stripped.
        
        :param size:    Number of bytes to read
        :type size:     int
        :returns:       bytes
        :raises:        ResourceNotOpen
        """
        try:
            ret = bytes()
            
            if size is None:
                size = self.instrument.inWaiting()
            
            ret += self.instrument.read(size)
            if len(ret) != len(size):
                raise InterfaceTimeout("Timeout before requested bytes could be read")
                
            return ret
        
        except SerialException as e:
            if e == serial.portNotOpenError:
                raise ResourceNotOpen()
            else:
                raise InterfaceError(e.strerror)
    
    def query(self, data, delay=None):
        """
        Retreive ASCII-encoded data from the device given a prompt.
        
        A combination of write(data) and read()
        
        :param data:    Data to send
        :type data:     str
        :param delay:   delay (in seconds) between write and read operations.
        :type delay:    float
        :returns:       str
        :raises:        ResourceNotOpen
        :raises:        InterfaceTimeout
        :raises:        InterfaceError
        """
        self.write(data)
        if delay is not None:
            time.sleep(delay)
        return self.read()
    
    def inWaiting(self):
        """
        Return the number of bytes in the receive buffer
        
        :returns:       int
        :raises:        InterfaceError
        """
        try:
            return self.instrument.inWaiting()

        except serial.SerialException as e:
            raise InterfaceError(e.strerror)

    def flush(self):
        """
        Flush the output buffer
        """
        try:
            return self.instrument.flush()

        except serial.SerialException as e:
            raise InterfaceError(e.strerror)