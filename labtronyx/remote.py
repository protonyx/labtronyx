# System Imports

# Local Imports
from . import common
from .common.rpc import RpcClient
from .common.errors import RpcServerException

__all__ = ['RemoteManager', 'RemoteResource']


class LabtronyxRpcClient(RpcClient):
    def _handleException(self, exception_object):
        if isinstance(exception_object, RpcServerException):
            exc_type, exc_msg = exception_object.message.split('|')

            if hasattr(common.errors, exc_type):
                raise getattr(common.errors, exc_type)(exc_msg)
            else:
                RpcClient._handleException(self, exception_object)

        else:
            RpcClient._handleException(self, exception_object)


class RemoteManager(LabtronyxRpcClient):
    """
    Labtronyx Remote Instrument Manager
    
    Connects to a InstrumentManager instance running on another computer. Requires the Labtronyx server to be running
    on the remote computer in order to connect.

    Required Parameters:

    :param host:        Hostname or IP Address of computer to connect to
    :type host:         str

    Optional Parameters:

    :param port:           TCP port to connect to
    :type port:            int
    :param timeout:        Request timeout (seconds)
    :type timeout:         float
    :param logger:         Logger
    :type logger:          logging.Logger
    """
    RPC_PORT = 6780

    def __init__(self, **kwargs):
        uri = kwargs.get('uri')
        host = kwargs.pop('host', 'localhost')
        port = kwargs.pop('port', self.RPC_PORT)
        if port is None:
            port = self.RPC_PORT

        if uri is None:
            uri = 'http://{0}:{1}/rpc'.format(host, port)

        super(RemoteManager, self).__init__(uri, **kwargs)

        self._remote_clients = {}
        self._properties = {}

        # Test the connection
        self._version = self._rpcCall('getVersion')

    def refresh(self):
        """
        Query the InstrumentManager resources and create RemoteResource objects
        for new resources
        """
        self._rpcCall('refresh')

        self._properties = self._rpcCall('getProperties')

        REMOTE_PLUGIN_MAP = {
            'resource':  RemoteResource,
            'interface': LabtronyxRpcClient,
            'script':    LabtronyxRpcClient
        }
        
        for plug_uuid, plug_props in self._properties.items():
            if plug_uuid not in self._remote_clients:
                uri = "http://{0}:{1}/rpc/{2}".format(self.host, self.port, plug_uuid)
                remote_class = REMOTE_PLUGIN_MAP.get(plug_props.get('pluginType'), LabtronyxRpcClient)
                self._remote_clients[plug_uuid] = remote_class(uri, timeout=self.timeout, logger=self.logger)
        
        # Purge resources that are no longer in remote
        for plug_uuid in self._remote_clients.keys():
            if plug_uuid not in self._properties:
                del self._remote_clients[plug_uuid]

    def _clients_by_type(self, pluginType):
        return {uuid: self._remote_clients.get(uuid) for uuid, props in self._properties.items()
                if props.get('pluginType') == pluginType}

    @property
    def scripts(self):
        return self._clients_by_type('script')

    @property
    def interfaces(self):
        return self._clients_by_type('interface')

    @property
    def resources(self):
        return self._clients_by_type('resource')
    
    def getResource(self, interface, resID, driverName=None):
        self._rpcNotify('getResource', interface, resID, driverName)

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
        props = self._rpcCall('getProperties')

        # Force resource plugin types
        kwargs['pluginType'] = 'resource'
        
        for res_uuid, res_dict in props.items():
            match = True
            
            for key, value in kwargs.items():
                if res_dict.get(key) != value:
                    match = False
                    break
                
            if match:
                if res_uuid in self.resources:
                    matching_instruments.append(self.resources.get(res_uuid))
                
        return matching_instruments
    
    def findInstruments(self, **kwargs):
        """
        Alias for :func:`findResources`
        """
        return self.findResources(**kwargs)


class RemoteResource(LabtronyxRpcClient):
    """
    Labtronyx Remote Resource

    Provides convenience properties `uuid`, `resID` and `driver` similar to BaseResource API.
    """

    def __init__(self, uri, **kwargs):
        LabtronyxRpcClient.__init__(self, uri, **kwargs)

    @property
    def properties(self):
        return self.getProperties()

    @property
    def uuid(self):
        return self.properties.get('uuid')

    @property
    def resID(self):
        return self.properties.get('resourceID')

    @property
    def driver(self):
        return self.properties.get('driver')