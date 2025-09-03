import threading
import logging
from common.conn_socket import Socket
from common.utils import Bet, has_won


class AgencyCommunicationHandler(threading.Thread):
    BUFF_SIZE = 8192
    BET_FIELDS_SIZE = 6
    BET_SPLITTER = "\n"
    BET_FIELDS_SPLITTER = ","

    def __init__(self, socket, bets_monitor):
        threading.Thread.__init__(self)
        self._socket = Socket(socket)
        self._closed = False
        self._bets_monitor = bets_monitor
        self._agency_number = None

    def run(self):
        try:
            self._run()
        except IOError as e:
            if not self._stop:
                logging.error(f"Error using client socket | error: {e} | shutting down")
        finally:
            self.close()

    def _run(self):
        self.__recieve_bets_batch()
        self.__send_winners()

    def __recieve_bets_batch(self):
        success = True
        while not self._socket.finished() and not self._closed:
            try:
                op_code, msg = self._socket.recv_all(self.BUFF_SIZE)
            except BlockingIOError:
                continue
            except IOError as e:
                success = False
            if not msg and self._socket.finished():
                continue

            if op_code == Socket.BATCH_OP_CODE:
                bets, success = self.__parse_lines(msg)
                self.__store_and_send_response(bets, success)
            elif op_code == Socket.WINNERS_OP_CODE:
                self._agency_number = msg
                logging.debug(f"Agency waiting for winner: {msg}")
                break
            else:
                logging.error(f"Invalid op_code: {op_code}")
                break
    
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
    
    def __store_and_send_response(self, bets, success):
        self._bets_monitor.store_bets(bets)
        bet_stored = len(bets)
        result = "success" if success else "fail"
        logging.debug(f"action: apuesta_recibida | result: {result} | cantidad: {bet_stored}")
        msg = "SUCCESS: Bet stored\n" if success else "ERROR: error storing bets\n"
        if self._socket.send(msg) < 0:
            logging.error(f"action: enviar_respuesta | result: fail | short write, socket closed")
        

    def __send_winners(self):
        logging.info("action: sorteo | result: success")
        bets = self._bets_monitor.load_bets()
        winners = []
        for bet in bets:
            if not has_won(bet) or bet.agency != self._agency_number:
                continue
            winners.append(bet.document)
        
        if len(winners) == 0:
            logging.debug(f"agency {self._agency_number} has no winners")
            self._socket.send(self.BET_SPLITTER)
            return
        logging.debug(f"winners sent to agency: {self._agency_number}")
        msg = self.BET_FIELDS_SPLITTER.join(winners)
        msg += self.BET_SPLITTER
        self._socket.send(msg)

    def close(self):
        if not self._closed:
            self._socket.close()
            self._closed = True
            logging.info("action: shutdown | result: success | info: handler shutdown completed")

        
