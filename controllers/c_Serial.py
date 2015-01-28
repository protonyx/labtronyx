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
    
    e_alive = threading.Event()
    
    #===========================================================================
    # Controller Thread
    #===========================================================================
    
    def __thread_run(self):
        while(self.e_alive.isAlive()):
            
            try:
                res_list = list(serial.tools.list_ports.comports()) 
                
                # Check for new resources
                for res in res_list:
                    resID, _, _ = res
                        
                    if resID not in self.resources:
                        new_resource = r_Serial(resID, self)
                        self.resources[resID] = new_resource

            except:
                # Exception thrown when there are no resources
                self.logger.exception("Unhandled Exception occurred while creating new Serial resource: %s", resID)
            
            time.sleep(60.0)

    def open(self):
        try:
            self.e_alive.set()
            
            self.__controller_thread = threading.Thread(name="c_Serial", target=self.__thread_run)
            self.__controller_thread.run()
            
            return True
        
        except:
            self.logger.exception("Failed to initialize Serial Controller")
            self.e_alive.clear()
        
            return False
    
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


        
class r_Serial(controllers.r_Base):
    type = "Serial"
        
    def __init__(self, resID, controller):
        controllers.r_Base.__init__(self, resID, controller)
        
        self.instrument = serial.Serial()
        self.instrument.port = resID
        
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
    
        