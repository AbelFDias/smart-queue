from typing import List, Tuple, Dict, Optional
from collections import deque
import time


Point = Tuple[int, int]


"""Funções antigas de cálculo direto (observado) removidas.
O modelo atual usa apenas fila simulada interna em QueueStats.
"""


class QueueStats:
    def __init__(self, window_sec: int = 120):
        self.window_sec = max(1, int(window_sec))
        self._arrivals = deque()  # timestamps (seconds)
        self.queue_estimate: int = 0
        self._service_accum: float = 0.0

    def _prune(self, now: Optional[float] = None):
        if now is None:
            now = time.time()
        cutoff = now - self.window_sec
        while self._arrivals and self._arrivals[0] < cutoff:
            self._arrivals.popleft()

    def on_entry(self, ts: Optional[float] = None):
        if ts is None:
            ts = time.time()
        self._arrivals.append(ts)
        self._prune(ts)
        self.queue_estimate += 1

    def tick(self, dt: float, avg_service_time_sec: int):
        if dt <= 0 or avg_service_time_sec <= 0 or self.queue_estimate <= 0:
            return
        self._service_accum += dt
        events = int(self._service_accum // float(avg_service_time_sec))
        if events > 0:
            self.queue_estimate = max(0, self.queue_estimate - events)
            self._service_accum -= events * float(avg_service_time_sec)

    def register_service_events(self, count: int = 1):
        if count <= 0 or self.queue_estimate <= 0:
            return
        self.queue_estimate = max(0, self.queue_estimate - int(count))
        if self.queue_estimate == 0:
            self._service_accum = 0.0

    def current_queue_len(self) -> int:
        return int(self.queue_estimate)

    def arrival_rate_per_min(self, now: Optional[float] = None) -> float:
        self._prune(now)
        n = len(self._arrivals)
        return (n / float(self.window_sec)) * 60.0 if n > 0 else 0.0

    @staticmethod
    def service_rate_per_min(avg_service_time_sec: int) -> float:
        if not avg_service_time_sec or avg_service_time_sec <= 0:
            return 0.0
        return 60.0 / float(avg_service_time_sec)

    @staticmethod
    def utilization(lambda_per_min: float, mu_per_min: float) -> float:
        capacity = mu_per_min
        if capacity <= 0:
            return 0.0
        return max(0.0, min(1.0, lambda_per_min / capacity))

    @staticmethod
    def eta_for_new(queue_len: int, avg_service_time_sec: int) -> int:
        if queue_len <= 0 or avg_service_time_sec <= 0:
            return 0
        return int(queue_len * avg_service_time_sec)

    def build_metrics(
        self,
        fps: float,
        entries: int,
        direction: str,
        people_detected: int,
        avg_service_time_sec: int,
        now: Optional[float] = None,
    ) -> Dict:
        """Retorna apenas o conjunto simplificado de métricas pedido.
        Campos: fps, direction, queue_len, entries, people_detected, eta_sec
        """
        if now is None:
            now = time.time()
        q_len = self.current_queue_len()
        # ETA passa a ser sempre calculado (antes dependia de include_eta/show_eta)
        eta_sec = self.eta_for_new(q_len, avg_service_time_sec)
        dir_code = 1 if direction == "left_to_right" else -1
        return {
            "fps": round(float(fps), 2),
            "direction": dir_code,
            "queue_len": int(q_len),
            "entries": int(entries),
            "people_detected": int(people_detected),
            "eta_sec": int(eta_sec),
        }
