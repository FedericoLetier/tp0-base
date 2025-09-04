import socket
import logging
from common.utils import Bet, store_bets, load_bets, has_won
from common.bets_monitor import BetsMonitor
from common.client_handler import AgencyCommunicationHandler

class Server:
    def __init__(self, port, listen_backlog, total_agencys):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._bets_monitor = BetsMonitor(total_agencys)
        self._handlers = []
        self._stop = False

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        try:
            while not self._stop:
                self.__accept_new_connection()
                logging.debug(f"Conexión creada, vamos {len(self._handlers)}")
        except IOError as e:
            logging.error(f"Error using client socket not catched in loop | error: {e} | shutting down")
        except Exception as e:
            logging.error(f"Uknown error not catched in loop | error: {e} | shutting down")
        finally:
            self.close() 
        
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
        handler = AgencyCommunicationHandler(c, self._bets_monitor)
        handler.start()
        self._handlers.append(handler)
    
    def close(self):
        if not self._stop:
            self._stop = True
            self._bets_monitor.close()
            for handler in self._handlers:
                handler.close()
            for handler in self._handlers:
                handler.join()
            self._server_socket.close()
            logging.info("action: shutdown | result: success | info: Server shutdown completed")
        