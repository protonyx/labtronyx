import threading
import zmq
from enum import Enum
import logging


class EventSubscriber(object):
    """
    Subscribe to events broadcast by the Labtronyx Server. Run asynchronously in a separate thread to prevent the need
    for continuous polling.

    :param host:        Hostname or IP address to connect to
    :type host:         str
    """
    ZMQ_PORT = 6781
    POLL_TIME = 100 # ms

    def __init__(self, **kwargs):
        self.logger = kwargs.get('logger', logging)

        self._callbacks = {}
        self._client_alive = threading.Event()

        # Create ZMQ context and socket
        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.SUB)
        self._socket.setsockopt(zmq.SUBSCRIBE, '')

        # Start client thread
        self._client_thread = threading.Thread(name='EventSubscriber', target=self._client)
        self._client_thread.start()

        # Give the thread time to start up
        self._client_alive.wait(1.0)

    def __del__(self):
        self.stop()

    def _client(self):
        self._client_alive.set()

        while self._client_alive.is_set():
            in_waiting = self._socket.poll(self.POLL_TIME)

            if in_waiting > 0:
                for idx in range(in_waiting):
                    msg = self._socket.recv_json()

                    event = msg.get('event')
                    args = msg.get('args')

                    self.logger.debug("Received event: %s", event)

                    self.handleMsg(event, args)

        self._socket.close()

    def connect(self, host):
        """
        Connect to a remote event publisher

        :param host:        Hostname or IP Address of remote host
        :type host:         str
        """
        uri = "tcp://{}:{}".format(host, self.ZMQ_PORT)
        self._socket.connect(uri)

    def handleMsg(self, event, args):
        """
        Default message handler. Dispatches events to registered callbacks. Overload in subclasses to change how
        messages are dispatched.

        :param event:       Event
        :type event:        str
        :param args:        Arguments
        :type args:         dict
        """
        if event in self._callbacks:
            self._callbacks.get(event)(args)

        else:
            if '' in self._callbacks:
                self._callbacks.get('')(args)

    def registerCallback(self, event, cb_func):
        """
        Register a function to be called when a particular event is received. An event of `''` will register a default
        callback

        :param event:       Event to register
        :type event:        str
        :param cb_func:     Function which takes a single parameter `args` (dict)
        :type cb_func:      method
        """
        self._callbacks[event] = cb_func

    def stop(self):
        """
        Convenience function to stop the subscriber thread. Thread will automatically stop before garbage collection.
        """
        self._client_alive.clear()


class ManagerEvents(Enum):

    shutdown = "MANAGER_SHUTDOWN"


class ResourceEvents(Enum):

    created = "RESOURCE_CREATED"

    destroyed = "RESOURCE_DESTROYED"

    status_changed = "RESOURCE_STATUS"

    driver_load = "DRIVER_LOADED"

    driver_unload = "DRIVER_UNLOADED"