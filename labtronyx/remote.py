# System Imports

# Local Imports
try:
    from labtronyx.common.rpc import RpcClient, RpcServerNotFound
except ImportError:
    raise

__all__ = ['RemoteManager', 'RemoteResource']

class RemoteManager(RpcClient):
    """
    Labtronyx Remote Instrument Manager
    
    Subclass of RpcClient
    
    .. note::
       
       InstrumentManager must be running with RPC enabled on the computer that you are trying to connect to.
    """
    RPC_PORT = 6780

    def __init__(self, uri=None, **kwargs):
        host = kwargs.pop('host', 'localhost')
        port = kwargs.pop('port', self.RPC_PORT)

        if uri is None:
            uri = 'http://{0}:{1}/rpc'.format(host, port)

        super(RemoteManager, self).__init__(uri, **kwargs)

        self._resources = {}
        
        #self._enableNotifications()
        #self._registerCallback('event_new_resource', lambda: self.cb_event_new_resource())
        
    def refresh(self):
        """
        Query the InstrumentManager resources and create RemoteResource objects
        for new resources
        """
        self._rpcNotify('refresh')

        prop = self._rpcCall('getProperties')
        
        for res_uuid, res_dict in prop.items():
            if res_uuid not in self._resources:
                address = res_dict.get('address')
                port = res_dict.get('port')
                uri = "http://{0}:{1}/rpc/{2}".format(address, port, res_uuid)

                instr = RemoteResource(uri, timeout=self.timeout, logger=self.logger)
                self._resources[res_uuid] = instr
        
        # Purge resources that are no longer in remote
        for res_uuid in self._resources:
            if res_uuid not in prop:
                self._resources.pop(res_uuid)

    def _getResource(self, res_uuid):
        """
        Returns a resource object given the Resource UUID
                
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: RemoteResource object
        """
        if res_uuid in self._resources:
            return self._resources.get(res_uuid)
        
        else:
            self.refresh()
            return self._resources.get(res_uuid)
    
    def getResource(self, interface, resID, driverName=None):
        self._rpcNotify(interface, resID, driverName)

        res_list = self.findResources(interface=interface, resID=resID)

        if len(res_list) > 0:
            return res_list[0]
    
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
        
        prop = self._rpcCall('getProperties')
        
        for uuid, res_dict in prop.items():
            match = True
            
            for key, value in kwargs.items():
                if res_dict.get(key) != value:
                    match = False
                    break
                
            if match:
                matching_instruments.append(self._getResource(uuid))
                
        return matching_instruments
    
    def findInstruments(self, **kwargs):
        """
        Alias for :func:`findResources`
        """
        return self.findResources(**kwargs)
    
class RemoteResource(RpcClient):
    
    def _handleException(self, exception_object):
        pass

