"""Finite localhost RTSP research runner. GI is optional and imported at runtime.

The supervisor owns a process group, the trial owns its server child and client
pipelines. Missing prerequisites fail explicitly; ordinary pytest never uses GI.
"""

import argparse
import errno
import json
import multiprocessing
import os
import signal
import socket
import subprocess
import sys
from dataclasses import asdict
from threading import Condition, Event, Thread
from threading import enumerate as enumerate_threads
from time import monotonic, monotonic_ns

from .gstreamer_contract import PublicationLedger
from .rtsp_contract import SCENARIOS, RtspConfig, receipt_evidence

STARTUP_S = 5
JOIN_S = 3
TRIAL_S = 30


def bindings():
    import gi

    for name in ("Gst", "GstApp", "GstRtp", "GstRtsp", "GstRtspServer"):
        gi.require_version(name, "1.0")
    from gi.repository import GLib, Gst, GstApp, GstRtp, GstRtsp, GstRtspServer

    Gst.init(None)
    return GLib, Gst, GstApp, GstRtp, GstRtsp, GstRtspServer


def server_main(pipe) -> None:
    """Wrap the installed RTSP server, with a finite synthetic media factory."""
    GLib, Gst, _, _, _, Server = bindings()
    loop = GLib.MainLoop()
    server = Server.RTSPServer()
    server.set_address("127.0.0.1")
    server.set_service("0")
    factory = Server.RTSPMediaFactory()
    factory.set_shared(True)
    factory.set_launch(
        "( videotestsrc name=source is-live=true num-buffers=100 pattern=smpte "
        "! video/x-raw,format=I420,width=320,height=240,framerate=10/1 "
        "! valve name=fault drop=false ! jpegenc "
        "! rtpjpegpay name=pay0 pt=26 )"
    )
    state = {"produced": 0, "accepted_loopback": [], "media": None}
    media_objects = []

    def produced(pad, info):
        state["produced"] += 1
        return Gst.PadProbeReturn.OK

    def configured(factory, media):
        # Keep wrappers alive until explicit native teardown has finished; native
        # streaming callbacks must not outlive Python interpreter finalization.
        media_objects.append(media)
        state["media"] = media.get_element()
        state["media"].get_by_name("source").get_static_pad("src").add_probe(
            Gst.PadProbeType.BUFFER, produced
        )

    def connected(server, client):
        local = client.get_connection().get_ip() == "127.0.0.1"
        state["accepted_loopback"].append(local)
        if not local:
            client.close()

    factory.connect("media-configure", configured)
    server.connect("client-connected", connected)
    server.get_mount_points().add_factory("/synthetic", factory)
    attachment = server.attach(None)
    if not attachment or server.get_bound_port() <= 0:
        raise RuntimeError("RTSP listener did not attach")
    pipe.send(
        {
            "ready": True,
            "port": server.get_bound_port(),
            "loopback": server.get_address() == "127.0.0.1",
        }
    )

    def control():
        if pipe.poll():
            command = pipe.recv()
            if command == "stall":
                state["media"].get_by_name("fault").set_property("drop", True)
            pipe.send(
                {
                    "command": command,
                    "server_monotonic_ns": monotonic_ns(),
                    "produced": state["produced"],
                    "accepted_loopback": list(state["accepted_loopback"]),
                }
            )
            if command == "stop":
                loop.quit()
                return False
        return True

    GLib.timeout_add(10, control)
    try:
        loop.run()
    finally:
        GLib.source_remove(attachment)
        clients = server.client_filter(lambda *_: Server.RTSPFilterResult.REF)
        for client in clients:
            client.close()
        server.get_session_pool().filter(lambda *_: Server.RTSPFilterResult.REMOVE)
        media_null = []
        for media in media_objects:
            unprepared = media.unprepare()
            element = media.get_element()
            element.set_state(Gst.State.NULL)
            state_result, current, _ = element.get_state(JOIN_S * Gst.SECOND)
            media_null.append(
                bool(unprepared)
                and current == Gst.State.NULL
                and state_result != Gst.StateChangeReturn.FAILURE
            )
        server.get_mount_points().remove_factory("/synthetic")
        # Documented test-suite cleanup: wait for the library's own tasks rather
        # than relying on interpreter/process destruction to stop native work.
        Server.RTSPThreadPool.cleanup()
        pipe.send(
            {"command": "cleanup", "media_null": media_null, "pool_drained": True}
        )
        pipe.close()


