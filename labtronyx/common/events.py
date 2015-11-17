import threading
import zmq
import logging
import time
import socket

__all__ = ['EventPublisher', 'EventSubscriber', 'EventMessage', 'EventCodes']


class EventPublisher(object):
    """
    Event broadcast class for Labtronyx

    :param port:        Port to bind for event notifications
    :type port:         int
    """
    HEARTBEAT_FREQ = 60.0 # Send heartbeat once per minute

    def __init__(self, port):
        self.port = port
        self._zmq_context = zmq.Context()
        self._zmq_socket = None

        self._server_alive = threading.Event()
        self._server_alive.clear()

    def start(self):
        # Start ZMQ Event publisher
        self._zmq_socket = self._zmq_context.socket(zmq.PUB)
        self._zmq_socket.bind("tcp://*:{}".format(self.port))

        # Start heartbeat server
        heartbeat_srv = threading.Thread(name='Labtronyx-Heartbeat-Server', target=self._heartbeat_server)
        heartbeat_srv.setDaemon(True)
        heartbeat_srv.start()

    def _heartbeat_server(self):
        last_heartbeat = 0.0
        self._server_alive.set()

        while self._server_alive.isSet():
            if time.time() - last_heartbeat > self.HEARTBEAT_FREQ:
                self.publishEvent(EventCodes.manager.heartbeat)
                last_heartbeat = time.time()
            time.sleep(0.5) # Low sleep time to ensure we shutdown in a timely manor

    def stop(self):
        # Stop heartbeat server
        self._server_alive.clear()

        # Close ZMQ socket
        if self._zmq_socket is not None:
            self._zmq_socket.close()
            self._zmq_socket = None

    def publishEvent(self, event, *args, **kwargs):
        if self._zmq_socket is not None:
            self._zmq_socket.send_json({
                'labtronyx-event': '1.0',
                'hostname': socket.gethostname(),
                'event': str(event),
                'args': args,
                'params': kwargs
            })


class EventSubscriber(object):
    """
    Subscribe to events broadcast by the Labtronyx Server. Run asynchronously in a separate thread to prevent the need
    for continuous polling. Use `connect` to listen for notifications from a remote server. A single `EventSubscriber`
    object can listen to multiple servers.
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
        self.version = json_msg.get('labtronyx-event')

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

    class interface:
        created = "interface.created"
        destroyed = "interface.destroyed"
        changed = "interface.changed"

    class resource:
        created = "resource.created"
        destroyed = "resource.destroyed"
        changed = "resource.changed"
        driver_loaded = "resource.driver.loaded"
        driver_unloaded = "resource.driver.unloaded"

    class script:
        created = "script.created"
        changed = "script.changed"
        destroyed = "script.destroyed"
        finished = "script.finished"
        log = "script.log"