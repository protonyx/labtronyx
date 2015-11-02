from labtronyx.bases import InterfaceBase, ResourceBase
from labtronyx.common.errors import *

class r_Template(ResourceBase):
    type = ""
        
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
        # TODO
            
    def write_raw(self, data):
        # TODO
    
    def read(self, termination=None):
        # TODO                
    
    def read_raw(self, size=None):
        # TODO
    
    def query(self, data, delay=None):
        # TODO
    
    def inWaiting(self):
        # TODO
    
    