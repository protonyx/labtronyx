import sys
# System Imports
import os
import importlib
import subprocess
import time
import logging
import logging.handlers
import socket

from RemoteManager import RemoteManager

class LabManager(object):
    """
    LabManager is a helper class that provides functionality to 
    communicate with any number of local or remote InstrumentManager instances.  
    
    - Tracks multiple connected InstrumentManagers
    - Local cache of all resources from connected InstrumentManagers
    
    :param configFile: Configuration file to load
    :type configFile: str
    """
    managers = {} # IP Address -> RemoteManager object
    hostnames = {} # Hostname => IP Address [Lookup table]
    
    # Resources
    resources = {}  # { Resource UUID -> RemoteResource objects }
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
    
    def _resolveAddress(self, address):
        """
        Verify a IPv4 address from the input. Always returns an IPv4 Address or
        None
        
        :param address: IP Address or Hostname
        :type address: str
        :returns: str -- IPv4 Address
        """
        try:
            socket.inet_aton(address)
            return address
            
        except socket.error:
            # Invalid address
            return socket.gethostbyname(address)
    
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
                
            except Exception as e:
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
        man.refreshResources()
        
        # Refresh properties
        prop = man.getProperties()
        self.properties.update(prop)
        
        # Purge properties
        for res_uuid, res_dict in self.properties.items():
            if res_dict.get('address') == address and res_uuid not in prop:
                self.properties.pop(res_uuid)
        
        # Get resource objects
        for res_uuid in prop:
            self.resources[res_uuid] = man.getResource(res_uuid)
        
        # Purge resources that are no longer in remote
        for res_uuid in self.resources:
            if res_uuid not in self.properties:
                self.resources.pop(res_uuid)
    
    def removeManager(self, address):
        """
        Disconnect from the InstrumentManager at the given address and purge all 
        resources and cached properties from that host.
        
        :param address: IP Address of InstrumentManager
        :type address: str
        :returns: True if successful, False otherwise
        """
        address = self._resolveAddress(address)
        
        if address in self.managers:
            # Clear out all cached properties from this manager
            dev_list = [x.get('uuid') for x in self.properties if x.get('address') == address]
            
            try:
                for uuid in dev_list:
                    self.properties.pop(uuid, None)
                    self.resources.pop(uuid, None)
                    
                # Remove host
                man = self.managers.pop(address, None)
                man.disconnect()
                
            except:
                pass
            
            return True
        
        else:
            return False
        
    def getManager(self, address=None):
        """
        Get an InstrumentManager object for the host at `address`. Object
        returned is an :class:`RemoteManager` object that is linked to
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
        
    def refresh(self):
        """
        Refresh all managers and resources
        """
        for address, man in self.managers.items():
            self.refreshManager(address)

    #===========================================================================
    # Resource Operations
    #===========================================================================
    
    def getResource(self, res_uuid):
        """
        Create a :class:`RemoteResource` instance that is linked to a resource 
        on a local or remote machine.
        
        Get a listing of all resources from all InstrumentManager instances.
        
        :param res_uuid: Unique Resource Identifier (UUID)
        :type res_uuid: str
        :returns: RpcClient object or None if UUID does not match a valid resource
        """
        return self.resources.get(res_uuid)
    
    def getInstrument(self, res_uuid):
        """
        Alias for :func:`getResource`
        """
        return self.getResource(res_uuid)
    
    def findResources(self, **kwargs):
        """
        Get a list of instruments that match the parameters specified.
        Parameters can be any key found in the resource property dictionary.
        
        :param address: IP Address of host
        :param hostname: Hostname of host
        :param uuid: Unique Resource Identifier (UUID)
        :param interface: Interface
        :param resourceID: Interface Resource Identifier
        :param resourceType: Resource Type (Serial, VISA, etc.)
        :param deviceVendor: Instrument Vendor
        :param deviceModel: Instrument Model Number
        :param deviceSerial: Instrument Serial Number
        :returns: list
        """
        matching_instruments = []
        
        for res_uuid, res_dict in self.properties.items():
            match = True
            
            for key, value in kwargs.items():
                if res_dict.get(key) != value:
                    match = False
                    break
                
            if match:
                matching_instruments.append(self.getInstrument(res_uuid))
                
        return matching_instruments
    
    def findInstruments(self, **kwargs):
        """
        Alias for :func:`findResources`
        """
        return self.findResources(**kwargs)
    
    def refreshResource(self, res_uuid):
        """
        Refresh the properties dictionary for a given resource.
        
        :returns: True if successful, False otherwise
        """
        if res_uuid in self.resources:
            prop = self.resources.get(res_uuid).getProperties()
            self.properties[res_uuid] = prop

            return True
        
        else:
            return False
        
    def refreshInstrument(self, res_uuid):
        """
        Alias for :func:`refreshResource`
        """
        return self.refreshResource(res_uuid)
        
    #===========================================================================
    # Properties
    #===========================================================================
    
    def getProperties(self, res_uuid=None):
        """
        Get property dictionaries for all known resources, nested by Resource
        UUID.
        
        If Resource UUID is provided, the property dictionary for that resource
        will be returned.
        
        :param res_uuid: Unique Resource Identifier (UUID) (Optional)
        :type res_uuid: str
        :returns: dict
        """
        if res_uuid is None:
            return self.properties
        
        else:
            return self.properties.get(res_uuid, {})
 