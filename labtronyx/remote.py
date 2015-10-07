# System Imports

# Local Imports
try:
    from ptxrpc import PtxRpcClient, RpcServerNotFound
except ImportError:
    raise

__all__ = ['RemoteManager', 'RemoteResource']

class RemoteManager(PtxRpcClient):
    """
    Labtronyx Remote Instrument Manager
    
    Subclass of RpcClient
    
    .. note::
       
       InstrumentManager must be running with RPC enabled on the computer that you are trying to connect to.
    """
    resources = {}
    
    def __init__(self, host='localhost', **kwargs):
        uri = kwargs.get('uri', 'http://%s:6780/' % host)

        super(RemoteManager, self).__init__(uri)
        
        #self._enableNotifications()
        #self._registerCallback('event_new_resource', lambda: self.cb_event_new_resource())
        
    def refresh(self):
        """
        Query the InstrumentManager resources and create RemoteResource objects
        for new resources
        """
        self.refresh()
        prop = self.getProperties()
        
        for res_uuid, res_dict in prop.items():
            if res_uuid not in self.resources:
                address = res_dict.get('address')
                port = res_dict.get('port')
                uri = "http://{0}:{1}/{2}".format(address, port, res_uuid)

                instr = RemoteResource(uri)
                self.resources[res_uuid] = instr
        
        # Purge resources that are no longer in remote
        for res_uuid in self.resources:
            if res_uuid not in prop:
                self.resources.pop(res_uuid)

    def refreshResources(self):
        self.refresh()

    def getResource(self, res_uuid):
        """
        Returns a resource object given the Resource UUID
                
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: RemoteResource object
        """
        if res_uuid in self.resources:
            return self.resources.get(res_uuid)
        
        else:
            self.refreshResources()
            return self.resources.get(res_uuid)
    
    def getInstrument(self, res_uuid):
        """
        Alias for :func:`getResource`
        """
        return self.getResource(res_uuid)
    
    def findResources(self, **kwargs):
        """
        Get a list of resources that match the parameters specified.
        Parameters can be any key found in the resource property dictionary.

        :param uuid: Unique Resource Identifier (UUID)
        :param interface: Interface
        :param resourceID: Interface Resource Identifier (Port, Address, etc.)
        :param resourceType: Resource Type (Serial, VISA, etc.)
        :param deviceVendor: Instrument Vendor
        :param deviceModel: Instrument Model Number
        :param deviceSerial: Instrument Serial Number
        :returns: list
        """
        matching_instruments = []
        
        prop = self.getProperties()
        
        for uuid, res_dict in prop.items():
            match = True
            
            for key, value in kwargs.items():
                if res_dict.get(key) != value:
                    match = False
                    break
                
            if match:
                matching_instruments.append(self.getResource(uuid))
                
        return matching_instruments
    
    def findInstruments(self, **kwargs):
        """
        Alias for :func:`findResources`
        """
        return self.findResources(**kwargs)
    
class RemoteResource(PtxRpcClient):
    
    def _handleException(self, exception_object):
        pass

