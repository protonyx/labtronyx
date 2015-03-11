
#import multiprocessing
import Tkinter as Tk
from common.rpc import RpcClient

class Base_Applet(Tk.Toplevel):
    
    def __init__(self, master, instrument):
        Tk.Toplevel.__init__(self, master, padx=5, pady=5)
        
        self.__instrument = instrument
        
    def getInstrument(self):
        return self.__instrument
            
    def run(self):
        raise NotImplementedError
    
    def _NotImplemented(self):
        raise NotImplementedError
    
    def methodWrapper(self, refObject, refMethod):
        if hasattr(refObject, refMethod):
            return getattr(refObject, refMethod)
        
        else:
            return self._NotImplemented