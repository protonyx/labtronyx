import threading
import zmq
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

                    msg_obj = EventMessage(msg)

                    self.logger.debug("Received event: %s", msg_obj.event)

                    self.handleMsg(msg_obj)

        self._socket.close()

    def connect(self, host):
        """
        Connect to a remote event publisher

        :param host:        Hostname or IP Address of remote host
        :type host:         str
        """
        uri = "tcp://{}:{}".format(host, self.ZMQ_PORT)
        self._socket.connect(uri)

    def disconnect(self, host):
        """
        Disconnect from a remote event publisher

        :param host:        Hostname or IP Address of remote host
        :type host:         str
        """
        uri = "tcp://{}:{}".format(host, self.ZMQ_PORT)
        self._socket.disconnect(uri)

    def handleMsg(self, event):
        """
        Default message handler. Dispatches events to registered callbacks. Overload in subclasses to change how
        messages are dispatched.

        :param event:       Event
        :type event:        EventMessage object
        """
        code = event.event

        if code in self._callbacks:
            self._callbacks.get(code)(event)

        else:
            if '' in self._callbacks:
                self._callbacks.get('')(event)

    def registerCallback(self, event, cb_func):
        """
        Register a function to be called when a particular event is received. An event of `''` will register a default
        callback

        :param event:       Event to register
        :type event:        str
        :param cb_func:     Function which takes parameters `event` (str) and `args` (dict)
        :type cb_func:      method
        """
        self._callbacks[event] = cb_func

    def stop(self):
        """
        Convenience function to stop the subscriber thread. Thread will automatically stop before garbage collection.
        """
        self._client_alive.clear()


class EventMessage(object):
    def __init__(self, json_msg):
        self.version = json_msg.get('labtronyx-version')

        self.hostname = json_msg.get('hostname')
        self.event = json_msg.get('event')

        self.args = json_msg.get('args', [])
        self.params = json_msg.get('params', {})

    def __len__(self):
        return len(self.args)

    def __getitem__(self, item):
        return self.args[item]

    def __getattr__(self, item):
        return self.params.get(item)


class EventCodes:
    class manager:
        shutdown = "manager.shutdown"
        heartbeat = "manager.heartbeat"

    class resource:
        created = "resource.created"
        destroyed = "resource.destroyed"
        changed = "resource.changed"

    class driver:
        loaded = "driver.loaded"
        unloaded = "driver.unloaded"