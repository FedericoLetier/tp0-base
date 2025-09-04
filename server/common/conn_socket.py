class Socket:
    END_MSG = '\n'
    
    def __init__(self, socket):
        self._socket = socket
        
    def recv(self, bufsize: int) -> bytes:
        msg = ''
        while not msg.endswith(self.END_MSG):
            try: 
                chunk = self._socket.recv(bufsize)
            except BlockingIOError:
                continue
            except IOError as e:
                return None
            if not chunk:
                break
            msg += chunk.decode('utf-8')
        
        return msg
    
    def send(self, msg: str) -> int:
        try:
            self._socket.sendall(msg.encode('utf-8'))
        except OSError as e:
            return -1
        return 0
    
    def close(self):
        self._socket.close()
