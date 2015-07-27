from labtronyx.bases.interface import Base_Interface, InterfaceError, InterfaceTimeout
from labtronyx.bases.resource import Base_Resource, ResourceNotOpen

import importlib
import sys
import time
import errno

import serial
import serial.tools.list_ports
# list(serial.tools.list_ports.comports())

import common.resource_status as resource_status
from serial.serialutil import SerialException

import common.status

class i_Serial(Base_Interface):
    
    info = {
        # Interface Author
        'author':               'KKENNEDY',
        # Interface Version
        'version':              '1.0',
        # Revision date
        'date':                 '2015-03-06'
    }
    
    # Dict: ResID -> (VID, PID)
    resources = {}
    
    REFRESH_RATE = 5.0 # Seconds

    def open(self):
        return True
    
    def close(self):
        for resID, res in self.resources.items():
            try:
                if res.isOpen():
                    res.close()
                    
            except:
                pass
            
            res.stop()
            
        return True
    
    def getResources(self):
        return self.resources
    
    #===========================================================================
    # Optional - Automatic Controllers
    #===========================================================================

    def refresh(self):
        """
        Scans system for new resources and creates resource objects for them.
        """
        try:
            res_list = list(serial.tools.list_ports.comports()) 
            
            # Check for new resources
            for res in res_list:
                resID, _, _ = res
                    
                if resID not in self.resources:
                    try:
                        instrument = serial.Serial(port=resID, timeout=0)
                        
                        new_resource = r_Serial(resID, self,
                                                instrument=instrument,
                                                logger=self.logger,
                                                config=self.config,
                                                enableRpc=self.manager.enableRpc)
                        self.resources[resID] = new_resource
                        
                        self.manager._cb_new_resource()    
                        
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
    
        except:
            # Exception thrown when there are no resources
            self.logger.exception("Unhandled Exception occurred while creating new Serial resource: %s", resID)
            
    #===========================================================================
    #     if sys.platform.startswith('win'):
    #         ports = ['COM' + str(i + 1) for i in range(256)]
    # 
    #     elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
    #         # this is to exclude your current terminal "/dev/tty"
    #         ports = glob.glob('/dev/tty[A-Za-z]*')
    # 
    #     elif sys.platform.startswith('darwin'):
    #         ports = glob.glob('/dev/tty.*')
    # 
    #     else:
    #         raise EnvironmentError('Unsupported platform')
    # 
    #     result = []
    #     for port in ports:
    #         try:
    #             s = serial.Serial(port)
    #             s.close()
    #             self.resources[port] = ('', '')
    #             self.logger.debug('Found Serial Device %s', port)
    #         except (OSError, serial.SerialException):
    #             pass
    #===========================================================================
        
class r_Serial(Base_Resource):
    type = "Serial"
    
    CR = '\r'
    LF = '\n'
    termination = CR + LF
        
    def __init__(self, resID, interface, instrument, **kwargs):
        Base_Resource.__init__(self, resID, interface, **kwargs)
        
        self.instrument = instrument
        
        self.logger.info("Created Serial resource: %s", resID)
        
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
        
        :param baudrate: Serial - Baudrate. Default 9600
        :param timeout: Read timeout
        :param bytesize: Serial - Number of bits per frame. Default 8.
        :param parity: Serial - Parity
        :param stopbits: Serial - Number of stop bits
        :param termination: Write termination
        """
        if 'baudrate' in kwargs:
            self.instrument.setBaudrate(int(kwargs.get('baudrate')))
            
        if 'timeout' in kwargs:
            self.instrument.setTimeout(float(kwargs.get('timeout')))
            
        if 'bytesize' in kwargs:
            self.instrument.setByteSize(int(kwargs.get('bytesize')))
            
        if 'parity' in kwargs:
            self.instrument.setParity(kwargs.get('parity'))
            
        if 'stopbits' in kwargs:
            self.instrument.setStopbits(int(kwargs.get('stopbits')))
            
        if 'termination' in kwargs:
            self.termination = kwargs.get('termination')
            
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
    
        