def port_closed(port: int) -> bool:
    with socket.socket() as probe:
        probe.settimeout(0.3)
        return probe.connect_ex(("127.0.0.1", port)) == errno.ECONNREFUSED


class OwnedServer:
    def __init__(self, events: list[dict]) -> None:
        self.events = events
        self.port: int | None = None
        self.stopped = False
        context = multiprocessing.get_context("spawn")
        self.pipe, child = context.Pipe()
        self.process = context.Process(target=server_main, args=(child,))
        self.process.start()
        child.close()

    def ready(self) -> None:
        if not self.pipe.poll(STARTUP_S):
            raise TimeoutError("server readiness guard")
        ready = self.pipe.recv()
        if not ready.get("ready") or not ready.get("loopback"):
            raise RuntimeError("server readiness invalid")
        self.port = ready["port"]
        self.events.append({"server_ready_ns": monotonic_ns()})

    def command(self, command: str) -> dict:
        self.pipe.send(command)
        if not self.pipe.poll(STARTUP_S):
            raise TimeoutError(f"server command guard: {command}")
        response = self.pipe.recv()
        if response["command"] != command:
            raise RuntimeError("server acknowledgment mismatch")
        self.events.append(
            {"server_ack": response, "client_monotonic_ns": monotonic_ns()}
        )
        return response

    def production_phase(self, count: int) -> None:
        deadline = monotonic() + STARTUP_S
        while monotonic() < deadline:
            # Acknowledged observations, not a sleep-based inference of production.
            if self.command("observe")["produced"] >= count:
                return
        raise TimeoutError("source production phase guard")

    def stop(self) -> None:
        if self.stopped:
            return
        requested = monotonic_ns()
        fallback = False
        response = None
        try:
            if self.process.is_alive():
                response = self.command("stop")
        finally:
            self.process.join(JOIN_S)
            if self.process.is_alive():
                fallback = True
                self.process.terminate()
                self.process.join(JOIN_S)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(JOIN_S)
            library_cleanup = None
            if self.pipe.poll():
                try:
                    library_cleanup = self.pipe.recv()
                except EOFError:
                    pass
            closed = self.port is None or port_closed(self.port)
            self.events.append(
                {
                    "server_stop_request_ns": requested,
                    "server_exit_observed_ns": monotonic_ns(),
                    "server_exitcode": self.process.exitcode,
                    "termination_fallback": fallback,
                    "port_closed": closed,
                    "accepted_loopback": None
                    if response is None
                    else response["accepted_loopback"],
                    "library_cleanup": library_cleanup,
                }
            )
            self.stopped = True
            self.pipe.close()
            if (
                self.process.is_alive()
                or self.process.exitcode != 0
                or not closed
                or fallback
                or not library_cleanup
                or library_cleanup.get("command") != "cleanup"
                or not library_cleanup.get("pool_drained")
                or not all(library_cleanup.get("media_null", []))
            ):
                raise RuntimeError("server did not cleanly exit and release listener")
            if response is not None and (
                not response["accepted_loopback"]
                or not all(response["accepted_loopback"])
            ):
                raise RuntimeError("missing verified loopback client acceptance")


