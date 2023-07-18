
import socket
from enum import Enum
from .iadapter import IAdapter

class IP(IAdapter):
    class Status(Enum):
        DISCONNECTED = 0
        CONNECTED = 1
    class Protocol(Enum):
        TCP = 0
        UDP = 1
    def __init__(self, descriptor : str, port = None, transport : Protocol = Protocol.TCP):
        """
        IP stack adapter

        Parameters
        ----------
        descriptor : str
            IP description
        port : int
            port used (optional, can be specified in descriptor)
        transport : Transport
            Transport protocol, TCP or UDP
        """
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(5)
        self._ip = descriptor # TODO : update this
        self._port = port
        self._status = self.Status.DISCONNECTED


    def flushRead(self):
        return super().flushRead()

    def open(self):
        self._socket.connect((self._ip, self._port))
        self._status = self.Status.CONNECTED

    def close(self):
        self._socket.close()
            
    def write(self, data : bytearray):
        if self._status == self.Status.DISCONNECTED:
            self.open()
        self._socket.send(data)

    def read(self, ):
        if self._status == self.Status.DISCONNECTED:
            self.open()
        
        self._socket.settimeout(5)

        buffer = b''
        while True:
            try:
                recv = self._socket.recv(10)
                self._socket.settimeout(0.05)
                buffer += recv
            except TimeoutError:
                break
        return buffer