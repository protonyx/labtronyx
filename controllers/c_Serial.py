import sys
import serial

from . import c_Base

class c_Serial(c_Base):
    
    # Dict: ResID -> (VID, PID)
    resources = {}
    # Dict: ResID -> Serial Object
    devices = {}
    
    auto_load = False

    def open(self):
        return True
    
    def close(self):
        for dev in self.devices:
            try:
                if dev.isOpen():
                    dev.close()
            except:
                pass
    
    def getResources(self):
        return self.resources
    
    def canEditResources(self):
        return True
    
    #===========================================================================
    # Optional - Automatic Controllers
    #===========================================================================
    
    def refresh(self):
        """
        Lists serial ports
    
        :raises EnvironmentError: On unsupported or unknown platforms
        :returns: A list of available serial ports
        """
        if sys.platform.startswith('win'):
            ports = ['COM' + str(i + 1) for i in range(256)]
    
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this is to exclude your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
    
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
    
        else:
            raise EnvironmentError('Unsupported platform')
    
        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                self.resources[port] = ('', '')
                self.logger.debug('Found Serial Device %s', port)
            except (OSError, serial.SerialException):
                pass

    def _getInstrument(self, resID):
        """
        :returns: serial.Serial object
        """
        ser = self.devices.get(resID, None)
        
        if ser is None:
            ser = serial.Serial()
            ser.port = resID
            self.devices[resID] = ser
            
        return ser
        
                
        