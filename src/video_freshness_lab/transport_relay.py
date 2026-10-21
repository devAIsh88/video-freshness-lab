"""Single-fixture, loopback-only TCP relay. No CLI or configurable destination."""

import select
import socket
from collections import deque
from threading import Condition, Thread
from time import monotonic_ns

from .model import integer
from .rtsp_experiment import port_closed
from .transport_framing import DownstreamFramer, Unit


class FixtureRelay:
    """One I/O owner, acknowledged faults, one retained downstream record."""

    def __init__(self, server_port: int) -> None:
        integer("owned server port", server_port)
        if not 1 <= server_port <= 65535:
            raise ValueError("invalid owned server port")
        self.server_port = server_port
        self.condition = Condition()
        self.commands: deque[tuple[int, str]] = deque()
        self.serial = self.ack = 0
        self.errors: list[str] = []
        self.events: list[dict] = []
        self.counts = dict(control=0, rtp=0, rtcp=0, upstream_bytes=0, connections=0)
        self.session_headers = 0
        self.negotiated_connections = 0
        self.mode: str | None = None
        self.held: Unit | None = None
        self.hold_started_ns = 0
        self.deadline_ns: int | None = None
        self.running = True
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(1)
        self.port = self.listener.getsockname()[1]
        self.client: socket.socket | None = None
        self.upstream: socket.socket | None = None
        self.framer = DownstreamFramer()
        self.worker = Thread(target=self._run, name="fixture-transport-relay")
        self.worker.start()

    def command(self, command: str) -> int:
        if command not in ("delay", "stall", "release", "cut", "stop"):
            raise ValueError("unknown fixture relay command")
        with self.condition:
            self.serial += 1
            serial = self.serial
            self.commands.append((serial, command))
            if not self.condition.wait_for(
                lambda: self.ack >= serial or self.errors, 5
            ):
                raise TimeoutError("relay command acknowledgment guard")
            self.check()
            return next(e["at_ns"] for e in self.events if e.get("serial") == serial)

    def check(self) -> None:
        if self.errors:
            raise RuntimeError(f"fixture relay error: {self.errors}")

    def wait_event(self, kind: str, after: int = 0) -> dict:
        with self.condition:

            def found():
                return next((e for e in self.events[after:] if e["kind"] == kind), None)

            if not self.condition.wait_for(lambda: found() or self.errors, 5):
                raise TimeoutError(f"relay boundary guard: {kind}")
            self.check()
            return dict(found())

    def _event(self, kind: str, **fields) -> None:
        self.events.append({"kind": kind, "at_ns": monotonic_ns(), **fields})
        self.condition.notify_all()

    def _disconnect(self, *, expected: bool) -> None:
        if not expected:
            self.framer.finish()
        for stream in (self.client, self.upstream):
            if stream is not None:
                try:
                    stream.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                stream.close()
        self.client = self.upstream = None
        self.framer = DownstreamFramer()
        self.held = None
        self.mode = None
        self.deadline_ns = None

    def _commands(self) -> None:
        while self.commands:
            serial, command = self.commands.popleft()
            if command in ("stall", "delay"):
                if self.mode is not None or self.client is None:
                    raise RuntimeError("cannot arm relay fault at this boundary")
                self.mode = command
            elif command == "release":
                if self.held is None:
                    raise RuntimeError("no held media to release")
                self.deadline_ns = 0
            else:
                self._disconnect(expected=True)
                if command == "stop":
                    self.running = False
            self._event(command, serial=serial)
            self.ack = serial

    def _send(self, unit: Unit) -> None:
        self.client.sendall(unit.wire)
        self.counts[unit.kind] += 1
        if unit.kind == "control":
            self.session_headers += int(unit.session_present)

    def _downstream(self) -> None:
        if self.held is not None:
            if self.deadline_ns is None or monotonic_ns() < self.deadline_ns:
                return
            self._send(self.held)
            self._event(
                "forwarded-held",
                hold_started_ns=self.hold_started_ns,
                held_kind=self.held.kind,
            )
            self.held = None
            self.mode = None
            self.deadline_ns = None
        while (unit := self.framer.pop()) is not None:
            if unit.kind != "control" and self.mode in ("stall", "delay"):
                self.held = unit
                self.hold_started_ns = monotonic_ns()
                self.deadline_ns = (
                    self.hold_started_ns + 200_000_000 if self.mode == "delay" else None
                )
                self._event("held", mode=self.mode, held_kind=unit.kind)
                return
            self._send(unit)

    def _run(self) -> None:
        try:
            while self.running:
                with self.condition:
                    self._commands()
                    if not self.running:
                        break
                    if self.client is not None:
                        self._downstream()
                    reads = [self.listener] if self.client is None else [self.client]
                    if self.upstream is not None and self.held is None:
                        reads.append(self.upstream)
                readable, _, _ = select.select(reads, [], [], 0.01)
                for stream in readable:
                    with self.condition:
                        if stream is self.listener:
                            incoming, address = self.listener.accept()
                            self.client = incoming
                            if (
                                address[0] != "127.0.0.1"
                                or self.counts["connections"] >= 4
                            ):
                                raise RuntimeError("unapproved fixture connection")
                            self.client.settimeout(0.5)
                            self.upstream = socket.create_connection(
                                ("127.0.0.1", self.server_port), 0.5
                            )
                            self.counts["connections"] += 1
                            self._event(
                                "connected", generation=self.counts["connections"] - 1
                            )
                        else:
                            data = stream.recv(65536)
                            if not data:
                                # Client teardown may intentionally abandon bytes.
                                self._disconnect(expected=stream is self.client)
                                self._event("peer-closed")
                                break
                            if stream is self.client:
                                self.upstream.sendall(data)
                                self.counts["upstream_bytes"] += len(data)
                            else:
                                previously = self.framer.negotiated
                                self.framer.feed(data)
                                self._downstream()
                                if not previously and self.framer.negotiated:
                                    self.negotiated_connections += 1
        except Exception as error:
            with self.condition:
                self.errors.append(type(error).__name__ + ": " + str(error))
                self.condition.notify_all()
        finally:
            with self.condition:
                self._disconnect(expected=True)
                self.listener.close()
                self.running = False
                self.condition.notify_all()

    def close(self) -> dict:
        try:
            if self.worker.is_alive() and not self.errors:
                self.command("stop")
        except Exception as error:
            self.errors.append("close: " + type(error).__name__)
        finally:
            self.worker.join(3)
        report = {
            "events": list(self.events),
            "counts": dict(self.counts),
            "negotiated_connections": self.negotiated_connections,
            "session_header_observations": self.session_headers,
            "errors": list(self.errors),
            "worker_joined": not self.worker.is_alive(),
            "port_refused": port_closed(self.port),
            "connected_sockets_closed": self.client is None and self.upstream is None,
        }
        return report
