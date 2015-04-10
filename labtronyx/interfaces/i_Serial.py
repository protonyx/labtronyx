from Base_Interface import Base_Interface
from Base_Resource import Base_Resource

import importlib
import sys
import time

import serial
import serial.tools.list_ports
# list(serial.tools.list_ports.comports())

import common.resource_status as resource_status

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
                    
                res.stop()
                
            except:
                pass
            
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
                    new_resource = r_Serial(resID, self,
                                            logger=self.logger,
                                            config=self.config,
                                            enableRpc=self.manager.enableRpc)
                    self.resources[resID] = new_resource
                    
                    self.manager._cb_new_resource()

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

import common.status
        
class r_Serial(Base_Resource):
    type = "Serial"
    
    CR = '\r'
    LF = '\n'
    termination = CR + LF
        
    def __init__(self, resID, controller, **kwargs):
        Base_Resource.__init__(self, resID, controller, **kwargs)
        
        try:
            #conn = "\\.\%s" % resID
            self.instrument = serial.Serial(port=resID, timeout=0)
            
            self.logger.info("Identified new Serial resource: %s", resID)
            
            self.setResourceStatus(resource_status.READY)
            
            # Serial port is immediately opened on object creation
            self.instrument.close()
            
        except serial.SerialException as e:
            # Seems to be thrown on Windows systems
            self.setResourceStatus(common.status.error)
            self.setResourceError((e.errno, e.message))
            self.logger.error("Serial Error %s: %s", e.errno, e.message)
            
        except OSError as e:
            # Seems to be thrown on POSIX systems
            self.setResourceStatus(common.status.error)
            self.setResourceError((e.errno, e.strerror))
            self.logger.error("OS Error %s: %s", e.errno, e.strerror)
            
        except:
            self.logger.exception("Unhandled exception")
        
    #===========================================================================
    # Resource State
    #===========================================================================
        
    def open(self):
        self.instrument.open()
    
    def close(self):
        self.instrument.close()
        
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
        self.checkResourceStatus()
        
        for attempt in range(2):
            try:
                return self.instrument.write(data + self.termination)
            except SerialException as e:
                if e == serial.portNotOpenError:
                    self.open()
                else:
                    raise
                
    def write_raw(self, data):
        """
        Send Binary-encoded data to the instrument. Termination character is
        not included
        
        :param data: Data to send
        :type data: str
        :raises: ResourceNotReady
        """
        self.checkResourceStatus()
        
        for attempt in range(2):
            try:
                return self.instrument.write(data)
            except SerialException as e:
                if e == serial.portNotOpenError:
                    self.open()
                else:
                    raise
    
    def read(self, termination=None):
        """
        Read string data from the instrument.
        
        Reading stops when the device stops sending, or the termination 
        characters sequence was detected.
        
        All line-ending characters are stripped from the end of the string.
        """
        self.checkResourceStatus()
        
        ret = ''
        if termination is None:
            bytes = self.instrument.inWaiting()
            ret += self.instrument.read(bytes)
        
        else:
            ret += self.instrument.read(1)
            while ret[-1] != self.termination[-1] or self.instrument.inWaiting() == 0:
                ret += self.instrument.read(1)
            ret = ret[:-len(self.termination)]
                
        return ret
    
    def read_raw(self, size=None):
        """
        Read Binary-encoded data from the instrument.
        
        No termination characters are stripped.
        
        :param size: Number of bytes to read
        :type size: int
        :returns: bytes
        """
        ret = bytes()
        
        if size is None:
            bytes = self.instrument.inWaiting()
            ret += self.instrument.read(bytes)
            
        else:
            ret += self.instrument.read(size)
            
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
        self.checkResourceStatus()
        
        for attempt in range(2):
            try:
                self.write(data)
                if delay is not None:
                    time.sleep(delay)
                return self.read()
            except portNotOpenError:
                self.open()
    
    def inWaiting(self):
        """
        Return the number of bytes in the receive buffer
        
        :returns: int
        """
        return self.instrument.inWaiting()
    
        