class Client:
    def __init__(self, port: int, config: RtspConfig, generation: int) -> None:
        _, self.Gst, _, self.Rtp, _, _ = bindings()
        Gst = self.Gst
        self.generation = generation
        self.condition = Condition()
        self.pad_events: list[dict] = []
        self.rtp: list[dict] = []
        self.receipts: list[dict] = []
        self.bus_events: list[dict] = []
        self.callback_errors: list[str] = []
        self.rendered = 0
        self.closed = False
        self.close_record: dict = {}
        self.pipeline = Gst.parse_launch(
            f"rtspsrc name=source location=rtsp://127.0.0.1:{port}/synthetic "
            "protocols=tcp latency=50 drop-on-latency=false tcp-timeout=2000000 "
            "! application/x-rtp,media=video,encoding-name=JPEG "
            "! rtpjpegdepay name=depay ! jpegdec name=decoder "
            "! appsink name=sink max-buffers=2 max-bytes=0 max-time=0 "
            f"leaky-type={'downstream' if config.policy == 'leaky' else 'none'} "
            "sync=false async=false emit-signals=true enable-last-sample=false "
            "wait-on-eos=false"
        )
        self.sink = self.pipeline.get_by_name("sink")
        self.bus = self.pipeline.get_bus()
        self.runtime = {
            "gstreamer": Gst.version_string(),
            "plugins": {
                name: Gst.ElementFactory.find(name).get_plugin().get_version()
                for name in (
                    "videotestsrc",
                    "valve",
                    "jpegenc",
                    "rtpjpegpay",
                    "rtspsrc",
                    "rtpjpegdepay",
                    "jpegdec",
                    "appsink",
                )
            },
            "transport": "TCP only; UDP disabled by protocols=tcp",
            "rtspsrc": {
                name: str(self.pipeline.get_by_name("source").get_property(name))
                for name in (
                    "protocols",
                    "latency",
                    "drop-on-latency",
                    "tcp-timeout",
                    "buffer-mode",
                    "do-retransmission",
                )
            },
        }
        self.sink.connect("new-sample", self.on_sample)
        self.sink.get_static_pad("sink").add_probe(Gst.PadProbeType.BUFFER, self.on_pad)
        self.pipeline.get_by_name("depay").get_static_pad("sink").add_probe(
            Gst.PadProbeType.BUFFER, self.on_rtp
        )

    def start(self) -> None:
        if (
            self.pipeline.set_state(self.Gst.State.PLAYING)
            == self.Gst.StateChangeReturn.FAILURE
        ):
            raise RuntimeError("client PLAYING failed")

    def on_sample(self, sink):
        with self.condition:
            self.rendered += 1
            self.condition.notify_all()
        return self.Gst.FlowReturn.OK

    def on_pad(self, pad, info):
        buffer = info.get_buffer()
        with self.condition:
            self.pad_events.append(
                {
                    "ordinal": len(self.pad_events),
                    "pts": int(buffer.pts),
                    "at_ns": monotonic_ns(),
                }
            )
            self.condition.notify_all()
        return self.Gst.PadProbeReturn.OK

    def on_rtp(self, pad, info):
        try:
            mapped, packet = self.Rtp.RTPBuffer.map(
                info.get_buffer(), self.Gst.MapFlags.READ
            )
            if not mapped:
                raise RuntimeError("RTP buffer map failed")
            try:
                item = {
                    "sequence": packet.get_seq(),
                    "timestamp": packet.get_timestamp(),
                    "ssrc": packet.get_ssrc(),
                    "marker": packet.get_marker(),
                    "at_ns": monotonic_ns(),
                }
            finally:
                packet.unmap()
            with self.condition:
                self.rtp.append(item)
        except Exception as error:
            with self.condition:
                self.callback_errors.append(type(error).__name__)
                self.condition.notify_all()
        return self.Gst.PadProbeReturn.OK

    def wait(self, *, rendered: int = 0, ingress: int = 0) -> None:
        with self.condition:
            ready = self.condition.wait_for(
                lambda: bool(self.callback_errors)
                or (self.rendered >= rendered and len(self.pad_events) >= ingress),
                STARTUP_S,
            )
        if not ready or self.callback_errors:
            raise RuntimeError(
                f"client observation guard/errors: {self.callback_errors}"
            )

    def pull(self, epoch: int, timeout_s: float = STARTUP_S):
        sample = self.sink.emit("try-pull-sample", int(timeout_s * self.Gst.SECOND))
        if sample is None:
            return None
        receipt_ns = monotonic_ns()
        pts = int(sample.get_buffer().pts)
        with self.condition:
            matches = [p for p in self.pad_events if p["pts"] == pts]
        if len(matches) != 1:
            raise RuntimeError("ambiguous decoder-pad to receipt PTS association")
        pad = matches[0]
        evidence = receipt_evidence(
            generation=self.generation,
            epoch=epoch,
            ordinal=len(self.receipts),
            receipt_ns=receipt_ns,
            pts=None if pts == self.Gst.CLOCK_TIME_NONE else pts,
        )
        record = {
            "generation": self.generation,
            "epoch": epoch,
            "delivery_ordinal": len(self.receipts),
            "decoder_pad_ordinal": pad["ordinal"],
            "decoder_pad_ns": pad["at_ns"],
            "receipt_ns": receipt_ns,
            "processing_start_ns": monotonic_ns(),
            "pad_to_receipt_ns": receipt_ns - pad["at_ns"],
            "pts": pts,
            "pts_time_base": "1/1000000000",
            "pts_domain": f"decoder-generation-{self.generation}",
            "capture_age_ns": None,
            "caps": sample.get_caps().to_string(),
        }
        self.receipts.append(record)
        return evidence, record

    def symptoms(self) -> bool:
        found = False
        while message := self.bus.pop_filtered(
            self.Gst.MessageType.ERROR | self.Gst.MessageType.EOS
        ):
            record = {"at_ns": monotonic_ns(), "type": message.type.value_nicks[-1]}
            if message.type == self.Gst.MessageType.ERROR:
                error, _ = message.parse_error()
                # Debug strings can contain endpoints; only stable error codes are needed.
                record.update(domain=error.domain, code=error.code)
            self.bus_events.append(record)
            found = True
        return found

    def snapshot(self) -> dict:
        levels = {
            name: int(self.sink.get_property(name))
            for name in ("in", "out", "dropped", "current-level-buffers")
        }
        jitter = []
        iterator = self.pipeline.iterate_recurse()
        while True:
            status, element = iterator.next()
            if status == self.Gst.IteratorResult.DONE:
                break
            if status == self.Gst.IteratorResult.RESYNC:
                iterator.resync()
                continue
            if status != self.Gst.IteratorResult.OK:
                raise RuntimeError("pipeline inspection failed")
            factory = element.get_factory()
            if factory and factory.get_name() == "rtpjitterbuffer":
                jitter.append(element.get_property("stats").to_string())
        rtp_caps = (
            self.pipeline.get_by_name("depay").get_static_pad("sink").get_current_caps()
        )
        # SDP-derived caps can contain sender CNAMEs. Keep only the media fields
        # needed for this experiment, never arbitrary sender identifiers.
        negotiated = None
        if rtp_caps is not None:
            structure = rtp_caps.get_structure(0)
            negotiated = {
                name: structure.get_value(name)
                for name in ("media", "payload", "clock-rate", "encoding-name")
            }
        return {
            "generation": self.generation,
            "at_ns": monotonic_ns(),
            "atomic": False,
            "appsink": levels,
            "jitterbuffer_stats": jitter,
            "decoder_loss": None,
            "packet_to_frame_mapping": None,
            "rtp_caps": negotiated,
        }

    def close(self) -> None:
        if self.closed:
            return
        try:
            self.pre_null = self.snapshot()
        finally:
            # Instrumentation failure must never prevent the actual transition.
            requested = monotonic_ns()
            self.pipeline.set_state(self.Gst.State.NULL)
            result, current, _ = self.pipeline.get_state(JOIN_S * self.Gst.SECOND)
            self.closed = (
                current == self.Gst.State.NULL
                and result != self.Gst.StateChangeReturn.FAILURE
            )
            self.close_record = {
                "null_request_ns": requested,
                "null_observed_ns": monotonic_ns(),
                "null": self.closed,
            }
        if not self.closed:
            raise RuntimeError("client failed NULL cleanup")


