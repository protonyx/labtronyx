from Base_Resource import *

class r_Template(Base_Resource):
    type = ""
        
    def __init__(self, resID, interface, **kwargs):
        Base_Resource.__init__(self, resID, interface, **kwargs)
        
        # TODO
        
    #===========================================================================
    # Resource State
    #===========================================================================
        
    def open(self):
        # TODO
        
    def isOpen(self):
        # TODO
    
    def close(self):
        # TODO
        
    def lock(self):
        # TODO
        
    def unlock(self):
        # TODO
    
    #===========================================================================
    # Configuration
    #===========================================================================
    
    def configure(self, **kwargs):
        # TODO
            
    def getConfiguration(self):
        # TODO
        
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
        # TODO
            
    def write_raw(self, data):
        """
        Send Binary-encoded data to the instrument. Termination character is
        not included
        
        :param data: Data to send
        :type data: str
        :raises: ResourceNotReady
        """
        # TODO
    
    def read(self, termination=None):
        """
        Read string data from the instrument.
        
        Reading stops when the device stops sending, or the termination 
        characters sequence was detected.
        
        All line-ending characters are stripped from the end of the string.
        """
        # TODO                
    
    def read_raw(self, size=None):
        """
        Read Binary-encoded data from the instrument.
        
        No termination characters are stripped.
        
        :param size: Number of bytes to read
        :type size: int
        :returns: bytes
        """
        # TODO
    
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
        # TODO
    
    