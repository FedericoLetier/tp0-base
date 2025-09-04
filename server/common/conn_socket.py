import logging
import socket

class Socket:
    BATCH_OP_CODE = 1
    WINNERS_OP_CODE = 2
    SIZE_BYTES = 2

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
    

    def __recv_one_int(self):
        op_code_bytes = self.__recv_n_bytes(1)
        if not op_code_bytes:
            return None
        return int.from_bytes(op_code_bytes, "big")

    def __recv_size(self):
        size_bytes = self.__recv_n_bytes(self.SIZE_BYTES)
        if not size_bytes:
            return None
        msg_size = int.from_bytes(size_bytes, "big")
        logging.debug(f"Expecting to receive {msg_size} bytes")
        return msg_size

    def __recv_batch(self, bufsize):
        msg_size = self.__recv_size()
        if msg_size is None:
            return None 
        
        if msg_size > bufsize:
            logging.error(f"action: recieve_barch | result: fail | message too big {msg_size}")
            return None
        
        msg_bytes = self.__recv_n_bytes(msg_size)
        if msg_bytes is None:
            self._finished = True
            return None
        
        logging.debug(f"Received {len(msg_bytes)} bytes")

        return msg_bytes.decode("utf-8")

    def recv_all(self, bufsize: int) -> bytes:
        op_code = self.__recv_one_int()

        if op_code == self.BATCH_OP_CODE:
            return self.BATCH_OP_CODE, self.__recv_batch(bufsize)
        elif op_code == self.WINNERS_OP_CODE:
            agency_id = self.__recv_one_int()
            return self.WINNERS_OP_CODE, agency_id
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
