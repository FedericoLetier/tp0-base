import socket
import logging
from common.conn_socket import Socket
from common.utils import Bet, store_bets, load_bets, has_won

class Server:
    BET_FIELDS_SIZE = 6
    BUFF_SIZE = 8192
    BET_SPLITTER = "\n"
    BET_FIELDS_SPLITTER = ","

    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._waiting_winners = []
        self._stop = False

    def run(self, total_agencys):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # the server
        client_socket = None
        try:
            while not self._stop:
                client_socket = self.__accept_new_connection()
                self.__handle_client_connection(client_socket)
                logging.debug(f"Cliente manejado, vamos {len(self._waiting_winners)}")

                if len(self._waiting_winners) == total_agencys:
                    self.__send_winners()
                    break
        except IOError as e:
            logging.error(f"Error using client socket | error: {e} | shutting down")
        except Exception as e:
            logging.error(f"Uknown error | error: {e} | shutting down")
        finally:
            self.close()
            if client_socket:
                client_socket.close()

    def __send_winners(self):
        logging.info("action: sorteo | result: success")
        bets = load_bets()
        winners = {}
        for bet in bets:
            if not has_won(bet):
                continue
            if not bet.agency in winners:
                winners[bet.agency] = []
            winners[bet.agency].append(bet.document)
        for agency, socket in self._waiting_winners:
            if agency not in winners:
                logging.debug(f"agency {agency} has no winners")
                socket.send("\n")
                continue
            logging.debug(f"winners sent to agency: {agency}")
            agency_winners = winners[agency]
            msg = self.BET_FIELDS_SPLITTER.join(agency_winners)
            msg += self.BET_SPLITTER
            socket.send(msg)

    def __store_and_send_response(self, bets, success, client_socket):
        store_bets(bets)
        bet_stored = len(bets)
        result = "success" if success else "fail"
        logging.debug(f"action: apuesta_recibida | result: {result} | cantidad: {bet_stored}")
        msg = "SUCCESS: Bet stored\n" if success else "ERROR: error storing bets\n"
        if client_socket.send(msg) < 0:
            logging.error(f"action: enviar_respuesta | result: fail | short write, socket closed")
        
    def __parse_lines(self, msg):
        success = True
        bets = []
        raw_bets = msg.split(self.BET_SPLITTER)
        for line in raw_bets:
            split_msg = line.split(self.BET_FIELDS_SPLITTER)
            if len(split_msg) != self.BET_FIELDS_SIZE:
                logging.debug(f"action: parse_bet | result: fail | line: {raw_bets}")
                logging.debug(f"action: parse_bet | result: fail | line: {raw_bets}")
                success = False
                break
            bet = Bet(split_msg[0], split_msg[1], split_msg[2], split_msg[3], split_msg[4], split_msg[5])
            bets.append(bet)    
        return bets, success

    def __handle_client_connection(self, client_socket):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        if not client_socket:
            return
        
        success = True
        while not client_socket.finished():
            try:
                op_code, msg = client_socket.recv_all(self.BUFF_SIZE)
            except BlockingIOError:
                continue
            except IOError as e:
                success = False
            if not msg and client_socket.finished():
                continue

            if op_code == 1:
                bets, success = self.__parse_lines(msg)
                self.__store_and_send_response(bets, success, client_socket)
            else:
                self._waiting_winners.append((msg, client_socket))
                logging.debug(f"Agency waiting for winner: {msg}")
                break

        client_socket = None

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
                return
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return Socket(c)
    
    def close(self):
        self._stop = True
        if self._server_socket:
            for _, socket in self._waiting_winners:
                socket.close()
            self._server_socket.close()
            self._server_socket = None
            logging.info("action: shutdown | result: success | info: Server shutdown completed")
        