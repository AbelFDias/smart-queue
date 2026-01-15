from typing import Tuple, Dict, Optional, Sequence
from collections import deque
import time


Point = Tuple[int, int]


"""Funções antigas de cálculo direto (observado) removidas.
O modelo atual usa apenas fila simulada interna em QueueStats.
"""


class QueueStats:
    def __init__(self, window_sec: int = 120, service_window: int = 5):
        self.window_sec = max(1, int(window_sec))
        self._arrivals = deque()  # timestamps (seconds)
        self.queue_estimate: int = 0
        self._service_accum: float = 0.0
        self._service_durations = deque(maxlen=max(1, int(service_window)))
        self._last_service_ts: Optional[float] = None

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

    def tick(self, dt: float, avg_service_time_sec: float):
        if dt <= 0 or avg_service_time_sec <= 0 or self.queue_estimate <= 0:
            return
        self._service_accum += dt
        events = int(self._service_accum // float(avg_service_time_sec))
        if events > 0:
            self.queue_estimate = max(0, self.queue_estimate - events)
            self._service_accum -= events * float(avg_service_time_sec)

    def register_service_event(self, ts: Optional[float] = None):
        if ts is None:
            ts = time.time()
        if self.queue_estimate > 0:
            self.queue_estimate = max(0, self.queue_estimate - 1)
            if self.queue_estimate == 0:
                self._service_accum = 0.0
        if self._last_service_ts is not None:
            duration = max(0.01, ts - self._last_service_ts)
            self._service_durations.append(duration)
        self._last_service_ts = ts

    def register_service_events(
        self,
        count: int = 1,
        timestamps: Optional[Sequence[float]] = None,
    ):
        if timestamps:
            for ts in timestamps:
                self.register_service_event(ts)
            return
        for _ in range(max(0, int(count))):
            self.register_service_event()

    def current_queue_len(self) -> int:
        return int(self.queue_estimate)

    # taxa de chegada (lambda) em eventos por minuto
    def arrival_rate_per_min(self, now: Optional[float] = None) -> float:
        self._prune(now)
        n = len(self._arrivals)
        return (n / float(self.window_sec)) * 60.0 if n > 0 else 0.0

    #taxa de serviço (mu) em eventos por minuto
    @staticmethod
    def service_rate_per_min(avg_service_time_sec: float) -> float:
        if not avg_service_time_sec or avg_service_time_sec <= 0:
            return 0.0
        return 60.0 / float(avg_service_time_sec)

    # ETA em segundos para a fila atual
    @staticmethod
    def eta_for_new(queue_len: int, avg_service_time_sec: float) -> int:
        if queue_len <= 0 or avg_service_time_sec <= 0:
            return 0
        return int(queue_len * avg_service_time_sec)

    def estimated_service_time(self, fallback: float) -> float:
        if self._service_durations:
            return max(0.01, sum(self._service_durations) / len(self._service_durations))
        return float(fallback)

    def build_metrics(
        self,
        fps: float,
        entries: int,
        direction: str,
        people_detected: int,
        avg_service_time_sec: float,
        led_alert: bool = False,
        now: Optional[float] = None,
    ) -> Dict:
        """Retorna apenas o conjunto simplificado de métricas pedido.
        Campos: fps, direction, queue_len, entries, people_detected, eta_sec,
        arrival_rate_min, service_rate_min, service_time_sec, led_alert
        """
        if now is None:
            now = time.time()
        q_len = self.current_queue_len()
        # ETA passa a ser sempre calculado (antes dependia de include_eta/show_eta)
        eta_sec = self.eta_for_new(q_len, avg_service_time_sec)
        dir_code = 1 if direction == "left_to_right" else -1
        arr_rate = self.arrival_rate_per_min(now)
        svc_rate = self.service_rate_per_min(avg_service_time_sec)
        return {
            "fps": round(float(fps), 2),
            "direction": dir_code,
            "queue_len": int(q_len),
            "entries": int(entries),
            "people_detected": int(people_detected),
            "eta_sec": int(eta_sec),
            "arrival_rate_min": round(arr_rate, 3),
            "service_rate_min": round(svc_rate, 3),
            "service_time_sec": round(float(avg_service_time_sec), 2),
            "led_alert": int(led_alert),
        }
