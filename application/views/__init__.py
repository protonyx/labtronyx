
#import multiprocessing
import Tkinter as Tk
from common.rpc import RpcClient

class v_Base(Tk.Toplevel):
    
    def __init__(self, master, resource):
        Tk.Toplevel.__init__(self, master, padx=5, pady=5)
        
        self.__resource = resource
        
        # TODO: Remove this, deprecated
        self.model = resource
        
    def getResource(self):
        return self.__resource
            
    def run(self):
        raise NotImplementedError
    
    def _NotImplemented(self):
        raise NotImplementedError
    
    def methodWrapper(self, refObject, refMethod):
        if hasattr(refObject, refMethod):
            return getattr(refObject, refMethod)
        
        else:
            return self._NotImplemented