"""Background serial listener for the physical keypad button.

Listens to a configured COM port, parses lines emitted by the Arduino sketch
(e.g., "Tecla: 1"), and fires a callback whenever the trigger key is pressed.
The listener runs on a daemon thread and is safe to ignore if the hardware is
not connected.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional, TYPE_CHECKING

try:
    import serial
    from serial import SerialException
except ImportError:  # pragma: no cover - enforced via requirements
    serial = None  # type: ignore
    SerialException = Exception  # type: ignore

if TYPE_CHECKING:  # pragma: no cover
    from serial import Serial


@dataclass
class ButtonListenerConfig:
    enabled: bool = False
    port: str = "COM3"
    baudrate: int = 115200
    trigger_key: str = "1"
    debounce_sec: float = 0.3

    def normalized_key(self) -> str:
        return (self.trigger_key or "").strip()


class ButtonListener:
    def __init__(self, cfg: ButtonListenerConfig, on_key: Callable[[str], None]):
        self.cfg = cfg
        self._on_key = on_key
        self._serial: Optional["Serial"] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._last_emit_ts: float = 0.0
        self._led_state: bool = False

    def start(self):
        if not self.cfg.enabled:
            return
        if serial is None:
            raise RuntimeError(
                "pyserial não está instalado. Execute pip install pyserial e volte a tentar."
            )
        try:
            self._serial = serial.Serial(
                self.cfg.port,
                self.cfg.baudrate,
                timeout=0.25,
            )
        except SerialException as exc:
            raise RuntimeError(f"Não foi possível abrir {self.cfg.port}: {exc}") from exc
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        # Desligar LED antes de fechar
        self.set_led(False)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except SerialException:
                pass

    def set_led(self, state: bool):
        """Envia comando para ligar (True) ou desligar (False) o LED vermelho."""
        if not self._serial or not self._serial.is_open:
            return
        if self._led_state == state:
            return  # Já está no estado desejado
        try:
            cmd = "LED:1\n" if state else "LED:0\n"
            self._serial.write(cmd.encode('utf-8'))
            self._serial.flush()
            self._led_state = state
        except SerialException:
            pass  # Ignorar erros de comunicação

    def _run(self):  # pragma: no cover - relies on hardware
        assert self._serial is not None
        while not self._stop.is_set():
            try:
                raw = self._serial.readline()
            except SerialException:
                time.sleep(0.5)
                continue
            if not raw:
                continue
            try:
                line = raw.decode("utf-8", errors="ignore").strip()
            except UnicodeDecodeError:
                continue
            key = self._extract_key(line)
            if not key:
                continue
            now = time.time()
            if now - self._last_emit_ts < max(0.0, self.cfg.debounce_sec):
                continue
            self._last_emit_ts = now
            self._on_key(key)

    def _extract_key(self, line: str) -> Optional[str]:
        if not line:
            return None
        if len(line) == 1:
            return line
        if ":" in line:
            value = line.split(":", 1)[-1].strip()
            return value[:1] if value else None
        # fallback: last token
        parts = line.split()
        if not parts:
            return None
        return parts[-1][:1]
