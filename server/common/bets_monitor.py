from threading import Barrier, Lock
from common.utils import Bet, store_bets, load_bets

class BetsMonitor:
    def __init__(self, total_agencys):
        self._lock = Lock()
        self._barrier = Barrier(total_agencys)
        self._bets = None

    def store_bets(self, bets: list[Bet]):
        with self._lock:
            store_bets(bets)

    def load_bets(self) -> list[Bet]:
        self._barrier.wait()

        with self._lock:
            return load_bets()