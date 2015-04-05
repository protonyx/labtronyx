
from common.rpc import RpcClient

class RemoteManager(RpcClient):
    """
    Labtronyx Remote Instrument Manager
    
    Subclass of RpcClient
    
    .. note::
       
       InstrumentManager must be running on the computer that you
       are trying to connect to. :func:`InstrumentControl.startManager` can be
       used to spawn a new process of InstrumentManager.
    """
    instruments = {}
    
    def __init__(self, address, port, **kwargs):
        RpcClient.__init__(self, address, port, **kwargs)
        
        man._enableNotifications()
        man._registerCallback('event_new_resource', lambda: self.cb_event_new_resource())
        
    def disconnect(self):
        pass
    
    def getResource(self):
        pass
    
    def getInstrument(self):
        return self.getResource()
    
    def findResources(self):
        pass
    
    def findInstruments(self):
        return self.findResources()
    
class RemoteInstrument(RpcClient):
    pass

