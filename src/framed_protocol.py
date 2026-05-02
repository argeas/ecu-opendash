"""Speeduino framed protocol v2 with CRC32.

Frame format (request, framed mode):
  [2-byte length big-endian] [payload] [4-byte CRC32 big-endian]

Frame format (response, framed mode):
  [2-byte length big-endian] [1-byte return code] [data...] [4-byte CRC32 big-endian]

Return codes:
  0x00 = SERIAL_RC_OK
  0x80 = SERIAL_RC_TIMEOUT (400ms exceeded)
  0x82 = SERIAL_RC_CRC_ERR
  0x83 = SERIAL_RC_UNKNOWN_CMD
  0x84 = SERIAL_RC_RANGE_ERR

Handshake: send 'F' legacy → receive '002' → switch to framed mode.
CRC32: ISO 3309 / IEEE 802.3 (zlib.crc32), big-endian in frame.
Length/CRC are big-endian. Payload data is little-endian.
"""
import struct
import zlib

SERIAL_RC_OK = 0x00
SERIAL_RC_TIMEOUT = 0x80
SERIAL_RC_CRC_ERR = 0x82
SERIAL_RC_UNKNOWN_CMD = 0x83
SERIAL_RC_RANGE_ERR = 0x84


def crc32_speeduino(data):
    return zlib.crc32(data) & 0xFFFFFFFF


def build_framed_request(payload):
    """Build a framed request: [2-byte len BE] [payload] [4-byte CRC32 BE]."""
    if isinstance(payload, str):
        payload = payload.encode()
    length = struct.pack(">H", len(payload))
    crc = struct.pack(">I", crc32_speeduino(payload))
    return length + payload + crc


def parse_framed_response(raw):
    """Parse framed response. Returns (return_code, payload, crc_valid)."""
    if not raw or len(raw) < 7:
        return None, None, False

    payload_size = struct.unpack(">H", raw[0:2])[0]
    expected_total = 2 + payload_size + 4
    if len(raw) < expected_total:
        return None, None, False

    payload = raw[2:2 + payload_size]
    received_crc = struct.unpack(">I", raw[2 + payload_size:expected_total])[0]
    calculated_crc = crc32_speeduino(payload)
    crc_valid = received_crc == calculated_crc

    return_code = payload[0] if payload else None
    data = payload[1:] if len(payload) > 1 else b""

    return return_code, data, crc_valid


class FramedProtocol:
    """Framed protocol with CRC32. Falls back to legacy if handshake fails."""

    def __init__(self, transport):
        self.transport = transport
        self.framed_mode = False

    def handshake(self):
        """Send 'F' to detect framed protocol v2. Returns True if supported."""
        response = self.transport.send_receive(b"F", 3, timeout=1.0)
        if response and response == b"002":
            self.framed_mode = True
            print("Framed protocol v2 with CRC32 enabled")
            return True
        print("Legacy protocol mode (no CRC32)")
        return False

    def request_realtime(self):
        """Request real-time data. Returns raw engine data bytes."""
        if not self.framed_mode:
            return self.transport.send_receive(b"A", 75, timeout=0.5)

        frame = build_framed_request(b"A")
        raw = self.transport.send_receive(frame, 257, timeout=0.5)
        if not raw:
            return None

        rc, data, valid = parse_framed_response(raw)
        if not valid:
            print("CRC32 mismatch — corrupted frame")
            return None
        if rc != SERIAL_RC_OK:
            return None

        return data

    def request_signature(self):
        """Request firmware signature via 'Q' command."""
        response = self.transport.send_receive(b"Q", 40, timeout=1.0)
        if response:
            try:
                return response.decode("ascii", errors="ignore").strip("\x00")
            except Exception:
                pass
        return None


class SerialTransport:
    """Serial port transport adapter."""

    def __init__(self, serial_conn):
        self.serial = serial_conn

    def send_receive(self, cmd, max_response, timeout=0.5):
        if not self.serial or not self.serial.is_open:
            return None
        try:
            old_timeout = self.serial.timeout
            self.serial.timeout = timeout
            self.serial.write(cmd)
            data = self.serial.read(max_response)
            self.serial.timeout = old_timeout
            return data if data else None
        except Exception:
            return None


class SocketTransport:
    """TCP socket transport adapter."""

    def __init__(self, sock):
        self.sock = sock

    def send_receive(self, cmd, max_response, timeout=0.5):
        if not self.sock:
            return None
        try:
            self.sock.settimeout(timeout)
            self.sock.sendall(cmd)
            data = b""
            while len(data) < max_response:
                try:
                    chunk = self.sock.recv(max_response - len(data))
                    if not chunk:
                        break
                    data += chunk
                except Exception:
                    break
            return data if data else None
        except Exception:
            return None
