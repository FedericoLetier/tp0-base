import socket
import logging
from common.conn_socket import Socket
from common.utils import Bet, store_bets

class Server:
    BET_FIELDS_SIZE = 6
    BUFF_SIZE = 8192

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

    def __store_and_send_response(self, client_sock, bets, success):
        store_bets(bets)
        bet_stored = len(bets)
        result = "success" if success else "fail"
        logging.debug(f"action: apuesta_recibida | result: {result} | cantidad: {bet_stored}")
        msg = "SUCCESS: Bet stored\n" if success else "ERROR: error storing bets\n"
        if client_sock.send(msg) < 0:
            logging.error(f"action: enviar_respuesta | result: fail | short write, socket closed")
        
    def __parse_lines(self, msg):
        success = True
        bets = []
        raw_bets = msg.split('\n')
        for line in raw_bets:
            split_msg = line.split(',')
            if len(split_msg) != self.BET_FIELDS_SIZE:
                logging.debug(f"action: parse_bet | result: fail | line: {line}")
                logging.debug(f"action: parse_bet | result: fail | line: {raw_bets}")
                success = False
                break
            bet = Bet(split_msg[0], split_msg[1], split_msg[2], split_msg[3], split_msg[4], split_msg[5])
            bets.append(bet)    
        return bets, success

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        success = True
        while not client_sock.finished():
            try:
                msg = client_sock.recv_all(self.BUFF_SIZE)
            except BlockingIOError:
                continue
            except IOError as e:
                success = False
                break
            if not msg and client_sock.finished():
                continue

            bets, success = self.__parse_lines(msg)

            self.__store_and_send_response(client_sock, bets, success)
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
                return 
            else:
                logging.error(f"action: accept_connections | result: fail | error: {e}")
                return None
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return Socket(c)
    
    def close(self):
        self._stop = True
        if self._server_socket:
            self._server_socket.close() 
            self._server_socket = None
            logging.info("action: shutdown | result: success | info: Server shutdown completed")
        