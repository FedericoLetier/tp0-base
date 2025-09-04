import logging

class Socket:
    def __init__(self, socket):
        self._socket = socket
        self._finished = False
        self._closed = False
        
    def __recv_n_bytes(self, n):
        msg_bytes = b''
        while len(msg_bytes) < n:
            chunk = self._socket.recv(n - len(msg_bytes))
            if not chunk:
                self._finished = True
                return None
            msg_bytes += chunk
        return msg_bytes
    
    def recv_all(self, bufsize: int) -> bytes:
        size_bytes = self.__recv_n_bytes(2)
        if self._finished:
            return None
        msg_size = int.from_bytes(size_bytes, "big")
        logging.debug(f"Expecting to receive {msg_size} bytes")

        if bufsize < msg_size:
            logging.error(f"Message too big {msg_size}. Bigger than max buf {bufsize}")
        msg_bytes = self.__recv_n_bytes(msg_size)
        logging.debug(f"Received {len(msg_bytes)} bytes")

        return msg_bytes.decode("utf-8")
    
    def send(self, msg: str) -> int:
        try:
            self._socket.sendall(msg.encode('utf-8'))
            logging.debug(f"action: send_response | result: success")
        except OSError as e:
            self._finished = True
            return -1
        return 0
    
    def finished(self) -> bool:
        return self._finished
    
    def close(self):
        if self._socket:
            self._socket.close()
            self._socket = None
