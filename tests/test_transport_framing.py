"""Pure framing regression coverage; no sockets, native bindings or waits."""

import subprocess

import pytest

from video_freshness_lab import transport_experiment
from video_freshness_lab.transport_experiment import FaultConfig
from video_freshness_lab.transport_framing import BUFFER_LIMIT, DownstreamFramer

SETUP = b"RTSP/1.0 200 OK\r\nTransport: RTP/AVP/TCP;interleaved=0-1\r\nSession: opaque\r\n\r\n"
BODY = b"body containing $\x00\x00\x03abc and RTSP/1.0 text"
DESCRIBE = (
    b"RTSP/1.0 200 OK\r\nContent-Length: "
    + str(len(BODY)).encode()
    + b"\r\n\r\n"
    + BODY
)
RTP = b"$\x00\x00\x05a$b\r\n"
RTCP = b"$\x01\x00\x03xyz"


@pytest.mark.parametrize("chunk_size", [1, 2, 3, 7, 65536])
def test_fragmentation_and_coalescing_preserve_exact_control_and_binary_units(
    chunk_size,
):
    framer = DownstreamFramer()
    stream = DESCRIBE + SETUP + RTP + RTCP
    units = []
    for offset in range(0, len(stream), chunk_size):
        framer.feed(stream[offset : offset + chunk_size])
        while (unit := framer.pop()) is not None:
            units.append(unit)
    framer.finish()
    assert [u.kind for u in units] == ["control", "control", "rtp", "rtcp"]
    assert b"".join(u.wire for u in units) == stream
    assert units[1].negotiated and units[1].session_present


@pytest.mark.parametrize(
    "wire",
    [
        b"RTSP/1.0 200 OK\r\nContent-Length: -1\r\n\r\n",
        b"RTSP/1.0 200 OK\r\nContent-Length: 1\r\nContent-Length: 1\r\n\r\nx",
        b"RTSP/1.0 200 OK\r\nContent-Length: 65537\r\n\r\n",
        b"RTSP/1.0 200 OK\r\nTransport: RTP/AVP;unicast\r\n\r\n",
        b"RTSP/1.0 200 OK\r\nTransport: RTP/AVP/TCP;interleaved=0-10\r\n\r\n",
        b"HTTP/1.0 200 OK\r\n\r\n",
        RTP,
    ],
)
def test_unsupported_or_ambiguous_framing_fails(wire):
    framer = DownstreamFramer()
    framer.feed(wire)
    with pytest.raises(ValueError):
        framer.pop()


def test_partial_interleaved_unit_is_not_forwardable_and_eof_fails():
    framer = DownstreamFramer()
    framer.feed(SETUP)
    framer.pop()
    framer.feed(RTP[:-1])
    assert framer.pop() is None
    with pytest.raises(ValueError, match="truncated"):
        framer.finish()


def test_unbounded_input_is_rejected():
    with pytest.raises(ValueError, match="limit"):
        DownstreamFramer().feed(b"x" * (BUFFER_LIMIT + 1))


@pytest.mark.parametrize("wire", [b"$\x02\x00\x01x", b"$\x00\x00\x00"])
def test_unnegotiated_channel_or_empty_record_is_rejected(wire):
    framer = DownstreamFramer()
    framer.feed(SETUP + wire)
    framer.pop()
    with pytest.raises(ValueError):
        framer.pop()


@pytest.mark.parametrize(
    "args", [("unknown",), ("baseline", "unknown"), ("baseline", "fifo", 1)]
)
def test_fault_configuration_rejects_invalid_schedules(args):
    with pytest.raises(ValueError):
        FaultConfig(*args)


def test_supervisor_watchdog_kills_and_waits_owned_group_without_retry(monkeypatch):
    calls = []

    class Child:
        pid = 123

        def __init__(self, args, **kwargs):
            assert args[1:3] == ["-m", "video_freshness_lab.transport_experiment"]
            assert kwargs["start_new_session"]

        def communicate(self, **kwargs):
            calls.append(kwargs)
            if "timeout" in kwargs:
                raise subprocess.TimeoutExpired("fixture", kwargs["timeout"])
            return "", ""

    monkeypatch.setattr(transport_experiment.subprocess, "Popen", Child)
    monkeypatch.setattr(
        transport_experiment.os, "killpg", lambda pid, sig: calls.append((pid, sig))
    )
    result = transport_experiment.run_isolated(FaultConfig("shutdown"), timeout_s=0.01)
    assert result["status"] == "error" and result["timeout_count"] == 1
    assert calls == [{"timeout": 0.01}, (123, transport_experiment.signal.SIGKILL), {}]
    assert result["cleanup"] is None
