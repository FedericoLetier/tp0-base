import logging
import socket

class Socket:
    def __init__(self, socket):
        self._socket = socket
        self._finished = False
        self._closed = False
        
    def __recv_one_byte(self):
        op_code_bytes = self._socket.recv(1)
        if not op_code_bytes:
            self._finished = True
            return None
        return int.from_bytes(op_code_bytes, "big")

    def __recv_size(self):
        size_bytes = self._socket.recv(2)
        if not size_bytes:
            self._finished = True
            return None
        msg_size = int.from_bytes(size_bytes, "big")
        logging.debug(f"Expecting to receive {msg_size} bytes")
        return msg_size

    def __recv_batch(self, bufsize):
        msg_size = self.__recv_size()
        if msg_size is None:
            return None 
    
        msg_bytes = b''
        while len(msg_bytes) < msg_size:
            chunk = self._socket.recv(min(bufsize, msg_size - len(msg_bytes)))
            if not chunk:
                self._finished = True
                return None
            msg_bytes += chunk
        logging.debug(f"Received {len(msg_bytes)} bytes")

        return msg_bytes.decode("utf-8")

    def recv_all(self, bufsize: int) -> bytes:
        op_code = self.__recv_one_byte()

        if op_code == 1:
            return 1, self.__recv_batch(bufsize)
        elif op_code == 2:
            agency_id = self.__recv_one_byte()
            return 2, agency_id
        else:
            logging.error(f"Uknown opcode: {op_code}")
            return None, None

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