def trial(config: RtspConfig, *, fault: str | None = None) -> dict:
    result = {
        "config": asdict(config),
        "status": "error",
        "events": [],
        "decisions": [],
        "snapshots": [],
    }
    servers: list[OwnedServer] = []
    clients: list[Client] = []
    reader: Thread | None = None
    ledger = PublicationLedger(config.filtered)

    def open_connection(generation: int) -> Client:
        server = OwnedServer(result["events"])
        servers.append(server)
        server.ready()
        client = Client(server.port, config, generation)
        clients.append(client)
        result["events"].append(
            {"client_open_ns": monotonic_ns(), "generation": generation}
        )
        client.start()
        return client

    def acquire(client: Client, epoch: int):
        item = client.pull(epoch)
        if item is None:
            raise RuntimeError("first/next sample guard")
        return item

    def complete(item) -> None:
        evidence, record = item
        decision = ledger.complete(len(result["decisions"]), evidence, monotonic_ns())
        decision.update(
            generation=int(evidence.decoder_metadata[0][1]),
            delivery_ordinal=evidence.sequence,
            arrival_age_ns=decision["decision_ns"] - record["receipt_ns"],
            processing_delay_ns=decision["decision_ns"] - record["processing_start_ns"],
            capture_age_ns=None,
        )
        result["decisions"].append(decision)

    try:
        client = open_connection(0)
        held = acquire(client, 0)
        if fault == "processing":
            raise RuntimeError("injected processing failure after acquisition")
        if fault == "snapshot":

            def broken_snapshot():
                raise RuntimeError("injected snapshot failure")

            client.snapshot = broken_snapshot
        server = servers[-1]
        scenario = config.scenario
        if scenario == "normal":
            complete(held)
            for _ in range(3):
                complete(acquire(client, 0))
        elif scenario == "slow":
            server.production_phase(10)
            client.wait(rendered=8 if config.policy == "leaky" else 3, ingress=4)
            result["snapshots"].append(client.snapshot())
            complete(held)
            for _ in range(2):
                complete(acquire(client, 0))
        elif scenario == "epoch":
            ledger.transition()
            result["events"].append({"epoch_activated_ns": monotonic_ns(), "epoch": 1})
            complete(held)
            complete(acquire(client, 1))
        elif scenario in ("interruption", "reconnect"):
            server.stop()
            post_exit = []
            detected = False
            deadline = monotonic() + JOIN_S
            while monotonic() < deadline:
                item = client.pull(0, 0.1)
                if item is not None:
                    post_exit.append(item[1]["delivery_ordinal"])
                    complete(item)
                if client.symptoms():
                    detected = True
                    break
            result["interruption"] = {
                "post_exit_deliveries": post_exit,
                "symptom_observed": detected,
                "observation_end_ns": monotonic_ns(),
            }
            if not detected:
                raise RuntimeError("no terminal bus symptom within interruption guard")
            client.close()
            if scenario == "reconnect":
                ledger.transition()
                result["events"].append(
                    {"epoch_activated_ns": monotonic_ns(), "epoch": 1}
                )
                recovered = open_connection(1)
                complete(acquire(recovered, 1))
                complete(held)
            else:
                complete(held)
        elif scenario == "blocked-read":
            complete(held)
            server.command("stall")
            # Drain already transported buffers. A bounded empty read is observed,
            # rather than assuming the server acknowledgment flushes native queues.
            drain_deadline = monotonic() + STARTUP_S
            while item := client.pull(0, 0.2):
                complete(item)
                if monotonic() >= drain_deadline:
                    raise TimeoutError("stall did not reach an empty acquisition")
            entered, finished = Event(), Event()
            reading: dict = {}

            def read() -> None:
                reading["read_enter_ns"] = monotonic_ns()
                entered.set()
                try:
                    reading["returned_sample"] = client.pull(0, 5) is not None
                except Exception as error:
                    reading["error"] = type(error).__name__
                finally:
                    reading["read_return_ns"] = monotonic_ns()
                    finished.set()

            reader = Thread(target=read, name="bounded-rtsp-reader")
            reader.start()
            if not entered.wait(JOIN_S) or finished.wait(0.1):
                raise RuntimeError("read was not pending at shutdown boundary")
            client.close()
            reader.join(JOIN_S)
            result["blocked_read"] = reading
            if (
                reader.is_alive()
                or reading.get("returned_sample") is not False
                or "error" in reading
            ):
                raise RuntimeError("blocked read failed to wake empty at NULL")
        if not client.closed:
            result["snapshots"].append(client.snapshot())
        if not client.rtp or not client.receipts:
            raise RuntimeError("missing transport evidence")
        for observed_client in clients:
            if any(
                b["pts"] <= a["pts"]
                for a, b in zip(
                    observed_client.receipts, observed_client.receipts[1:], strict=False
                )
            ):
                raise RuntimeError("decoder PTS did not advance within connection")
            observed_client.symptoms()
            if config.scenario not in ("interruption", "reconnect") and any(
                e["type"] == "error" for e in observed_client.bus_events
            ):
                raise RuntimeError("unexpected client bus error")
        if scenario == "slow":
            dropped = result["snapshots"][0]["appsink"]["dropped"]
            if (config.policy == "leaky" and dropped <= 0) or (
                config.policy == "fifo" and dropped != 0
            ):
                raise RuntimeError("slow-consumer native drop control failed")
        obsolete = [d for d in result["decisions"] if d["obsolete"]]
        if scenario in ("epoch", "reconnect") and len(obsolete) != 1:
            raise RuntimeError(
                "held old result was not classified obsolete exactly once"
            )
        if any(d["published"] == config.filtered for d in obsolete):
            raise RuntimeError("final epoch admission control failed")
        result["status"] = "ok"
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error))
    finally:
        cleanup_errors = []
        for client in reversed(clients):
            try:
                client.close()
            except Exception as error:
                cleanup_errors.append(str(error))
        if reader is not None:
            reader.join(JOIN_S)
        for server in reversed(servers):
            try:
                server.stop()
            except Exception as error:
                cleanup_errors.append(str(error))
        result["clients"] = [
            {
                "generation": c.generation,
                "receipts": c.receipts,
                "decoder_pad": c.pad_events,
                "rtp_packets": c.rtp,
                "bus": c.bus_events,
                "cleanup": c.close_record,
                "callback_errors": c.callback_errors,
                "runtime": c.runtime,
                "pre_null_snapshot": getattr(c, "pre_null", None),
            }
            for c in clients
        ]
        result["cleanup"] = {
            "errors": cleanup_errors,
            "owned_children_remaining": len(multiprocessing.active_children()),
            "extra_python_threads": len(enumerate_threads()) - 1,
            "all_clients_null": all(c.closed for c in clients),
        }
        if (
            cleanup_errors
            or result["cleanup"]["owned_children_remaining"]
            or result["cleanup"]["extra_python_threads"]
            or not result["cleanup"]["all_clients_null"]
        ):
            result["status"] = "error"
        if any(c.callback_errors for c in clients):
            result["status"] = "error"
    return result


