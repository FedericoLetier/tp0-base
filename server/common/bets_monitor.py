from threading import Barrier, Lock
from common.utils import Bet, store_bets, load_bets, has_won

class BetsMonitor:
    def __init__(self, total_agencys):
        self._lock = Lock()
        self._barrier = Barrier(total_agencys)
        self._total_agencys = total_agencys
        self._bets_winners = None

    def store_bets(self, bets: list[Bet]):
        with self._lock:
            store_bets(bets)

    def __calculate_winners(self):
        self._bets_winners = {}
        for i in range(1, self._total_agencys + 1):
            self._bets_winners[i] = []
        bets = load_bets()
        for bet in bets:
            if has_won(bet):
                self._bets_winners[bet.agency].append(bet.document)

    def get_agency_winners(self, agency_number) -> list[Bet]:
        self._barrier.wait()
        with self._lock:
            # Los ganadores se calculan solo una vez. El primer handler que
            # tome el lock será el encargado de eso.
            # Permite no tener que devolver el arreglo de todos las apuestas
            if self._bets_winners is None:
                self.__calculate_winners()
            return self._bets_winners[agency_number]
        
    def close(self):
        self._barrier.abort()