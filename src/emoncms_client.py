"""EmonCMS uploader helper.

Sends metrics dictionaries to an emonCMS instance via /input/post using HTTP GET
with the `fulljson` parameter (same formato do link fornecido no projeto).
Designed to be light-weight and safe for the main loop: throttled by interval
and swallow network errors after logging once.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Dict, Optional

import requests
from requests import RequestException


@dataclass
class EmonCMSConfig:
    enabled: bool = False
    base_url: str = "https://emoncms.org/input/post"
    api_key: str = ""
    node: str = "smart-queue"
    interval_sec: float = 5.0
    timeout_sec: float = 4.0


class EmonCMSUploader:
    def __init__(self, cfg: EmonCMSConfig):
        self.cfg = cfg
        self._last_sent_ts: float = 0.0
        self._last_error_msg: Optional[str] = None

    @property
    def enabled(self) -> bool:
        return self.cfg.enabled and bool(self.cfg.api_key)

    def maybe_send(self, metrics: Dict[str, int | float | str]):
        if not self.enabled:
            return
        now = time.time()
        if now - self._last_sent_ts < max(0.1, self.cfg.interval_sec):
            return
        self._last_sent_ts = now
        self._send(metrics)

    def _send(self, metrics: Dict[str, int | float | str]):
        params = {
            "node": self.cfg.node,
            "apikey": self.cfg.api_key,
            "fulljson": json.dumps(metrics, separators=(",", ":")),
        }
        try:
            resp = requests.get(
                self.cfg.base_url,
                params=params,
                timeout=self.cfg.timeout_sec,
            )
            resp.raise_for_status()
            # reset error cache on success
            self._last_error_msg = None
        except RequestException as exc:
            msg = f"EmonCMS upload falhou: {exc}"
            # só loga quando mensagem muda para evitar spam
            if msg != self._last_error_msg:
                print(f"⚠️  {msg}")
                self._last_error_msg = msg
