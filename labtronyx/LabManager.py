import sys
# System Imports
import os
import importlib
import subprocess
import time
import logging
import logging.handlers
import socket


class LabManager(object):
    """
    LabManager is a helper class that provides functionality to 
    communicate with any number of local or remote InstrumentManager instances.  
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
            self.startManager(kwargs.get('debug', False))
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
    # Instrument Operations
    #
    # Instruments are RPC Client objects to resources
    #===========================================================================
    
    def refreshInstrument(self, res_uuid):
        dev = self.getInstrument(res_uuid)
        dev._refresh()
        
    def findInstrument(self, **kwargs):
        """
        Get a list of instruments that match the parameters specified.
        
        :param address: IP Address of host
        :param hostname: Hostname of host
        :param uuid: Unique Resource Identifier (UUID)
        :param interface: Interface
        :param resourceID: Interface Resource Identifier
        :param resourceType: Resource Type (Serial, VISA, etc.)
        :param deviceVendor: Instrument Vendor
        :param deviceModel: Instrument Model Number
        :param deviceSerial: Instrument Serial Number
        """
        matching_instruments = []
        
        for uuid, res_dict in self.properties.items():
            match = True
            
            for key, value in kwargs.items():
                if res_dict.get(key) != value:
                    match = False
                    break
                
            if match:
                matching_instruments.append(self.getInstrument(uuid))
                
        return matching_instruments
    
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
    
 