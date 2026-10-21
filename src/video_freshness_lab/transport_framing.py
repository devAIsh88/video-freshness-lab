"""Bounded downstream framing for this fixture's RTSP/1.0 and channels 0/1 only."""

from dataclasses import dataclass

HEADER_LIMIT = 16_384
BODY_LIMIT = 65_536
BUFFER_LIMIT = 131_072


@dataclass(frozen=True, slots=True)
class Unit:
    kind: str
    wire: bytes
    negotiated: bool = False
    session_present: bool = False


class DownstreamFramer:
    """Retain original wire bytes; never interpret a dollar inside an RTSP body."""

    def __init__(self) -> None:
        self.buffer = bytearray()
        self.negotiated = False

    def feed(self, data: bytes) -> None:
        if len(self.buffer) + len(data) > BUFFER_LIMIT:
            raise ValueError("fixture framing buffer limit")
        self.buffer.extend(data)

    def pop(self) -> Unit | None:
        data = self.buffer
        if not data:
            return None
        if data[0] == 36:
            if len(data) < 4:
                return None
            channel, length = data[1], int.from_bytes(data[2:4], "big")
            if not self.negotiated or channel not in (0, 1) or length == 0:
                raise ValueError("unsupported interleaved channel/negotiation")
            size = 4 + length
            if len(data) < size:
                return None
            kind = "rtp" if channel == 0 else "rtcp"
            unit = Unit(kind, bytes(data[:size]))
        else:
            end = data.find(b"\r\n\r\n")
            if end < 0:
                if len(data) > HEADER_LIMIT:
                    raise ValueError("fixture RTSP header limit")
                return None
            if end > HEADER_LIMIT:
                raise ValueError("fixture RTSP header limit")
            header = bytes(data[:end]).decode("ascii")
            lines = header.split("\r\n")
            if not lines[0].startswith("RTSP/1.0 "):
                raise ValueError("expected fixture RTSP/1.0 response")
            fields: dict[str, str] = {}
            for line in lines[1:]:
                key, separator, value = line.partition(":")
                if not separator or key.lower() in fields:
                    raise ValueError("invalid/duplicate fixture RTSP header")
                fields[key.lower()] = value.strip()
            raw_length = fields.get("content-length", "0")
            if not raw_length.isascii() or not raw_length.isdecimal():
                raise ValueError("invalid RTSP Content-Length")
            length = int(raw_length)
            if length > BODY_LIMIT:
                raise ValueError("fixture RTSP body limit")
            size = end + 4 + length
            if len(data) < size:
                return None
            transport = fields.get("transport")
            if transport is not None:
                parts = [part.strip() for part in transport.split(";")]
                if parts[0] != "RTP/AVP/TCP" or "interleaved=0-1" not in parts:
                    raise ValueError("unsupported fixture transport")
                self.negotiated = True
            unit = Unit(
                "control", bytes(data[:size]), self.negotiated, "session" in fields
            )
        del data[:size]
        return unit

    def finish(self) -> None:
        if self.buffer:
            raise ValueError("truncated downstream framing")
