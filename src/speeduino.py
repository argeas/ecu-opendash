import socket
import struct
import threading
import time

import serial

from config import RT_MAP, SERIAL_BAUD, SERIAL_PORT, SERIAL_TIMEOUT, STOICH_AFR

# Airbear WiFi defaults
AIRBEAR_DEFAULT_HOST = "speeduino.local"
AIRBEAR_DEFAULT_PORT = 2000
AIRBEAR_AP_SSID = "Speeduino Dash"


def _parse_realtime(raw):
    """Parse Speeduino 'A' command response into a dict."""
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

    return parsed


class SpeeduinoReader:
    """USB serial reader for Speeduino/Dropbear ECU."""

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
            if sig:
                print(f"ECU connected via USB: {sig}")
            self.connected = True
            return True
        except serial.SerialException as e:
            print(f"USB serial error: {e}")
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
        parsed = _parse_realtime(raw)
        if parsed:
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


class WiFiReader:
    """WiFi TCP reader for Speeduino via Airbear module.

    Airbear (ESP32-C3) creates a WiFi AP 'Speeduino Dash' or joins
    an existing network. TCP server listens on port 2000. Same
    Speeduino serial protocol tunnelled over TCP.

    Connection options:
      1. Pi joins Airbear AP ('Speeduino Dash'), connect to 192.168.4.1:2000
      2. Airbear joins same WiFi as Pi, connect to speeduino.local:2000
    """

    def __init__(self, host=AIRBEAR_DEFAULT_HOST, port=AIRBEAR_DEFAULT_PORT):
        self.host = host
        self.port = port
        self.sock = None
        self.data = {}
        self.connected = False
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(3)
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(SERIAL_TIMEOUT)

            sig = self._send_command(b"Q", 20)
            if sig:
                print(f"ECU connected via WiFi ({self.host}:{self.port}): {sig}")
            self.connected = True
            return True
        except (socket.error, OSError) as e:
            print(f"WiFi connection error ({self.host}:{self.port}): {e}")
            self.connected = False
            if self.sock:
                self.sock.close()
                self.sock = None
            return False

    def _send_command(self, cmd, response_size):
        if not self.sock:
            return None
        try:
            self.sock.sendall(cmd)
            data = b""
            while len(data) < response_size:
                chunk = self.sock.recv(response_size - len(data))
                if not chunk:
                    break
                data += chunk
            return data
        except (socket.error, OSError):
            self.connected = False
            return None

    def read_realtime(self):
        raw = self._send_command(b"A", 75)
        parsed = _parse_realtime(raw)
        if parsed:
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
        if self.sock:
            self.sock.close()


class AutoReader:
    """Auto-detect ECU connection: tries WiFi first, falls back to USB.

    Searches for:
      1. WiFi TCP on speeduino.local:2000 (Airbear on same network)
      2. WiFi TCP on 192.168.4.1:2000 (Airbear AP mode)
      3. USB serial on /dev/ttyACM0, /dev/ttyACM1, /dev/ttyUSB0
    """

    def __init__(self):
        self.reader = None
        self.data = {}
        self.connected = False
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def _try_wifi(self, host, port=AIRBEAR_DEFAULT_PORT):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((host, port))
            s.close()
            return True
        except (socket.error, OSError):
            return False

    def _try_serial(self, port):
        import os
        return os.path.exists(port)

    def _find_connection(self):
        wifi_hosts = [
            AIRBEAR_DEFAULT_HOST,
            "192.168.4.1",
        ]
        for host in wifi_hosts:
            print(f"Trying WiFi: {host}:{AIRBEAR_DEFAULT_PORT}...")
            if self._try_wifi(host):
                reader = WiFiReader(host=host)
                if reader.connect():
                    print(f"Connected via WiFi: {host}")
                    return reader
                reader.stop()

        serial_ports = ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyUSB0"]
        for port in serial_ports:
            print(f"Trying USB: {port}...")
            if self._try_serial(port):
                reader = SpeeduinoReader(port=port)
                if reader.connect():
                    print(f"Connected via USB: {port}")
                    return reader

        return None

    def connect(self):
        self.reader = self._find_connection()
        if self.reader:
            self.connected = True
            return True
        print("No ECU found on WiFi or USB")
        self.connected = False
        return False

    def get_data(self):
        if self.reader:
            return self.reader.get_data()
        return {}

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self._running:
            if not self.connected:
                self.connect()
                if not self.connected:
                    time.sleep(3)
                    continue
            if self.reader:
                self.reader.read_realtime()
                if not self.reader.connected:
                    self.connected = False
                    self.reader = None
            time.sleep(0.03)

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self.reader:
            self.reader.stop()


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
