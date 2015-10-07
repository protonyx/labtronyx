"""
The Serial interface is a wrapper for the pyserial library.
"""

from labtronyx.bases.interface import Base_Interface
from labtronyx.bases.resource import Base_Resource
from labtronyx.common.errors import *
import labtronyx.common as common

import time
import errno

import serial
import serial.tools.list_ports
from serial.serialutil import SerialException

info = {
    # Interface Author
    'author':               'KKENNEDY',
    # Interface Version
    'version':              '1.0',
    # Revision date
    'date':                 '2015-10-05'
}


class i_Serial(Base_Interface):
    """
    Serial Interface

    Wraps PySerial.
    """
    
    info = {
        # Interface Name
        'interfaceName':    'Serial'
    }
    
    REFRESH_RATE = 5.0 # Seconds

    def open(self):
        return True
    
    def close(self):
        for resID, res in self._resources.items():
            try:
                if res.isOpen():
                    res.close()
                    
            except:
                pass
            
            res.stop()
            
        return True

    def enumerate(self):
        """
        Scans system for new resources and creates resource objects for them.
        """
        res_list = list(serial.tools.list_ports.comports())

        # Check for new resources
        for res in res_list:
            resID, _, _ = res

            if resID not in self._resources:
                try:
                    instrument = serial.Serial(port=resID, timeout=0)

                    new_resource = r_Serial(manager=self.manager,
                                            interface=self,
                                            resID=resID,
                                            instrument=instrument,
                                            logger=self.logger)
                    self._resources[resID] = new_resource

                    # Signal new resource event
                    self.manager._event_signal(common.constants.ResourceEvents.created)

                except serial.SerialException as e:
                    # Seems to be thrown on Windows systems
                    self.logger.exception("Serial Error %s: %s", e.errno, e.message)

                except OSError as e:
                    # Seems to be thrown on POSIX systems
                    if e.errno in [errno.EACCES, errno.EBUSY]:
                        pass
                        #self.logger.error("Serial OSError %s", e.errno)

                    else:
                        self.logger.exception("Unknown OSError Exception")

                except:
                    self.logger.exception("Unhandled Serial Exception while creating new resource %s", resID)
            
    def prune(self):
        """
        Remove any resources that are no longer found on the system
        """
        res_list = list(serial.tools.list_ports.comports())

        to_remove = []

        for resID in self._resources:
            if resID not in res_list:
                # Close this resource and remove from the list
                res = self._resources.get(resID)
                to_remove.append(resID)

                try:
                    # Resource is gone, so this will probably error
                    res.close()
                except:
                    pass

        for resID in to_remove:
            del self._resources[resID]

        
class r_Serial(Base_Resource):
    type = "Serial"
    
    CR = '\r'
    LF = '\n'
    termination = CR + LF
        
    def __init__(self, manager, interface, resID, **kwargs):
        Base_Resource.__init__(self, manager, interface, resID, **kwargs)
        
        self.instrument = kwargs.get('instrument')
        
        self.logger.debug("Created Serial resource: %s", resID)
        
        # Serial port is immediately opened on object creation
        self.close()
        
    #===========================================================================
    # Resource State
    #===========================================================================
        
    def open(self):
        try:
            self.instrument.open()
            
        except SerialException as e:
            #if e.errno in [errno.EACCES]:
            # Access Denied, the port is probably open somewhere else
            raise InterfaceError(e.message)
        
        except:
            raise InterfaceError("Unhandled Exception")
        
    def isOpen(self):
        try:
            return self.instrument._isOpen
        except:
            return False
    
    def close(self):
        try:
            self.instrument.close()
            
        except SerialException as e:
            #if e.errno in [errno.EACCES]:
            # Access Denied, the port is probably open somewhere else
            raise InterfaceError(e.message)
        
        except:
            raise InterfaceError("Unhandled Exception")
        
    def lock(self):
        pass
        
    def unlock(self):
        pass
    
    #===========================================================================
    # Configuration
    #===========================================================================
    
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
        return self.instrument.getSettingsDict()
        
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
        :raises: ResourceNotReady
        """
        try:
            self.logger.debug("Serial Write: %s", data)
            self.instrument.write(data + self.termination)
            
        except SerialException as e:
            if e == serial.portNotOpenError:
                raise ResourceNotOpen()
            else:
                raise InterfaceError()
            
    def write_raw(self, data):
        """
        Send Binary-encoded data to the instrument. Termination character is
        not included
        
        :param data: Data to send
        :type data: str
        :raises: ResourceNotReady
        """
        try:
            self.instrument.write(data)
            
        except SerialException as e:
            if e == serial.portNotOpenError:
                raise ResourceNotOpen()
            else:
                raise InterfaceError()
    
    def read(self, termination=None):
        """
        Read string data from the instrument.
        
        Reading stops when the device stops sending, or the termination 
        characters sequence was detected.
        
        All line-ending characters are stripped from the end of the string.
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
                raise InterfaceError()
                
    
    def read_raw(self, size=None):
        """
        Read Binary-encoded data from the instrument.
        
        No termination characters are stripped.
        
        :param size: Number of bytes to read
        :type size: int
        :returns: bytes
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
                raise ResourceNotOpen
            else:
                raise InterfaceError
    
    def query(self, data, delay=None):
        """
        Retreive ASCII-encoded data from the device given a prompt.
        
        A combination of write(data) and read()
        
        :param data: Data to send
        :type data: str
        :param delay: delay (in seconds) between write and read operations.
        :type delay: float
        :returns: str
        :raises: ResourceNotOpen
        """
        self.write(data)
        if delay is not None:
            time.sleep(delay)
        return self.read()
    
    def inWaiting(self):
        """
        Return the number of bytes in the receive buffer
        
        :returns: int
        """
        return self.instrument.inWaiting()
    
        