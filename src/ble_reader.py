"""Bluetooth LE reader for Speeduino via Airbear module.

Airbear advertises as 'Speeduino' with a UART service.
Uses standard Nordic UART Service (NUS) UUIDs.
"""
import struct
import threading
import time

try:
    import asyncio
    from bleak import BleakClient, BleakScanner
    HAS_BLEAK = True
except ImportError:
    HAS_BLEAK = False

from config import RT_MAP, STOICH_AFR

NUS_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NUS_TX_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # ECU → Pi (notify)
NUS_RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # Pi → ECU (write)

AIRBEAR_BLE_NAME = "Speeduino"


def _parse_realtime(raw):
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


class BLEReader:
    """Bluetooth LE reader for Speeduino via Airbear NUS service."""

    def __init__(self, device_name=AIRBEAR_BLE_NAME):
        if not HAS_BLEAK:
            raise ImportError("bleak library required: pip install bleak")
        self.device_name = device_name
        self.data = {}
        self.connected = False
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._client = None
        self._response_buffer = bytearray()
        self._response_event = threading.Event()

    def _notification_handler(self, sender, data):
        self._response_buffer.extend(data)
        self._response_event.set()

    async def _connect_async(self):
        device = await BleakScanner.find_device_by_name(self.device_name, timeout=5)
        if not device:
            print(f"BLE device '{self.device_name}' not found")
            return False

        self._client = BleakClient(device)
        await self._client.connect()
        await self._client.start_notify(NUS_TX_UUID, self._notification_handler)
        print(f"ECU connected via BLE: {device.name} ({device.address})")
        self.connected = True
        return True

    async def _send_command_async(self, cmd, response_size, timeout=0.5):
        if not self._client or not self._client.is_connected:
            return None
        self._response_buffer.clear()
        self._response_event.clear()
        await self._client.write_gatt_char(NUS_RX_UUID, cmd)

        start = time.time()
        while len(self._response_buffer) < response_size:
            self._response_event.wait(timeout=0.05)
            self._response_event.clear()
            if time.time() - start > timeout:
                break

        return bytes(self._response_buffer[:response_size])

    async def _read_realtime_async(self):
        raw = await self._send_command_async(b"A", 75)
        parsed = _parse_realtime(raw)
        if parsed:
            with self._lock:
                self.data = parsed
        return parsed

    async def _loop_async(self):
        while self._running:
            if not self.connected:
                try:
                    await self._connect_async()
                except Exception as e:
                    print(f"BLE connection error: {e}")
                    self.connected = False
                    await asyncio.sleep(3)
                    continue
            try:
                await self._read_realtime_async()
            except Exception:
                self.connected = False
                if self._client:
                    try:
                        await self._client.disconnect()
                    except Exception:
                        pass
                    self._client = None
            await asyncio.sleep(0.05)

    def _run_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._loop_async())

    def connect(self):
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(self._connect_async())

    def get_data(self):
        with self._lock:
            return dict(self.data)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._client:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._client.disconnect())
