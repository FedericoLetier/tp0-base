import logging
import socket

class Socket:
    def __init__(self, socket):
        self._socket = socket
        self._finished = False
        
    def recv_all(self, bufsize: int) -> bytes:
        size_bytes = self._socket.recv(2)
        if not size_bytes:
            self._finished = True
            return None
        msg_size = int.from_bytes(size_bytes, "big")
        logging.debug(f"Expecting to receive {msg_size} bytes")

        msg_bytes = b''
        while len(msg_bytes) < msg_size:
            chunk = self._socket.recv(min(bufsize, msg_size - len(msg_bytes)))
            if not chunk:
                self._finished = True
                return None
            msg_bytes += chunk
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
        self._socket.close()
