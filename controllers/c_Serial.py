import importlib
import sys

import serial
import serial.tools.list_ports
# list(serial.tools.list_ports.comports())

import controllers

class c_Serial(controllers.c_Base):
    
    # Dict: ResID -> (VID, PID)
    resources = {}
    
    auto_load = False

    def open(self):
        return True
    
    def close(self):
        for resID, res in self.resources.items():
            try:
                if res.isOpen():
                    res.close()
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
        Scans system for new resources and creates resource objects for them.
        """
        try:
            res_list = list(serial.tools.list_ports.comports()) 
            
            # Check for new resources
            for res in res_list:
                resID, _, _ = res
                    
                if resID not in self.resources:
                    new_resource = r_Serial(resID, self)
                    self.resources[resID] = new_resource
                    
                    self.manager._notify_new_resource()

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


        
class r_Serial(controllers.r_Base):
    type = "Serial"
        
    def __init__(self, resID, controller):
        controllers.r_Base.__init__(self, resID, controller)
        
        try:
            self.instrument = serial.Serial(resID)
            
            self.logger.info("Identified new Serial resource: %s", resID)
            
        except serial.SerialException:
            pass
        except:
            pass
        
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
    # Data Transmission
    #===========================================================================
    
    def write(self, data):
        return self.instrument.write(data)
    
    def read(self, size=1):
        return self.instrument.read(size)
    
    def query(self, data):
        return self.instrument.query(data)
    
        