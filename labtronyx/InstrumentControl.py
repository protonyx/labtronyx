import sys
# System Imports
import os
import importlib
import subprocess
import time
import logging
import logging.handlers
import socket

import common
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
        are trying to connect to. :func:`InstrumentControl.startManager` can be
        used to spawn a new process of InstrumentManager.
        
    """
    managers = {} # IP Address -> Manager RPC Client object
    hostnames = {} # Hostname => IP Address [Lookup table]
    
    # Resources
    resources = {}  # { Resource UUID -> RpcClient objects }
    properties = {} # { Resource UUID -> Properties (dict) }
    
    #instruments = {} # { Resource UUID -> RpcClient objects }
    
    def __init__(self, **kwargs):
        # Get the root path
        self.rootPath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir)))
        
        if not self.rootPath in sys.path:
            sys.path.append(self.rootPath)
            
        common_globals = common.ICF_Common()
        self.config = common_globals.getConfig()

         # Setup Logger
        if 'Logger' in kwargs or 'logger' in kwargs:
            self.logger = kwargs.get('Logger') or kwargs.get('logger')
        
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
                
        # Attempt to connect to the local manager
        if not self.addManager('localhost'):
            self.startManager()
            time.sleep(3.0)
            
        # Check the local Manager version
        localMan = self.getManager('localhost')
        
        try:
            localVer = localMan.getVersion()
            if localVer != self.config.version:
                # Version doesn't match, restart with new code from this release
                localMan.stop()
                time.sleep(1.0)
                self.startManager()
                time.sleep(2.0)
        except:
            pass
    
    #===========================================================================
    # Manager Operations    
    #===========================================================================
    
    def _resolveAddress(self, input):
        """
        Verify a IPv4 address from the input. Always returns an IPv4 Address or
        None
        
        :param input: IP Address or Hostname
        :type input: str
        :returns: str -- IPv4 Address
        """
        if input in self.hostnames:
            return self.hostnames.get(input)
        
        elif common.is_valid_ipv4_address(input):
            return input
        
        else:
            try:
                host = socket.gethostbyname(input)
            except:
                host = None
            finally:
                return host
    
    def getHostname(self, address):
        """
        Get the Hostname for the given address
        
        :param address: IP Address
        :type address: str - IPv4
        :returns: str
        """
        if address in self.managers.keys():
            man = self.managers.get(address)
            return man._getHostname() # RpcClient function
        
    def getConnectedAddresses(self):
        """
        Get a list of connected addresses
        
        :returns: list of connected addresses
        """
        return self.hostnames.values()
    
    def getConnectedHosts(self):
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
        local = self._resolveAddress('localhost')
        
        try:
            pyExec = sys.executable
            manPath = os.path.join(self.rootPath, 'InstrumentManager.py')
            
            subprocess.Popen([pyExec, manPath])
            
        except Exception as e:
            raise
    
    def stopManager(self, address, port=None):
        """
        Send a stop signal to a manager instance running on a local or remote
        machine.
        
        .. note::
           :class:`InstrumentManager` cannot be restarted once it is stopped
           
        :param address: IP Address or Hostname
        :type address: str
        :param port: Port
        :type port: int
        :returns: Nothing
        """
        address = self._resolveAddress(address)
        
        man = self.getManager(address)
        if man is not None:
            man.stop()
            self.removeManager(address)
        else:
            if self.addManager(address, port):
                man = self.getManager(address)
                man.stop()
                self.removeManager(address)
            else:
                # No manager could be found at the address:port
                pass
    
    def addManager(self, address, port=None):
        """
        Connect to a manager instance at the given address and port. If the
        connection is successful, the remote resources are automatically
        added to the pool of resources using :func:`refreshResources`
        
        :param address: IP Address or Hostname
        :type address: str
        :param port: Port
        :type port: int
        :returns: True if manager found, False if connection failed
        """
        address = self._resolveAddress(address)
        
        seekPort = port or self.config.managerPort
        
        if address not in self.managers.keys():
            # Attempt a connection
            try:
                testManager = RpcClient(address=address, port=seekPort)
                
                ver = testManager.getVersion()
                host = testManager._getHostname()
                
                self.hostnames[host] = address 
                self.managers[address] = testManager
                
                self.logger.info('Connected to InstrumentManager @ %s, version %s', address, ver)
                
                # Update the resource cache
                self.refreshResources(address)
                
                return True
                
            except:
                pass
        
        return False
    
    def removeManager(self, address):
        """
        Disconnect from the manager instance at `address` and purge all cached
        resources from that host.
        
        :param address: IP Address of manger
        :type address: str
        :returns: True unless there is no existing connection to `address`
        """
        address = self._resolveAddress(address)
        
        if address in self.managers.keys():
            # Remove all resources from that host
            cached_resources = self.resources.pop(address, {})
            
            for uuid, res in self.properties.items():
                self.properties.pop(uuid, None)
                self.resources.pop(uuid, None)
                
            # Remove host
            self.managers.pop(address, None)
            
            return True
        
        else:
            return False
        
    def getManager(self, address=None):
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
        if address is None:
            return self.managers
        
        else:
            address = self._resolveAddress(address)
                
            return self.managers.get(address, None)
    
    #===========================================================================
    # Interface Operations
    #===========================================================================
    
    def getInterfaces(self, address):
        """
        Get a list of controllers from a given InstrumentManager instance.
        
        :param address: IP Address
        :type address: str - IPv4
        :returns: dict
        """
        address = self._resolveAddress(address)
        
        if address in self.managers.keys():
            man = self.managers.get(address)
            return man.getInterfaces()

    #===========================================================================
    # Resource Operations
    #===========================================================================
        
    def refreshResources(self, address=None):
        """
        Refresh the local resource cache of all connected InstrumentManager
        instances. If an address is provided, only the specified cache will be
        refreshed.
        
        .. note::
           Use :func:`addManager` to establish a connection to a manager
           before calling this function.
        
        :param address: IP Address or Hostname
        :type address: str
        :returns: True unless there is no existing connection to `address`
        """
        if address is None:
            for addr in self.managers:
                self.refreshResources(addr)
                
            return True
                
        else:
            try:
                man = self.getManager(address)
                
                # Force a resource refresh
                man.refreshResources()
                remote_resources = man.getResources()
                
                for res_uuid, res_dict in remote_resources.items():
                    res_dict['address'] = address
                    res_dict['hostname'] = self.getHostname(address)
                    
                    self.properties[res_uuid] = res_dict
                        
                # Purge resources that are no longer in remote
                for res_uuid, res_dict in self.properties.items():
                    if res_dict.get('address') == address:
                        if res_uuid not in remote_resources:
                            self.properties.pop(res_uuid)
    
                return True
            
            except:
                self.logger.exception("Exception during refreshResource")
                return False
  
    def getResources(self):
        """
        Get a listing of all resources from all InstrumentManager instances.
        
        :returns: dict (Resource UUID as key)
        """
        return self.properties
    
    def getResourceProperties(self, res_uuid):
        """
        Get the resource property dictionary for a given UUID
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: dict
        """
        return self.properties.get(res_uuid, {})
    
    #===========================================================================
    # Resource Management
    #===========================================================================
    
    def addResource(self, address, controller, ResID):
        """
        Create a managed resource within a controller object
        
        If `controller` is not a valid controller on the remote manager instance,
        or if the controller does not support manually adding resources, this 
        function will return False. 
        
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
        
        :returns: bool - True if success, False otherwise
        """
        address = self._resolveAddress(address)
            
        if address in self.managers:
            man = self.managers.get(address)
            
            res = man.addResource(controller, ResID)
            
            # Update the local resource cache
            self.refreshResources(address)
            
            return res
        
        else:
            return False
    
    #===========================================================================
    # Drivers
    #===========================================================================
    
    def getDrivers(self, address):
        """
        Get the list of Models from an InstrumentManager instance
        
        :param address: IP Address of manager
        :type address: str
        
        :returns: list
        """
        address = self._resolveAddress(address)
            
        if address in self.managers:
            man = self.managers.get(address, None)
            
            if man is not None:
                return man.getDrivers()
            
            else:
                return []
            
        return []

    #===========================================================================
    # Instrument Operations
    #
    # Instruments are RPC Client objects to resources
    #===========================================================================
    
    def refreshInstrument(self, res_uuid):
        dev = self.getInstrument(res_uuid)
        dev._refresh()
    
    def getInstrument(self, res_uuid, **kwargs):
        """
        Create a :class:`RpcClient` instance that is linked to a resource on a
        local or remote machine.
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: RpcClient object or None if UUID does not match a valid resource
        """
        # Does an instrument already exist?
        instr = self.resources.get(res_uuid)
        
        if instr is not None:
            return instr
        
        else:
            # Create an RPC Client if one does not already exist
            res_dict = self.getResources().get(res_uuid)
            address = res_dict.get('address')
            port = res_dict.get('port')
            testInstrument = RpcClient(address=address, port=port)
            self.resources[res_uuid] = testInstrument
                
            return self.resources.get(res_uuid)
    
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
        return self.resources.values()
    
    def getInstrument_serial(self, serial_number):
        """
        Get a :class:`RpcClient` object for the resource with the given serial
        number.
        
        .. note::
        
            Only resources that have a model loaded will report a serial number.
        
        :returns: :class:`RpcClient` object
        """
        for res_uuid, prop_dict in self.getProperties().items():
            if prop_dict.get('deviceSerial', None) == serial_number:
                return self.getInstrument(res_uuid)
        
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
            if prop_dict.get('deviceModel', None) == model_number:
                ret.append(self.getInstrument(res_uuid))
                
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
            if prop_dict.get('deviceType', None) == d_type:
                ret.append(self.getInstrument(res_uuid))
                
        return ret
    
    def getInstrument_driver(self, d_driver):
        """
        Get a list of :class:`RpcClient` objects for resources with the given 
        device driver (Model).
        
        .. note::
        
            Only resources that have a model loaded will report a device type.
        
        :returns: list of :class:`RpcClient` objects
        """
        ret = []
        
        for res_uuid, prop_dict in self.getProperties().items():
            if prop_dict.get('modelName', None) == d_driver:
                ret.append(self.getInstrument(res_uuid))
                
        return ret
    
# Load GUI in interactive mode
if __name__ == "__main__":
    # Load Application GUI
    
    try:
        #sys.path.append("..")
        from application.a_Main import a_Main
        main_gui = a_Main()
        main_gui.mainloop()
         
    except Exception as e:
        print "Unable to load main application"
        raise
        sys.exit()
