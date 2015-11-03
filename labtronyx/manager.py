
# System Imports
import os
import socket
import threading

# Local Imports
from . import logger
from . import version

from . import bases
from . import common


class InstrumentManager(object):
    """
    Labtronyx InstrumentManager

    Facilitates communication with instruments using all available interfaces.

    :param server:         Enable RPC endpoint
    :type server:          bool
    :param server_port:    RPC endpoint port
    :type server_port:     int
    :param plugin_dirs:    List of directories containing plugins
    :type plugin_dirs:     list
    :param logger:         Logger
    :type logger:          Logging.logger object
    """
    name = 'Labtronyx'
    longname = 'Labtronyx Instrumentation Control Framework'

    SERVER_PORT = 6780
    ZMQ_PORT = 6781
    
    def __init__(self, **kwargs):
        # Configurable instance variables
        self.plugin_dirs = kwargs.get('plugin_dirs', [])
        self.server_port = kwargs.get('server_port', self.SERVER_PORT)
        self.logger = kwargs.get('logger', logger)

        # Initialize instance variables
        self._interfaces = {}  # Interface name -> interface object
        self._drivers = {}  # Module name -> Model info

        # Initialize PYTHONPATH
        self.rootPath = os.path.dirname(os.path.realpath(os.path.join(__file__, os.curdir)))
        # if self.rootPath not in sys.path:
        #     sys.path.append(self.rootPath)

        # Announce Version
        self.logger.info(self.longname)
        self.logger.info("Version: %s", version.ver_full)
        self.logger.debug("Build Date: %s", version.build_date)

        # Directories to search for plugins
        dirs = ['drivers', 'interfaces']
        dirs_res = [os.path.join(self.rootPath, dir) for dir in dirs] + self.plugin_dirs

        # Categorize plugins by base class
        cat_filter = {
            "drivers":      bases.DriverBase,
            "interfaces":   bases.InterfaceBase,
            "resources":    bases.ResourceBase,
            "scripts":      bases.ScriptBase
        }

        # Load Plugins
        self.plugin_manager = common.plugin.PluginManager(directories=dirs_res, categories=cat_filter, logger=self.logger)
        self.plugin_manager.search()

        # Validate plugins
        for plugin_name in self.plugin_manager.getAllPlugins().keys(): # Create a copy
            if not self.plugin_manager.validatePlugin(plugin_name):
                self.plugin_manager.disablePlugin(plugin_name)
        
        # Load Drivers
        self._drivers = self.plugin_manager.getPluginsByCategory('drivers')
        
        # Load Interfaces
        for interface_name in self.plugin_manager.getPluginsByCategory('interfaces'):
            self.enableInterface(interface_name)

        # Start Server
        if kwargs.get('server', False):
            if not self.server_start():
                raise EnvironmentError("Unable to start Labtronyx Server")
    
    def __del__(self):
        try:
            self.server_stop()
        except:
            pass

        self._close()

    def _close(self):
        """
        Close all resources and interfaces
        """
        # Disable all interfaces, close all resources
        for interface_name in self._interfaces.values(): # use values() so a copy is created
            self.disableInterface(interface_name)

    #===========================================================================
    # Labtronyx Server
    #===========================================================================

    def server_start(self, new_thread=True):
        """
        Start the API/RPC Server and Event publisher. If `new_thread` is True, the server will be started in a new
        thread in a non-blocking fashion.

        If a server is already running, it will be stopped and then restarted.

        :returns: True if successful, False otherwise
        """
        # Clean out old server, if any exists
        self.server_stop()

        # Start event publisher
        self._server_events = common.events.EventPublisher(self.ZMQ_PORT)
        self._server_events.start()

        # Create a server app
        self._server_app = common.server.create_server(self, self.server_port, logger=self.logger)

        # Server start command
        from werkzeug.serving import run_simple
        srv_start_cmd = lambda: run_simple(
            hostname='localhost', port=self.server_port, application=self._server_app,
            threaded=True, use_debugger=True
        )

        # Instantiate server
        if new_thread:
            server_thread = threading.Thread(name='Labtronyx-Server', target=srv_start_cmd)
            server_thread.start()

            return True

        else:
            try:
                srv_start_cmd()

            except:
                self.server_stop()

    def server_stop(self):
        """
        Stop the Server
        """
        # Signal the event
        self._publishEvent(common.events.EventCodes.manager.shutdown)

        # Stop the event publisher
        if hasattr(self, '_server_events'):
            try:
                self._server_events.stop()

            except:
                pass

            finally:
                del self._server_events

        # Shutdown server
        if hasattr(self, '_server_app'):
            try:
                # Must use the REST API to shutdown
                import urllib2
                url = 'http://{0}:{1}/api/shutdown'.format('localhost', self.server_port)
                resp = urllib2.Request(url)
                handler = urllib2.urlopen(resp)

                if handler.code == 200:
                    self.logger.debug('Server stopped')
                else:
                    self.logger.error('Server stop returned code: %d', handler.code)

            except:
                pass

            finally:
                del self._server_app

    @property
    def version(self):
        return version

    @staticmethod
    def getVersion():
        """
        Get the Labtronyx version
        
        :returns: str
        """
        return version.ver_full
    
    def getAddress(self):
        """
        Get the local IP Address

        :returns: str
        """
        return socket.gethostbyname(self.getHostname())
    
    def getHostname(self):
        """
        Get the local hostname

        :returns: str
        """
        return socket.gethostname()

    #===========================================================================
    # Event Publishing
    #===========================================================================

    def _publishEvent(self, event, *args, **kwargs):
        """
        Private method called internally to signal events. Calls handlers and dispatches event signal to subscribed
        clients

        :param event:   event
        :type event:    str
        """
        if hasattr(self, '_server_events'):
            self._server_events.publishEvent(event, *args, **kwargs)

    # ===========================================================================
    # Interface Operations
    # ===========================================================================

    @property
    def interfaces(self):
        return self._interfaces

    def _getInterface(self, interface_name):
        """
        Get an interface object with a given interface name. Used primarily in testing and debug, but can also be
        useful to access interface methods.

        :param interface_name:  Interface plugin name or InterfaceName attribute
        :type interface_name:   str
        :return:                object
        """
         # NON-SERIALIZABLE
        if interface_name not in self._interfaces:
            for interf_name, interf_cls in self._interfaces.items():
                if interf_cls.interfaceName == interface_name:
                    interface_name = interf_name

        return self._interfaces.get(interface_name)

    def listInterfaces(self):
        """
        Get a list of interfaces that are enabled
        
        :returns: list
        """
        return self._interfaces.keys()
    
    def enableInterface(self, interface_name, **kwargs):
        """
        Enable an interface for use. Requires a class object that extends InterfaceBase, NOT a class instance.

        :param interface_name:  Interface plugin name
        :type interface_name:   str
        :returns:               bool
        """
        int_cls = self.plugin_manager.getPlugin(interface_name)

        if int_cls is None:
            for interf_name, interf_cls in self.plugin_manager.getPluginsByCategory('interfaces').items():
                if interf_cls.interfaceName == interface_name:
                    interface_name = interf_name
                    int_cls = interf_cls
                    break

        if int_cls is not None:
            try:
                # If the interface is already enabled, disable the existing one
                self.disableInterface(interface_name)

                # Instantiate interface
                int_obj = int_cls(manager=self, logger=self.logger, **kwargs) # kwargs allows passing parameters to libs

                # Call the plugin hook to open the interface. Ensure interface opens correctly
                if int_obj.open():
                    self._interfaces[interface_name] = int_obj

                    self.logger.debug("Started Interface: %s", interface_name)
                    return True

                else:
                    self.logger.error("Interface %s failed to open", interface_name)
                    return False

            except NotImplementedError:
                return False

            except:
                self.logger.exception("Exception during interface open")
                return False
    
    def disableInterface(self, interface_name):
        """
        Disable an interface that is running.

        :param interface_name:  Interface plugin name
        :returns:               bool
        """
        if interface_name in self._interfaces:
            try:
                inter = self._interfaces.pop(interface_name)

                # Call the plugin hook to close the interface
                inter.close()

                self.logger.info("Stopped Interface: %s" % interface_name)

                return True

            except NotImplementedError:
                return False
                
            except:
                self.logger.exception("Exception during interface close")
                return False
        
    # ===========================================================================
    # Resource Operations
    # ===========================================================================
    
    def refresh(self):
        """
        Refresh all interfaces and resources. Attempts enumeration on all interfaces, then calls the `refresh`
        method for all resources.
        """
        for interf in self._interfaces.values():
            try:
                # Discover any new resources
                interf.refresh()
            except NotImplementedError:
                pass
    
    def getProperties(self):
        """
        Returns the property dictionaries for all resources
        
        :returns: dict
        """
        ret = {}

        for interface, interface_obj in self._interfaces.items():
            try:
                for resID, res in interface_obj.resources.items():
                    props = res.getProperties()

                    # UUID is not used to key properties within the interface
                    uuid = props.get('uuid', res.uuid)

                    ret[uuid] = props
                    ret[uuid].setdefault('deviceType', '')
                    ret[uuid].setdefault('deviceVendor', '')
                    ret[uuid].setdefault('deviceModel', '')
                    ret[uuid].setdefault('deviceSerial', '')
                    ret[uuid].setdefault('deviceFirmware', '')

            except NotImplementedError:
                pass
        
        return ret

    def _getResource(self, res_uuid):
        """
        Returns a resource object given the Resource UUID

        :param res_uuid:        Unique Resource Identifier (UUID)
        :type res_uuid:         str
        :returns:               object
        :raises:                KeyError if resource is not found
        """
         # NON-SERIALIZABLE
        for interf in self._interfaces.values():
            for resID, res in interf.resources.items():
                if res.uuid == res_uuid:
                    return res

        raise KeyError('Resource not found')
    
    def getResource(self, interface, resID, driverName=None):
        """
        Get a resource by name from the specified interface. Not supported by all interfaces, see interface
        documentation for more details.

        :param interface:       Interface name
        :type interface:        str
        :param resID:           Resource Identifier
        :type resID:            str
        :param driverName:      Driver to load for resource
        :type driverName:       str
        :returns:               Resource object
        :raises:                InterfaceUnavailable
        :raises:                ResourceUnavailable
        :raises:                InterfaceError
        """
         # NON-SERIALIZABLE
        int_obj = self._getInterface(interface)

        if int_obj is None:
            raise common.errors.InterfaceUnavailable('Interface not found')

        try:
            # Call the interface getResource hook
            res = int_obj.getResource(resID)

            # Attempt to load the specified driver, but do not force
            res.loadDriver(driverName)

            return res

        except NotImplementedError:
            raise common.errors.InterfaceError('Operation not support by interface %s' % interface)
    
    def findResources(self, **kwargs):
        """
        Get a list of resources/instruments that match the parameters specified.
        Parameters can be any key found in the resource property dictionary, such as these:

        :param uuid:            Unique Resource Identifier (UUID)
        :param interface:       Interface
        :param resourceID:      Interface Resource Identifier (Port, Address, etc.)
        :param resourceType:    Resource Type (Serial, VISA, etc.)
        :param deviceVendor:    Instrument Vendor
        :param deviceModel:     Instrument Model Number
        :param deviceSerial:    Instrument Serial Number
        :returns: list of objects
        """
        # NON-SERIALIZABLE
        matching_instruments = []
        
        prop = self.getProperties()
        
        for uuid, res_dict in prop.items():
            match = True
            
            for key, value in kwargs.items():
                if res_dict.get(key) != value:
                    match = False
                    break
                
            if match:
                try:
                    matching_instruments.append(self._getResource(uuid))
                except KeyError:
                    pass
                
        return matching_instruments
    
    def findInstruments(self, **kwargs):
        """
        Alias for :func:`findResources`
        """
        # NON-SERIALIZABLE
        return self.findResources(**kwargs)

    # ===========================================================================
    # Driver Operations
    # ===========================================================================

    @property
    def drivers(self):
        return self._drivers
                
    def listDrivers(self):
        """
        Get a list of loaded driver names. Returned names are the keys into the `driver` dictionary which contains the
        driver classes.

        :return: list
        """
        return self._drivers.keys()

    def getDriverInfo(self):
        """
        Get a dictionary of loaded driver info

        :return: dict
        """
        return {driver:self.plugin_manager.getPluginInfo(driver) for driver in self.drivers}