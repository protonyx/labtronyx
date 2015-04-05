import sys
# System Imports
import os
import importlib
import subprocess
import time
import logging
import logging.handlers
import socket

from RemoteManager import RemoteManager, RemoteInstrument

class LabManager(object):
    """
    LabManager is a helper class that provides functionality to 
    communicate with any number of local or remote InstrumentManager instances.  
    
    - Tracks multiple connected InstrumentManagers
    - Local cache of all resources from connected InstrumentManagers
    
    :param configFile: Configuration file to load
    :type configFile: str
    """
    managers = {} # IP Address -> Manager RPC Client object
    hostnames = {} # Hostname => IP Address [Lookup table]
    
    # Resources
    resources = {}  # { Resource UUID -> RemoteInstrument objects }
    properties = {} # { Resource UUID -> Properties (dict) }
    
    #instruments = {} # { Resource UUID -> RpcClient objects }
    
    def __init__(self, **kwargs):
        # Ensure library is present in PYTHONPATH
        self.rootPath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir)))
        
        if not self.rootPath in sys.path:
            sys.path.append(self.rootPath)
        
        # Load Config
        configFile = kwargs.get('configFile', 'default')
        try:
            cFile = importlib.import_module('config.%s' % configFile)
            self.config = cFile.Config()
        except Exception as e:
            print("FATAL ERROR: Unable to import config file")
            sys.exit()
                
        #=======================================================================
        # # Attempt to connect to the local manager
        # if not self.addManager('localhost'):
        #     self.startManager(kwargs.get('debug', False))
        #     time.sleep(3.0)
        #     
        # # Check the local Manager version
        # localMan = self.getManager('localhost')
        # 
        # try:
        #     localVer = localMan.getVersion()
        #     if localVer != self.config.version:
        #         # Version doesn't match, restart with new code from this release
        #         localMan.stop()
        #         time.sleep(1.0)
        #         self.startManager()
        #         time.sleep(2.0)
        # except:
        #     pass
        #=======================================================================
    
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

    def addManager(self, address, port=None):
        """
        Connect to a InstrumentManager instance at the given address and port. 
        If the connection is successful, the remote resources are automatically
        added to the pool of resources and their property dictionaries are
        cached.
        
        :param address: IP Address or Hostname of InstrumentManager
        :type address: str
        :param port: Port
        :type port: int
        :returns: True if successful, False otherwise
        """
        address = self._resolveAddress(address)
        
        seekPort = port or self.config.managerPort
        
        if address not in self.managers.keys():
            # Attempt a connection
            try:
                testManager = RemoteManager(address=address, port=seekPort)
                
                ver = testManager.getVersion()
                host = testManager.getHostname()
                address = testManager.getAddress()
                
                self.hostnames[host] = address 
                self.managers[address] = testManager
                
                # Update the resource cache
                self.refreshManager(address)
                
                return True
                
            except:
                return False
        
        else:
            return False
    
    def refreshManager(self, address):
        """
        Refresh the property cache for all resources from the Instrument
        Manager at the given address
        
        :param address: IP Address of InstrumentManager
        :type address: str
        """
        address = self._resolveAddress(address)
        
        man = self.managers.get(address)
        
        # Clear out all cached properties from this manager
        dev_list = [x.get('uuid') for x in self.resources]
        
        for uuid in dev_list:
            self.properties.pop(uuid, None)
        
        # Get the property dictionaries for the manager
        man_resources = man.getProperties()
        
        self.properties.update(man_resources)
    
    def removeManager(self, address):
        """
        Disconnect from the InstrumentManager at the given address and purge all 
        resources and cached properties from that host.
        
        :param address: IP Address of InstrumentManager
        :type address: str
        :returns: True if successful, False otherwise
        """
        address = self._resolveAddress(address)
        
        if address in self.managers.keys():
            # Clear out all cached properties from this manager
            dev_list = [x.get('uuid') for x in self.resources]
            
            for uuid in dev_list:
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
           
           This will always return an :class:`RemoteManager` object, even
           if the InstrumentManager instance is on the local machine.
           
        :param address: IP Address of manger
        :type address: str
        :returns: :class:`RemoteManager` object or None if there is no \
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
    
    def getResource(self, res_uuid):
        """
        Create a :class:`RemoteInstrument` instance that is linked to a resource on a
        local or remote machine.
        
        
        Get a listing of all resources from all InstrumentManager instances.
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: RpcClient object or None if UUID does not match a valid resource
        """
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
        pass
    
    def getInstrument(self, res_uuid):
        """
        Alias for :func:`getResource`
        """
        return self.getResource(res_uuid)
    
    def findResources(self, **kwargs):
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
    
    def findInstruments(self, **kwargs):
        """
        Alias for :func:`findResources`
        """
        return self.findResources(**kwargs)
    
    def refreshResource(self, res_uuid):
        """
        Refresh the properties dictionary for all resources.
        
        :returns: True if successful, False if an error occured
        """
        if res_uuid in self.resources:
            self.properties[res_uuid] = self.resources.get(res_uuid).getProperties()

            return True
        
        else:
            return False
        
    def refreshInstrument(self, res_uuid):
        """
        Alias for :func:`refreshResource`
        """
        return self.refreshResource(res_uuid)
    
    def pruneResources(self):
        """
        TODO
        """
        # Purge resources that are no longer in remote
        for res_uuid, res_dict in self.properties.items():
            if res_dict.get('address') == address:
                if res_uuid not in remote_resources:
                    self.properties.pop(res_uuid)
        
    #===========================================================================
    # Properties
    #===========================================================================
    
    def getProperties(self, res_uuid=None):
        """
        Get information about all resources. If Resource UUID is provided, a
        dictionary with all resources will be returned, nested by UUID
        
        :param res_uuid: Unique Resource Identifier (UUID) (Optional)
        :type res_uuid: str
        :returns: dict
        """
        if res_uuid is None:
            return self.properties
        
        else:
            return self.properties.get(res_uuid, {})
        

    

    
 