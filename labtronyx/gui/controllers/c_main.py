__author__ = 'kkennedy'

import socket

import labtronyx
from . import BaseController, ManagerController


class MainApplicationController(BaseController):

    def __init__(self):
        BaseController.__init__(self)

        self.event_sub = labtronyx.EventSubscriber()
        self.event_sub.registerCallback('', self._handleEvent)

        self._hosts = {}

        # Get proper hostname for localhost
        local_hostname = self.networkHostname('127.0.0.1')

        if not self.add_host(local_hostname):
            try:
                # No local host found, lets start one
                local_host = labtronyx.InstrumentManager(server=True)
                new_controller = ManagerController(local_host)

                ip_address = self.resolveHost(local_hostname)
                self.event_sub.connect(ip_address)

                self._hosts[ip_address] = new_controller

            except Exception as e:
                pass

    def _stop(self):
        self.event_sub.stop()

    def _handleEvent(self, event):
        # Notify manager controllers
        for ip_address, man_con in self._hosts.items():
            man_con._handleEvent(event)

        # Notify views
        self.notifyViews(event)

    def resolveHost(self, host):
        """
        Resolve a host to an IPv4 address. If the host is already an IP address, it will be returned without modification

        :param host:    hostname or IP address
        :return:        IP address
        """
        try:
            socket.inet_aton(host)
            return host

        except socket.error:
            # Invalid address
            return socket.gethostbyname(host)

    def networkHostname(self, ip_address):
        return socket.gethostbyaddr(ip_address)[0]

    def add_host(self, hostname, port=None):
        """
        Add remote host

        :param hostname:
        :param port:
        :rtype: bool
        """
        ip_address = self.resolveHost(hostname)

        if ip_address not in self._hosts:
            try:
                remote = labtronyx.RemoteManager(host=ip_address, port=port, timeout=1.0)

                new_controller = ManagerController(remote)
                self.event_sub.connect(ip_address)

                self._hosts[ip_address] = new_controller

                return True

            except labtronyx.RpcServerNotFound:
                return False

        return False


    def remove_host(self, hostname):
        ip_address = self.resolveHost(hostname)

        if ip_address in self._hosts:
            host = self._hosts.pop(ip_address)
            del host

            self.event_sub.disconnect(ip_address)

    def get_host(self, hostname):
        """
        Get a manager controller for the given hostname or IP address

        :param hostname:    hostname or IP address
        :return:
        """
        ip_address = self.resolveHost(hostname)

        return self._hosts.get(ip_address)

    @property
    def hosts(self):
        return self._hosts

    def list_hosts(self):
        return self._hosts.keys()

    def get_resource(self, res_uuid):
        """
        Get a resource controller for the resource with the given UUID

        :param res_uuid:
        :return:
        """
        for ip_address, man_con in self._hosts.items():
            try:
                res = man_con.get_resource(res_uuid)
                if res is not None:
                    return res

            except Exception:
                pass