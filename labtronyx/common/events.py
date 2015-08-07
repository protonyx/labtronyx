
import SocketServer

class EventHandler(SocketServer.BaseRequestHandler):
    pass

class EventDispatcher(SocketServer.UDPServer):

    def subscribe(self, address):
        pass

    def unsubscribe(self, address):
        pass

    def signal(self, event_code, args):
        pass