def run_isolated(config: RtspConfig, *, fault: str | None = None) -> dict:
    """One attempt only, with a watchdog covering trial and server descendants."""
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "video_freshness_lab.rtsp_experiment",
            "--trial",
            json.dumps({"config": asdict(config), "fault": fault}),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=TRIAL_S)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        return {
            "config": asdict(config),
            "status": "error",
            "error": "30-second process-group watchdog",
        }
    try:
        result = json.loads(stdout)
    except (ValueError, TypeError):
        return {
            "config": asdict(config),
            "status": "error",
            "error": "child produced no valid report",
            "exitcode": process.returncode,
            "stderr": stderr,
        }
    result["child_exitcode"] = process.returncode
    # Preserve native diagnostics locally, without copying debug endpoints to docs.
    result["stderr"] = stderr
    if process.returncode != 0:
        result["status"] = "error"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial")
    parser.add_argument("--repeat", type=int, default=5)
    args = parser.parse_args()
    if args.trial:
        payload = json.loads(args.trial)
        result = trial(RtspConfig(**payload["config"]), fault=payload.get("fault"))
        print(json.dumps(result))
        raise SystemExit(0 if result["status"] == "ok" else 1)
    if not 1 <= args.repeat <= 100:
        parser.error("repeat must be in [1, 100]")
    results = []
    # Normal controls precede faults. Every failure is retained, never retried away.
    for scenario in SCENARIOS:
        for policy in ("fifo", "leaky"):
            for filtered in (False, True):
                for repetition in range(args.repeat):
                    result = run_isolated(RtspConfig(scenario, policy, filtered))
                    result["repetition"] = repetition
                    results.append(result)
                    print(
                        f"{scenario}/{policy}/{filtered}/{repetition}: {result['status']}",
                        file=sys.stderr,
                        flush=True,
                    )
        if scenario == "normal" and any(r["status"] != "ok" for r in results):
            break
    print(json.dumps({"results": results}))
    raise SystemExit(int(any(r["status"] != "ok" for r in results)))


if __name__ == "__main__":
    main()
