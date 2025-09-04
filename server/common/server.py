import socket
import logging
from common.conn_socket import Socket
from common.utils import Bet, store_bets

class Server:
    BET_FIELDS_SPLITTER = ','
    BET_FIELDS_AMMOUNT = 6

    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._stop = False

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # the server
        client_sock = None
        while not self._stop:
            client_sock = self.__accept_new_connection()
            if client_sock:
                self.__handle_client_connection(client_sock)
        
        if client_sock:
            client_sock.close()
        self.close()

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        msg = client_sock.recv(1024)
        if not msg:
            logging.error("action: receive_message | result: fail | error: Connection closed by peer")
            client_sock.close()
            return
        
        split_msg = msg.split(self.BET_FIELDS_SPLITTER)
        if len(split_msg) != self.BET_FIELDS_AMMOUNT:
            logging.error("action: receive_message | result: fail | error: Invalid message format")
            client_sock.send("ERROR: Invalid message format\n")
            return
        
        bet = Bet(split_msg[0], split_msg[1], split_msg[2], split_msg[3], split_msg[4], split_msg[5])
        store_bets([bet])
        logging.info(f"action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}")
        msg = "SUCCESS: Bet stored\n"
        if client_sock.send(msg) < 0:
            logging.error("action: send_message | result: fail | error: Short write")
        client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        try: 
            c, addr = self._server_socket.accept()
        except OSError as e:
            if self._stop:
                return None
            else:
                logging.error(f"action: accept_connections | result: fail | error: {e}")
                return None
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return Socket(c)
    
    def close(self):
        self._stop = True
        if self._server_socket:
            self._server_socket.close() 
            logging.info("action: shutdown | result: success | info: Server shutdown completed")
        