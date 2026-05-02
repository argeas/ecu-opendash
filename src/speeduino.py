import struct
import threading
import time

import serial

from config import RT_MAP, SERIAL_BAUD, SERIAL_PORT, SERIAL_TIMEOUT, STOICH_AFR


class SpeeduinoReader:
    def __init__(self, port=SERIAL_PORT, baud=SERIAL_BAUD):
        self.port = port
        self.baud = baud
        self.serial = None
        self.data = {}
        self.connected = False
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def connect(self):
        try:
            self.serial = serial.Serial(
                self.port, self.baud, timeout=SERIAL_TIMEOUT
            )
            time.sleep(0.5)
            self.serial.reset_input_buffer()

            sig = self._send_command(b"Q", 20)
            if sig and b"speeduino" in sig.lower():
                self.connected = True
                return True

            self.connected = True
            return True
        except serial.SerialException:
            self.connected = False
            return False

    def _send_command(self, cmd, response_size):
        if not self.serial or not self.serial.is_open:
            return None
        try:
            self.serial.write(cmd)
            return self.serial.read(response_size)
        except serial.SerialException:
            self.connected = False
            return None

    def read_realtime(self):
        raw = self._send_command(b"A", 75)
        if not raw or len(raw) < 42:
            return None

        parsed = {}
        for name, spec in RT_MAP.items():
            offset = spec["offset"]
            size = spec["size"]
            if offset + size > len(raw):
                continue

            if size == 1:
                fmt = "b" if spec["signed"] else "B"
            elif size == 2:
                fmt = "<h" if spec["signed"] else "<H"
            else:
                continue

            value = struct.unpack_from(fmt, raw, offset)[0]
            value *= spec["scale"]
            value += spec.get("offset_val", 0)
            parsed[name] = value

        if "map" in parsed and "baro" in parsed:
            parsed["boost"] = max(0, parsed["map"] - parsed["baro"])

        if "afr" in parsed:
            parsed["lambda"] = parsed["afr"] / STOICH_AFR

        with self._lock:
            self.data = parsed

        return parsed

    def get_data(self):
        with self._lock:
            return dict(self.data)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            if not self.connected:
                self.connect()
                if not self.connected:
                    time.sleep(2)
                    continue
            self.read_realtime()
            time.sleep(0.03)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self.serial and self.serial.is_open:
            self.serial.close()


class DemoReader:
    """Simulated ECU data for development without hardware."""

    def __init__(self):
        self.data = {}
        self.connected = True
        self._running = False
        self._thread = None
        self._t = 0

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        import math
        while self._running:
            self._t += 0.03
            rpm = 800 + 2200 * (0.5 + 0.5 * math.sin(self._t * 0.5))
            self.data = {
                "rpm": rpm,
                "map": 40 + 60 * (0.5 + 0.5 * math.sin(self._t * 0.3)),
                "clt": 75 + 15 * math.sin(self._t * 0.1),
                "iat": 30 + 5 * math.sin(self._t * 0.15),
                "batteryv": 13.8 + 0.5 * math.sin(self._t * 0.2),
                "afr": 14.0 + 2.0 * math.sin(self._t * 0.4),
                "tps": 25 + 25 * (0.5 + 0.5 * math.sin(self._t * 0.6)),
                "advance": 15 + 10 * math.sin(self._t * 0.35),
                "boost": max(0, 30 * math.sin(self._t * 0.3)),
                "oilpressure": 45 + 15 * math.sin(self._t * 0.2),
                "baro": 101,
                "gear": max(1, min(5, int(rpm / 1500) + 1)),
                "pw1": 3.5 + 1.5 * math.sin(self._t * 0.4),
                "lambda": (14.0 + 2.0 * math.sin(self._t * 0.4)) / 14.7,
                "ve": 50 + 20 * math.sin(self._t * 0.3),
            }
            time.sleep(0.03)

    def get_data(self):
        return dict(self.data)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def connect(self):
        return True
