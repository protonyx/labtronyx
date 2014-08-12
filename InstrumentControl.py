import sys
# System Imports
import os
import importlib
import subprocess
import time
import logging
import logging.handlers

# Instrument Control Classes
import common
from common import is_valid_ipv4_address, resolve_hostname
from common.rpc import RpcClient

class InstrumentControl(object):
    """
    :param Logger: Logger instance if you wish to override the internal instance
    :type Logger: Logging.logger
    
    InstrumentControl is a helper class that provides functionality to 
    communicate with any number of local or remote InstrumentManager instances.
    
    InstrumentControl simplifies the process of writing test instrument
    automation and control scripts. This is accomplished by abstracting the
    communication with :class:`InstrumentManager` instances that contain the device
    interface code. 
    
    .. note::
        InstrumentManager must be running on the local or remote machine that you
        are trying to connect to. :func:`InstrumentControl.startWaitManager` can be
        used to spawn a new process of InstrumentManager.
        
    """
    managers = {} # IP Address -> Manager RPC Client object
    hostnames = {} # Hostname => IP Address [Lookup table]
    
    # Resources
    resources = {} # { Address -> { Resource UUID -> (Controller, ResourceID) } } 
    instruments = {} # { Resource UUID -> RpcClient objects }
    properties = {} # { Resource UUID -> Properties (dict) }
    
    def __init__(self, **kwargs):
        # Get the root path
        can_path = os.path.dirname(os.path.realpath(__file__)) # Resolves symbolic links
        rootPath = os.path.abspath(can_path)
        configPath = os.path.join(rootPath, 'config')
        configFile = os.path.join(configPath, 'default.py')
        
        try:
            import imp
            cFile = imp.load_source('default', configFile)
            self.config = cFile.Config()
            self.config.rootPath = rootPath
            
        except Exception as e:
            print("FATAL ERROR: Unable to import config file")
            sys.exit()

         # Setup Logger
        if 'Logger' in kwargs:
            self.logger = kwargs['Logger']
        
        else:
            #loggerList = logging.Logger.manager.loggerDict
            # Attach to the MTB/MIST logger if inside a test environment
            #if '__main__' in loggerList:
            #self.logger = logging.getLogger('__main__')
            
            self.logger = logging.getLogger(__name__)
            formatter = logging.Formatter(self.config.logFormat)
                    
             # Configure logging level
            self.logger.setLevel(self.config.logLevel_console)
                
            # Logging Handler configuration, only done once
            if self.logger.handlers == []:
                # Console Log Handler
                lh_console = logging.StreamHandler(sys.stdout)
                lh_console.setFormatter(formatter)
                lh_console.setLevel(self.config.logLevel_console)
                self.logger.addHandler(lh_console)
                
        # Attempt to start the local manager
        #self.startWaitManager()
                
        # Attempt to connect to the local manager
        #local = self.getAddressFromHostname('localhost')
        self.addManager('localhost')
        
        #=======================================================================
        # # Dependency Check
        # # Numpy
        # try:
        #     importlib.import_module('numpy')
        # except ImportError:
        #     self.logger.error('Unable to import Numpy. Non-fatal for the moment.')
        # # MatPlotLib
        # 
        # self.logger.info("Dependency check complete")
        #=======================================================================
    
    #===========================================================================
    # Manager Operations    
    #===========================================================================
    
    def getAddressFromHostname(self, hostname):
        """
        Resolves a hostname.
        
        :param hostname: Machine hostname to resolve
        :type hostname: str
        :returns: str -- IPv4 Address
        """
        addr = self.hostnames.get(hostname, None)
        if addr is None:
            addr = resolve_hostname(hostname)
            
        return addr
    
    def isConnectedHost(self, hostname):
        """
        Check if a given hostname is connected
        
        :param hostname: hostname to check
        :type hostname: str
        :returns: True is hostname if connected, False otherwise
        """
        if self.hostnames.get(hostname, None) is not None:
            return True
        else:
            return False
    
    def getHostnames(self):
        """
        Get a list of connected hostnames
        
        :returns: List of connected hostnames
        """
        return self.hostnames.keys()
    
    #===========================================================================
    # Local Manager Operations
    #===========================================================================
    
    def startManager(self):
        """
        Start a local instance of :class:`InstrumentManager` using 
        :func:`subprocess.Popen`.
        
        No attempt is made to check whether an :class:`InstrumentManager`
        process is already running. The default behavior for :class:'InstrumentManager'
        is to exit when the port is already in use.
        
        See :class:'InstrumentManager' documentation for more information. 
        
        .. note:: 
           This function does not block! If the :class:`InstrumentManager`
           instance is not fully initialized before attempting to connect to it,
           timeouts will occur. 
        """
        local = self.getAddressFromHostname('localhost')
        
        try:
            pyExec = sys.executable
            manPath = os.path.join(self.rootPath, 'InstrumentManager.py')
            
            subprocess.Popen([pyExec, manPath])
            
        except:
            pass
            
    def startWaitManager(self, timeout=10.0):
        """
        Start a local instance of :class:`InstrumentManager` using 
        :func:`subprocess.Popen`. This function will block until the manager is
        fully initialized. 
        
        See :func:`startManager` for more.
        
        :param timeout: Maximum number of seconds to wait before timeout occurs  
        :type timeout: float
        :returns: Nothing
        """
        local = self.getAddressFromHostname('localhost')
        
        self.startManager()
        
        tryTime = 0.0
        waitTime = 2.0
        
        while not self.managerRunning(local):
            tryTime += waitTime
            time.sleep(waitTime)
            if tryTime >= timeout:
                break
            
        self.addManager('localhost')
        
    def managerRunning(self, address, port=None):
        """
        Check if an :class:`InstrumentManager` instance is running. Attempts to
        open a socket to the provided address and port.
        
        :param address: IP Address to check
        :type address: str
        :param port: Port
        :type port: int
        :returns: True if running, False if not running
        """
        man = self.getManager(address)
        if man is not None:
            # Manager already connected
            return True
        else:
            # Try to connect to one
            if self.addManager(address, port):
                # Manager connected
                self.removeManager(address)
                return True
            else:
                # No manager could be found at the address:port
                return False
    
    def stopManager(self, address, port=None):
        """
        Send a stop signal to a manager instance running on a local or remote
        machine.
        
        .. note::
           :class:`InstrumentManager` cannot be restarted once it is stopped
           
        :param address: IP Address to check
        :type address: str
        :param port: Port
        :type port: int
        :returns: Nothing
        """
        man = self.getManager(address)
        if man is not None:
            man.rpc_stop()
            self.removeManager(address)
        else:
            if self.addManager(address, port):
                man = self.getManager(address)
                man.rpc_stop()
                self.removeManager(address)
            else:
                # No manager could be found at the address:port
                pass
    
    def addManager(self, address, port=None):
        """
        Connect to a manager instance at the given address and port. If the
        connection is successful, the remote resources are automatically
        added to the pool of resources using :func:`refreshManager`
        
        :param address: IP Address to check
        :type address: str
        :param port: Port
        :type port: int
        :returns: True if manager found, False if connection failed
        """
        
        seekPort = port or self.config.managerPort
        
        # Check address or resolve hostname
        if is_valid_ipv4_address(address):
            addr = address
        else:
            addr = resolve_hostname(address)
        
        # Attempt a connection
        try:
            testManager = RpcClient(address=addr, port=seekPort)
            if not testManager._ready():
                return False
        except:
            return False
        
        else:
            self.hostnames[testManager.hostname] = addr 
            self.managers[addr] = testManager
            self.refreshManager(addr)
            
        return True
        
    def refreshManager(self, address=None):
        """
        Refresh the cached resources for the manager at `address`. If no 
        address is provided, refreshes all resources across all managers
        
        .. note::
           Use :func:`addManager` to establish a connection to a manager
           before calling this function.
        
        :param address: IP Address to check
        :type address: str
        :returns: True unless there is no existing connection to `address`
        """
        
        if address in self.managers:
            man = self.managers.get(address)
            
            # Force a remote device scan
            man.refresh()
            
            # Get the list of resources for the address
            cached_resources = self.getResources(address)
            
            # Get resources from the remote manager
            remote_resources = man.getResources() or {}
            
            # Add new resources
            for res_uuid, res in remote_resources.items():
                if res_uuid not in cached_resources.keys():
                    # Expects res == (Controller, ResID, VID, PID)
                     self.resources[res_uuid] = (address,) + tuple(res)

            # Purge resources that are no longer available
            for res_uuid, res in cached_resources.items():
                if res_uuid not in remote_resources.keys():
                    self.resources.pop(res_uuid)

        elif address is None:
            for addr in self.managers:
                self.refreshManager(addr)
                 
        else:
            return False
        
        return True
    
    def removeManager(self, address):
        """
        Disconnect from the manager instance at `address` and purge all cached
        resources from that host.
        
        :param address: IP Address of manger
        :type address: str
        :returns: True unless there is no existing connection to `address`
        """
        if self.managers.has_key(address):
            # Remove all resources from that host
            cached_resources = self.resources.pop(address, {})
            
            for uuid, res in cached_resources.items():
                self.destroyInstrument(uuid)
                    
                self.properties.pop(uuid, None)
                
            # Remove host
            rpc_client = self.managers.pop(address, None)
            del rpc_client
            
            return True
        
        else:
            return False
        
    def getManager(self, address):
        """
        Get an InstrumentManager object for the host at `address`. Object
        returned is an :class:`common.rpc.RpcClient` object that is linked to
        a remote InstrumentManager instance.
        
        .. note::
           
           This will always return an :class:`common.rpc.RpcClient` object, even
           if the InstrumentManager instance is on the local machine.
           
        :param address: IP Address of manger
        :type address: str
        :returns: :class:`common.rpc.RpcClient` object or None if there is no \
        existing connection to `address`
        """
        return self.managers.get(address, None)

    #===========================================================================
    # Resource Operations
    #===========================================================================
        
    def getResources(self, address=None):
        """
        Get a listing of all cached resources from the given address or from all
        :class:`InstrumentManager` instances.
        
        .. note::
        
            `getResources` will not trigger a refresh on the InstrumentManager,
            so resources returned may not be valid
        
        :param address: IP Address of host (optional)
        :type address: str
        
        :returns: dict of tuples - { Resource UUID: \ 
                    (`address`, `controller`, `resourceID`, `VID`, `PID`) }
        """
        if address is not None:
            ret = {}
            
            if address in self.hostnames.values():
                
                for res_uuid, res in self.resources.items():
                    if res[0] is address:
                        ret[res_uuid] = res
                    
            return ret
    
        else:
            return self.resources
        
        #=======================================================================
        # # Iterate through all resources to find
        # for address in self.resources:
        #     addr_res = self.resources.get(address, {})
        #     for uuid, res in addr_res.items():
        #         if uuid == res_uuid:
        #             return res
        #         
        # return None
        #=======================================================================
        
    def getResource_address(self, res_uuid):
        """
        Get the address where a resource is located.
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: str - IP Address
        """
        if res_uuid in self.resources.keys():
            return self.resources.get(res_uuid)[0]
        
        else:
            return None
    
    def addResource(self, address, controller, ResID, VendorID, ProductID):
        """
        Create a managed resource within a controller object
        
        If `controller` is not a valid controller on the remote manager instance,
        or if the controller does not support manually adding resources, this 
        function will return False. 
        
        Additional keyword arguments may be necessary, depending on the
        requirements of the controller. See the controller documentation for
        further requirements.
        
        .. note::
        
            Controllers that rely on system resources such as VISA or serial
            can only communicate with devices that are known to the system.
            Controllers that have no way to scan or enumerate devices depend on
            this function to make it aware of the device. An example of this is
            a CAN bus-based Controller, which must know a device address before
            communication can be established.
        
        :param address: IP Address of manager
        :type address: str
        :param controller: Name of controller to attach new resource
        :type controller: str
        :param ResID: Resource Identifier
        :type ResID: str
        :param VendorID: Vendor Identifier for automatic model loading
        :type VendorID: str
        :param ProductID: Product Identifier for automatic model loading
        :type ProductID: str
        
        :returns: bool - True if success, False otherwise
        """
        if address in self.managers:
            man = self.managers.get(address)
            
            # Does manager support manually adding resources?
            if man.canEditResources(controller):
                man.addResource(controller, VendorID, ProductID)
            res_dict['address'] = address
            res_dict['hostname'] = self.managers.get(address).hostname
        
            self.resources[res_uuid] = res_dict
            return True
        
        else:
            return False
    
    def removeResource(self, res_uuid):
        """
        Remove a managed resource from a remote controller.
        
        Unlike :func:`addResource`, this function will find the IP Address and
        controller given `res_uuid`. If the resource cannot be found in the
        cache, this function will return False. 
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: bool - True if resource was removed, False otherwise
        """
        if self.resources.has_key(res_uuid):
            # Instrument may not exist, but just in case
            self.destroyInstrument(res_uuid)
            
            if self.resources.pop(res_uuid, None) is not None:
                return True
            
        return False

    #===========================================================================
    # Instrument Operations
    #
    # Instruments are RPC Client objects to local/remote instruments
    #===========================================================================
    
    def getInstrument(self, res_uuid):
        """
        Get an Instrument :class:`common.rpc.RpcClient` object that is linked
        to the remote model.
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: :class:`common.rpc.RpcClient` object or None if unable to \
        connect to Model
        """
        ret = self.instruments.get(res_uuid, None)
        
        if ret is None:
            ret = self.createInstrument(res_uuid)
            
        return ret
    
    def loadModel(self, res_uuid, modelName=None, className=None):
        """
        Signal the remote InstrumentManager to load a model for a given
        resource. The InstrumentManager will attempt to identify a compatible
        model to load automatically. To force load a particular model, provide
        a `modelName` and `className`.
        
        `modelName` must be an importable module on the remote system. The
        base folder used to locate the module is the `models` folder.
        
        On startup, the InstrumentManager will attempt to load models for all
        resources automatically. This function only needs to be called to
        override the default model. :func:`unloadModel` must be called before
        loading a new model for a resource.
        
        .. note::
        
            If the import fails on the remote InstrumentManager, an exception 
            will be logged (on the remote system), but this function will return
            False with no other indication. 
            
        Example::
        
            instr.loadModel('360ba14f-19be-11e4-95bf-a0481c94faff', 'Tektronix.Oscilloscope.m_DigitalPhosphor', 'm_DigitalPhosphor')
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :param modelName: Model package (Python module)
        :type modelName: str
        :param className: Class Name
        :type className: str
        :returns: bool - True if successful, False otherwise
        """
        res = self.resources.get(res_uuid, None)
        
        man = self.managers.get(res[0], None)
        
        if man is not None:
            return man.loadModel(res_uuid, modelName, className)
        
        else:
            return False
        
    def unloadModel(self, res_uuid):
        """
        Signal the remote InstrumentManager to unload the currently loaded
        model for a given resource. This function must be called before 
        :func:`loadModel`.
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: bool - True if successful, False otherwise
        """
        res = self.resources.get(res_uuid, None)
        
        man = self.managers.get(res[0], None)
        
        if man is not None:
            ret = man.unloadModel(res_uuid)
            self.refreshProperties(res_uuid)
            return ret
        
        else:
            return False
    
    def createInstrument(self, res_uuid):
        """
        Create a :class:`RpcClient` instance that is linked to a model on a
        local or remote machine. :func:`createInstrument` only works with
        resources that have models loaded. 
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: RpcClient object or None if no model is loaded for the resource
        """
        # Does an instrument already exist?
        instr = self.instruments.get(res_uuid, None)
        
        if instr is not None:
            return instr
        
        else:
            # Is it a valid res_uuid?
            if res_uuid not in self.resources.keys():
                return False
                
            # Find out where this resource is located
            res = self.resources.get(res_uuid, None)
            address = self.getResource_address(res_uuid)
            man = self.getManager(address)
                    
            if man is not None:
                res_model = man.getModelName(res_uuid)
                
                if res_model is not None:
                    # A model is loaded, get the port
                    # The manager will automatically start the RPC server
                    port = man.getModelPort(res_uuid)
                    
                    try:
                        testInstrument = RpcClient(address=address, port=port)
                        if testInstrument._ready():
                            self.instruments[res_uuid] = testInstrument
                            
                            self.refreshProperties(res_uuid)
                            
                            return testInstrument
                        
                        else:
                            return None
                    except:
                        return None
                    
                else:
                    # No model loaded for that resource
                    return None
                
            else:
                # The resource could not be located
                return None
    
    def destroyInstrument(self, res_uuid):
        """
        Destroys the local instance of an :class:`RpcClient` object linked to
        a local or remote model. 
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: bool - True if successful, False otherwise
        """
        instr = self.instruments.pop(res_uuid, None)
        if instr is not None:
            instr._close()
            del instr
            return True
        
        return False
    
    def refreshProperties(self, res_uuid=None):
        """
        Refresh the cached property dictionary for a given resource. If no
        Resource UUID is provided, all resources properties will be updated.
        
        .. note::
        
            Properties should be refreshed when loading a new Model for a 
            resource.
            
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: dict - updated resource properties
        """
        if res_uuid is None:
            for res_uuid, res in self.resources.items():
                # These dictionaries can be large, so update one at a time
                self.refreshProperties(res_uuid)
                    
            return self.properties
        
        elif res_uuid in self.resources.keys():
            # Get the manager object
            address = self.getResource_address(res_uuid)
            man = self.getManager(address)
            
            # Get the properties from the manager
            prop = man.getProperties(res_uuid)
            
            # Inject hostname and address
            ret['address'] = instr._getAddress()
            ret['hostname'] = instr._getHostname()
            
            # Cache the properties
            self.properties[res_uuid] = ret
            
            return ret
            
    def getProperties(self, res_uuid=None):
        """
        Get the cached property dictionary for a given resource. If no
        Resource UUID is provided, returns the resources properties for all
        resources in nested dictionaries by Resource UUID.
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: dict - updated resource properties or None if invalid UUID
        """
        if res_uuid in self.properties:
            return self.properties.get(res_uuid, None)
        
        else:
            return self.properties
    
    def getInstrument_list(self):
        """
        Get a list of :class:`RpcClient` objects for all resources with models
        loaded
        
        .. note::
        
            This function opens a socket to every known instrument with a Model
            loaded. This could use a lot of system resources both locally and
            on remote InstrumentManagers if you don't need them.
        
        :returns: list of :class:`RpcClient` objects
        """
        for address, man in self.managers.items():
            devices = man.getModels()
            for res_uuid in devices:
                self.createInstrument(res_uuid)
                
        return self.instruments.values()
    
    def getInstrument_serial(self, serial_number):
        """
        Get a :class:`RpcClient` object for the resource with the given serial
        number.
        
        .. note::
        
            Only resources that have a model loaded will report a serial number.
        
        :returns: :class:`RpcClient` object
        """
        for res_uuid, prop_dict in self.getProperties().items():
            if prop_dict['deviceSerial'] == serial_number:
                return self.createInstrument(res_uuid)
        
        return None
    
    def getInstrument_model(self, model_number):
        """
        Get a list of :class:`RpcClient` objects for resources with the given 
        model number.
        
        .. note::
        
            Only resources that have a model loaded will report a model number.
        
        :returns: list of :class:`RpcClient` objects
        """
        ret = []
        
        for res_uuid, prop_dict in self.getProperties().items():
            if prop_dict['deviceModel'] == model_number:
                ret.append(self.createInstrument(res_uuid))
                
        return ret
    
    def getInstrument_type(self, d_type):
        """
        Get a list of :class:`RpcClient` objects for resources with the given 
        device type.
        
        .. note::
        
            Only resources that have a model loaded will report a device type.
        
        :returns: list of :class:`RpcClient` objects
        """
        ret = []
        
        for res_uuid, prop_dict in self.getProperties().items():
            if prop_dict['deviceType'] == d_type:
                ret.append(self.createInstrument(res_uuid))
                
        return ret
    
# Load GUI in interactive mode
if __name__ == "__main__":
    pass
    # Load Application GUI
    #===========================================================================
    # try:
    #     #sys.path.append("..")
    #     from application.a_Main import a_Main
    #     main_gui = a_Main()
    #     
    # except Exception as e:
    #     print "Unable to load main application"
    #     raise
    #     sys.exit()
    #===========================================================================
