"""ECU tuning parameter read/write via Speeduino protocol.

Common tunable parameters exposed via web UI.
Uses the Speeduino 't' (read) and 'w' (write) commands.

WARNING: Writing incorrect values can damage your engine.
All writes require explicit confirmation.
"""
import struct

TUNING_PARAMS = [
    {
        "id": "req_fuel",
        "name": "Required Fuel",
        "unit": "ms",
        "description": "Base fuel pulse width at 100% VE",
        "page": 2, "offset": 0, "size": 2, "scale": 0.1,
        "min": 0, "max": 25.5, "step": 0.1,
    },
    {
        "id": "cranking_rpm",
        "name": "Cranking RPM",
        "unit": "rpm",
        "description": "RPM threshold below which cranking enrichment is active",
        "page": 2, "offset": 22, "size": 2, "scale": 1,
        "min": 100, "max": 800, "step": 10,
    },
    {
        "id": "idle_target_rpm",
        "name": "Idle Target RPM",
        "unit": "rpm",
        "description": "Target idle RPM for closed-loop idle control",
        "page": 2, "offset": 31, "size": 2, "scale": 10,
        "min": 400, "max": 2000, "step": 50,
    },
    {
        "id": "rev_limit",
        "name": "Rev Limit",
        "unit": "rpm",
        "description": "Hard RPM limit — fuel/spark cut above this",
        "page": 2, "offset": 2, "size": 2, "scale": 1,
        "min": 2000, "max": 9000, "step": 100,
    },
    {
        "id": "boost_target",
        "name": "Boost Target",
        "unit": "kPa",
        "description": "Target boost pressure for boost controller",
        "page": 2, "offset": 123, "size": 1, "scale": 1,
        "min": 0, "max": 255, "step": 5,
    },
    {
        "id": "flex_fuel_low",
        "name": "Flex Fuel Low %",
        "unit": "%",
        "description": "Ethanol content considered as low (petrol)",
        "page": 2, "offset": 178, "size": 1, "scale": 1,
        "min": 0, "max": 100, "step": 1,
    },
    {
        "id": "fan_on_temp",
        "name": "Fan On Temperature",
        "unit": "°C",
        "description": "Coolant temp at which radiator fan switches on",
        "page": 2, "offset": 27, "size": 1, "scale": 1,
        "min": 50, "max": 120, "step": 1,
    },
    {
        "id": "fan_off_temp",
        "name": "Fan Off Temperature",
        "unit": "°C",
        "description": "Coolant temp at which radiator fan switches off",
        "page": 2, "offset": 26, "size": 1, "scale": 1,
        "min": 40, "max": 110, "step": 1,
    },
]


class ECUTuner:
    """Read/write ECU tuning parameters."""

    def __init__(self, reader):
        self.reader = reader
        self._cache = {}

    def _get_transport(self):
        r = self.reader
        if hasattr(r, "reader") and r.reader:
            r = r.reader
        if hasattr(r, "serial") and r.serial:
            return ("serial", r.serial)
        if hasattr(r, "sock") and r.sock:
            return ("socket", r.sock)
        return (None, None)

    def _send_receive(self, cmd, size, timeout=1.0):
        ttype, transport = self._get_transport()
        if not transport:
            return None
        try:
            if ttype == "serial":
                transport.timeout = timeout
                transport.write(cmd)
                return transport.read(size)
            elif ttype == "socket":
                transport.settimeout(timeout)
                transport.sendall(cmd)
                data = b""
                while len(data) < size:
                    chunk = transport.recv(size - len(data))
                    if not chunk:
                        break
                    data += chunk
                return data
        except Exception:
            return None

    def read_param(self, param_id):
        param = next((p for p in TUNING_PARAMS if p["id"] == param_id), None)
        if not param:
            return None

        page = param["page"]
        offset = param["offset"]
        size = param["size"]

        cmd = struct.pack("BBH", ord("r"), page, offset) + struct.pack("H", size)
        raw = self._send_receive(cmd, size)
        if not raw or len(raw) < size:
            return None

        if size == 1:
            value = raw[0]
        elif size == 2:
            value = struct.unpack("<H", raw)[0]
        else:
            return None

        return value * param["scale"]

    def write_param(self, param_id, value):
        return False, "Write disabled — use TunerStudio for ECU tuning"

    def burn_to_flash(self):
        return False

    def get_all_params(self):
        result = []
        for p in TUNING_PARAMS:
            entry = dict(p)
            if p["id"] in self._cache:
                entry["value"] = self._cache[p["id"]]
            else:
                entry["value"] = None
            result.append(entry)
        return result
