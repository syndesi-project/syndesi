import socket
from enum import Enum
from .iadapter import IAdapter
from ..tools.types import to_bytes
from .timeout import Timeout
from threading import Thread
from .timed_queue import TimedQueue
from typing import Union
import logging
from ..tools.logger import Logger

DEFAULT_RESPONSE_TIMEOUT = 1
DEFAULT_CONTINUATION_TIMEOUT = 1e-3
DEFAULT_TOTAL_TIMEOUT = 5

DEFAULT_BUFFER_SIZE = 1024

DEFAULT_TIMEOUT = Timeout(
                    response=DEFAULT_RESPONSE_TIMEOUT,
                    continuation=DEFAULT_CONTINUATION_TIMEOUT,
                    total=DEFAULT_TOTAL_TIMEOUT)

class IP(IAdapter):
    class Protocol(Enum):
        TCP = 'TCP'
        UDP = 'UDP'
    def __init__(self,
                address : str,
                port : int,
                transport : str = 'TCP',
                timeout : Union[Timeout, float] = DEFAULT_TIMEOUT,
                stop_condition = None,
                log_level : int = 0,
                buffer_size : int = DEFAULT_BUFFER_SIZE):
        """
        IP stack adapter

        Parameters
        ----------
        address : str
            IP description
        port : int
            IP port
        transport : str
            'TCP' or 'UDP'
        """
        super().__init__(timeout=timeout, stop_condition=stop_condition, log_level=log_level)
        self._transport = transport
        if transport == self.Protocol.TCP.value:
            self._logger.log_status("Setting up TCP IP adapter", 0)
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif transport == self.Protocol.UDP.value:
            self._logger.log_status("Setting up UDP IP adapter", 0)
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            raise ValueError("Invalid protocol")
        self._address = address
        self._port = port
        self._buffer_size = buffer_size
        

    def set_default_port(self, port):
        """
        Sets IP port if no port has been set yet.

        This way, the user can leave the port empty
        and the driver/protocol can specify it later
        
        Parameters
        ----------
        port : int
        """
        if self._port is None:
            self._port = port

    def open(self):
        self._socket.connect((self._address, self._port))
        self._status = self.Status.CONNECTED

    def close(self):
        if hasattr(self, '_socket'):
            self._socket.close()
            
    def write(self, data : Union[bytes, str]):
        data = to_bytes(data)
        if self._status == self.Status.DISCONNECTED:
            self._logger.log_status("Opening adapter for writing", 0)
            self.open()
        if self._logger:
            self._logger.log_write(data)
        self._socket.send(data)

    def _read_thread(self, socket : socket.socket, read_queue : TimedQueue):
        while True:
            try:
                payload = socket.recv(self._buffer_size)
                if len(payload) == self._buffer_size and self._transport == self.Protocol.UDP:
                    logging.warning("Warning, inbound UDP data may have been lost (max buffer size attained)")
            except OSError:
                break
            if not payload:
                break
            read_queue.put(payload)

    def _start_thread(self):
        self._thread = Thread(target=self._read_thread, daemon=True, args=(self._socket, self._read_queue))
        self._thread.start()

    def query(self, data : Union[bytes, str]):
        self.flushRead()
        self.write(data)
        return self.read()