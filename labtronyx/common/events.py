import threading
import zmq


class EventSubscriber(object):
    """
    Subscribe to events broadcast by the Labtronyx Server. Run asynchronously in a separate thread to prevent the need
    for continuous polling.

    :param host:        Hostname or IP address to connect to
    :type host:         str
    """
    ZMQ_PORT = 6781
    POLL_TIME = 100 # ms

    def __init__(self, host):
        self._callbacks = {}
        self._client_alive = threading.Event()

        # Connect ZMQ socket
        uri = "tcp://{}:{}".format(host, self.ZMQ_PORT)

        self._context = zmq.Context()
        self._socket = self._context.socket(zmq.SUB)
        self._socket.setsockopt(zmq.SUBSCRIBE, '')
        self._socket.connect(uri)

        # Start client thread
        self._client_thread = threading.Thread(name='EventSubscriber', target=self._client)
        self._client_thread.start()

        self._client_alive.wait(0.5)

    def __del__(self):
        self.stop()

    def _client(self):
        self._client_alive.set()

        while self._client_alive.is_set():
            in_waiting = self._socket.poll(self.POLL_TIME)

            if in_waiting > 0:
                for idx in range(in_waiting):
                    msg = self._socket.recv_json()
                    self._handleMsg(msg)

        self._socket.close()

    def _handleMsg(self, msg):
        event = msg.get('event')
        args = msg.get('args')

        if event in self._callbacks:
            self._callbacks.get(event)(args)

    def registerCallback(self, event, cb_func):
        """
        Register a function to be called when a particular event is received.

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