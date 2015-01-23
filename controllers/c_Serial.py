import importlib
import sys
import serial
# import serial.tools.list_ports
# list(serial.tools.list_ports.comports())

from . import c_Base

class c_Serial(c_Base):
    
    # Dict: ResID -> (VID, PID)
    resources = {}
    
    # Dict: ResID -> Serial Object
    resourceObjects = {}
    
    auto_load = False

    def open(self):
        return True
    
    def close(self):
        for dev in self.resourceObjects:
            try:
                if dev.isOpen():
                    dev.close()
            except:
                pass
            
        return True
    
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

    def openResourceObject(self, resID, **kwargs):
        import serial
        
        resource = self.resourceObjects.get(resID, None)
        if resource is not None:
            return resource
        else:
            resource = serial.Serial()
            resource.port = resID
            self.resourceObjects[resID] = resource
            return resource
        
    def closeResourceObject(self, resID):
        resource = self.resourceObjects.get(resID, None)
        
        if resource is not None:
            resource.close()
            del self.resourceObjects[resID]
        
                
        