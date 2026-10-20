"""Optional, finite native-library experiment; GI is imported only in a child.

Run with system Python and PYTHONPATH=src. Every case has its own subprocess
watchdog; the normal Python-only suite never imports GI or launches a pipeline.
"""

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, replace
from fractions import Fraction
from importlib.metadata import version
from threading import Condition
from threading import enumerate as enumerate_threads
from time import monotonic_ns

from .evidence import FrameEvidence, Timestamp
from .gstreamer_contract import (
    WORKLOADS,
    ExperimentConfig,
    PublicationLedger,
    accounting,
    associate,
    encode_id,
)


class NativeCase:
    """One finite source, native streaming task, owner-driven consumer/controller."""

    def __init__(self, config: ExperimentConfig, *, fault: str | None = None) -> None:
        import gi

        gi.require_version("Gst", "1.0")
        gi.require_version("GstApp", "1.0")
        from gi.repository import Gst, GstApp

        Gst.init(None)
        self.Gst, self.GstApp = Gst, GstApp
        self.config, self.fault = config, fault
        self.condition = Condition()
        self.registry: dict[int, FrameEvidence] = {}
        self.submitted_ns: dict[int, int] = {}
        self.ingress: list[dict] = []
        self.receipts: list[dict] = []
        self.decisions: list[dict] = []
        self.rendered = 0
        self.eos_seen = False
        self.eos_at_pad = False
        self.callback_errors: list[str] = []
        self.snapshots: list[dict] = []
        self.ledger = PublicationLedger(config.session_filter)
        self.pipeline = Gst.Pipeline.new("finite-evidence-experiment")
        self.source = Gst.ElementFactory.make("appsrc", "source")
        self.sink = Gst.ElementFactory.make("appsink", "sink")
        if self.source is None or self.sink is None:
            raise RuntimeError("appsrc/appsink factory unavailable")
        for element in (self.source, self.sink):
            for prop in ("max-buffers", "leaky-type", "in", "out", "dropped"):
                if element.find_property(prop) is None:
                    raise RuntimeError(f"required native property unavailable: {prop}")
        # Appsrc buffering is finite and measured, not an invisible extra queue.
        self.source.set_property("max-buffers", 4)
        self.source.set_property("max-bytes", 0)
        self.source.set_property("max-time", 0)
        self.source.set_property("block", False)
        self.source.set_property("leaky-type", 0)
        self.source.set_property("format", Gst.Format.TIME)
        self.source.set_property("is-live", True)
        self.source.set_property("do-timestamp", False)
        self.source.set_property(
            "caps", Gst.Caps.from_string("application/x-vfl-synthetic")
        )
        self.sink.set_property("max-buffers", 2)
        self.sink.set_property("max-bytes", 0)
        self.sink.set_property("max-time", 0)
        self.sink.set_property("leaky-type", 2 if config.policy == "leaky" else 0)
        self.sink.set_property("sync", False)
        self.sink.set_property("async", False)
        self.sink.set_property("enable-last-sample", False)
        self.sink.set_property("emit-signals", True)
        self.sink.set_property("wait-on-eos", fault == "eos-wait")
        self.pipeline.add(self.source)
        self.pipeline.add(self.sink)
        if not self.source.link(self.sink):
            raise RuntimeError("direct appsrc/appsink link failed")
        self.bus = self.pipeline.get_bus()
        self.probe = self.sink.get_static_pad("sink").add_probe(
            Gst.PadProbeType.BUFFER | Gst.PadProbeType.EVENT_DOWNSTREAM, self._arrival
        )
        self.signal = self.sink.connect("new-sample", self._rendered)

    def _arrival(self, pad, info):
        try:
            if info.type & self.Gst.PadProbeType.EVENT_DOWNSTREAM:
                if info.get_event().type == self.Gst.EventType.EOS:
                    with self.condition:
                        self.eos_at_pad = True
                        self.condition.notify_all()
                return self.Gst.PadProbeReturn.OK
            buffer = info.get_buffer()
            token, _ = associate(
                buffer.extract_dup(0, buffer.get_size()), self.registry
            )
            with self.condition:
                self.ingress.append({"token": token, "pad_arrival_ns": monotonic_ns()})
                self.condition.notify_all()
            return self.Gst.PadProbeReturn.OK
        except Exception as error:
            with self.condition:
                self.callback_errors.append(type(error).__name__)
                self.condition.notify_all()
            return self.Gst.PadProbeReturn.DROP

    def _rendered(self, sink):
        # Signal emitted after queue insertion. Do not pull in this callback.
        with self.condition:
            self.rendered += 1
            self.condition.notify_all()
        return self.Gst.FlowReturn.OK

    def check_bus(self) -> None:
        # pop_filtered discards other message types. Keep EOS while checking errors.
        while (
            message := self.bus.pop_filtered(
                self.Gst.MessageType.ERROR | self.Gst.MessageType.EOS
            )
        ) is not None:
            if message.type == self.Gst.MessageType.EOS:
                self.eos_seen = True
                continue
            error, _debug = message.parse_error()
            raise RuntimeError(
                f"GStreamer bus error {error.domain}/{error.code}: {error.message}"
            )
        if self.callback_errors:
            raise RuntimeError(f"streaming callback error: {self.callback_errors}")

    def wait(self, *, ingress: int = 0, rendered: int = 0, eos: bool = False) -> None:
        with self.condition:
            ready = self.condition.wait_for(
                lambda: bool(self.callback_errors)
                or (
                    len(self.ingress) >= ingress
                    and self.rendered >= rendered
                    and (not eos or self.eos_at_pad)
                ),
                self.config.guard_s,
            )
        self.check_bus()
        if not ready:
            raise TimeoutError(
                f"boundary not reached: ingress={ingress}, rendered={rendered}"
            )

    def snapshot(self, label: str) -> dict:
        # Independent property reads. Only stable terminal observations support
        # conservation; intermediate observations are explicitly non-atomic.
        item = {"label": label, "at_ns": monotonic_ns(), "atomic": False}
        for name, element in (("appsrc", self.source), ("appsink", self.sink)):
            item[name] = {
                prop: element.get_property(prop)
                for prop in ("in", "out", "dropped", "current-level-buffers")
            }
        self.snapshots.append(item)
        return item

    def push(self, token: int, epoch: int = 0) -> None:
        sequence = token if epoch == 0 else token - 2
        pts = sequence * 10_000_000
        evidence = FrameEvidence(
            "synthetic-appsrc",
            epoch,
            sequence,
            provenance="explicit producer token registry",
            sequence_kind="source_order",
            pts=Timestamp(
                pts,
                Fraction(1, 1_000_000_000),
                f"media-epoch-{epoch}",
                "application assigned GstBuffer PTS",
                "reported",
            ),
            admission="accepted",
            admission_reason="registered synthetic submission",
        )
        self.registry[token] = evidence
        self.submitted_ns[token] = monotonic_ns()
        payload = encode_id(token + 100 if self.fault == "association" else token)
        buffer = self.Gst.Buffer.new_allocate(None, len(payload), None)
        buffer.fill(0, payload)
        buffer.pts, buffer.duration = pts, 10_000_000
        if self.source.emit("push-buffer", buffer) != self.Gst.FlowReturn.OK:
            raise RuntimeError("native submission failed")
        self.snapshot(f"submitted-{token}")

    def acquire(self) -> tuple[int, FrameEvidence]:
        sample = self.sink.emit(
            "try-pull-sample", int(self.config.guard_s * self.Gst.SECOND)
        )
        self.check_bus()
        if sample is None:
            raise TimeoutError("expected synthetic sample unavailable")
        at_ns = monotonic_ns()
        buffer = sample.get_buffer()
        token, original = associate(
            buffer.extract_dup(0, buffer.get_size()), self.registry
        )
        if any(item["token"] == token for item in self.receipts):
            raise ValueError("duplicate received token")
        if buffer.pts != original.pts.ticks:
            raise ValueError("PTS does not match registered evidence")
        evidence = replace(original, arrival_ns=at_ns, arrival_domain="local-monotonic")
        pad_at = next(
            item["pad_arrival_ns"] for item in self.ingress if item["token"] == token
        )
        self.receipts.append(
            {
                "token": token,
                "source_id": evidence.source_id,
                "epoch": evidence.epoch,
                "sequence": evidence.sequence,
                "pts_ns": buffer.pts,
                "arrival_ns": at_ns,
                "processing_start_ns": monotonic_ns(),
                "capture_age_ns": None,
                "pad_to_receipt_ns": at_ns - pad_at,
                "submission_to_receipt_ns": at_ns - self.submitted_ns[token],
            }
        )
        return token, evidence

    def complete(self, active: tuple[int, FrameEvidence]) -> None:
        if self.fault == "processing":
            raise RuntimeError("injected processing failure")
        token, evidence = active
        result = self.ledger.complete(token, evidence, monotonic_ns())
        result["arrival_age_ns"] = result["decision_ns"] - evidence.arrival_ns
        receipt = next(item for item in self.receipts if item["token"] == token)
        result["processing_ns"] = result["decision_ns"] - receipt["processing_start_ns"]
        self.decisions.append(result)

    def eos(self) -> None:
        if self.source.emit("end-of-stream") != self.Gst.FlowReturn.OK:
            raise RuntimeError("native EOS submission failed")

    def wait_eos(self) -> None:
        self.check_bus()
        if self.eos_seen:
            return
        message = self.bus.timed_pop_filtered(
            int(self.config.guard_s * self.Gst.SECOND),
            self.Gst.MessageType.EOS | self.Gst.MessageType.ERROR,
        )
        if message is None:
            raise TimeoutError("EOS bus message unavailable")
        if message.type == self.Gst.MessageType.ERROR:
            error, _ = message.parse_error()
            raise RuntimeError(
                f"GStreamer bus error {error.domain}/{error.code}: {error.message}"
            )
        self.eos_seen = True
        self.check_bus()

    def workload(self) -> dict:
        work = self.config.workload
        if self.fault == "bus-error":
            from gi.repository import GLib

            error = GLib.Error.new_literal(
                self.Gst.CoreError.quark(),
                "injected bus failure",
                self.Gst.CoreError.FAILED,
            )
            self.bus.post(self.Gst.Message.new_error(self.pipeline, error, "synthetic"))
            self.check_bus()
        if self.fault == "association":
            self.push(0)
            self.wait(ingress=1)
        if work in ("balanced", "pause"):
            for token in range(4):
                self.push(token)
                self.wait(rendered=token + 1)
                self.complete(self.acquire())
                if work == "pause" and token == 1:
                    # A finite event-delimited producer pause, no elapsed-time claim.
                    if self.sink.emit("try-pull-sample", 0) is not None:
                        raise ValueError("unexpected sample during producer pause")
                    self.snapshot("producer-paused-empty")
            self.eos()
        elif work == "shutdown":
            for token in range(2):
                self.push(token)
                self.wait(rendered=token + 1)
            self.eos()
            if self.fault == "eos-wait":
                self.wait(eos=True)
                if self.eos_seen:
                    raise ValueError("bus EOS arrived before pending buffers drained")
                self.snapshot("EOS-at-pad-before-drain")
                for _ in range(2):
                    self.complete(self.acquire())
        else:
            self.push(0)
            self.wait(rendered=1)
            active = self.acquire() if work in ("slow", "active-epoch") else None
            self.push(1)
            self.wait(rendered=2)
            if work.endswith("epoch"):
                self.ledger.transition()
            for token in range(2, 4):
                self.push(token, epoch=int(work.endswith("epoch")))
            # FIFO blocks the native task at the full sink queue. Leaky admits
            # the complete burst. This unavoidable scheduling difference is recorded.
            self.wait(
                ingress=3 if self.config.policy == "fifo" and active is None else 4,
                rendered=4 if self.config.policy == "leaky" else (3 if active else 2),
            )
            self.snapshot("withheld-consumer")
            if self.fault == "abort":
                raise RuntimeError("injected owner abort with pending buffers")
            self.eos()
            if active:
                self.complete(active)
            expected = (3 if active else 2) if self.config.policy == "leaky" else 4
            while len(self.receipts) < expected:
                self.complete(self.acquire())
            self.wait(rendered=4)
        self.wait_eos()
        final = self.snapshot("quiescent-before-NULL")
        received, published = (
            len(self.receipts),
            sum(d["published"] for d in self.decisions),
        )
        counts = accounting(
            submitted=len(self.registry),
            received=received,
            native_drops=final["appsink"]["dropped"],
            rejected=received - published,
            published=published,
            unpulled=final["appsink"]["current-level-buffers"],
        )
        if final["appsrc"]["current-level-buffers"] or final["appsrc"]["dropped"]:
            raise ValueError("unaccounted appsrc buffering/drop")
        if final["appsrc"]["out"] != len(self.registry):
            raise ValueError("appsrc did not forward all submissions")
        if final["appsink"]["out"] != received:
            raise ValueError("native receipt counter mismatch")
        return {"counts": counts, "eos": True, "ledger": self.ledger.events}

    def run(self) -> dict:
        baseline = set(enumerate_threads())
        report = {
            "config": asdict(self.config),
            "fault": self.fault,
            "gstreamer": self.Gst.version_string(),
            "python": sys.version.split()[0],
            "pygobject": version("PyGObject"),
            "app_plugin": self.source.get_factory().get_plugin().get_version(),
            "measurement_provenance": {
                "token_epoch": "exact payload token lookup in producer registry",
                "pts": "application assigned nanoseconds; media clock only",
                "local_times": "monotonic_ns; same process clock domain",
                "capture": "unavailable",
                "publication": "locked in-memory ledger; filtered only when configured",
            },
            "status": "error",
        }
        try:
            if (
                self.pipeline.set_state(self.Gst.State.PLAYING)
                == self.Gst.StateChangeReturn.FAILURE
            ):
                raise RuntimeError("pipeline could not enter PLAYING")
            report.update(self.workload())
            report["status"] = "ok"
        except Exception as error:
            report.update(error_type=type(error).__name__, error=str(error))
        finally:
            result = self.pipeline.set_state(self.Gst.State.NULL)
            state_result, state, pending = self.pipeline.get_state(
                int(self.config.guard_s * self.Gst.SECOND)
            )
            report["cleanup_null"] = (
                result != self.Gst.StateChangeReturn.FAILURE
                and state == self.Gst.State.NULL
                and state_result != self.Gst.StateChangeReturn.FAILURE
            )
            report["extra_python_threads"] = len(set(enumerate_threads()) - baseline)
            self.sink.disconnect(self.signal)
            self.sink.get_static_pad("sink").remove_probe(self.probe)
            report.update(
                receipts=self.receipts,
                decisions=self.decisions,
                ingress=self.ingress,
                snapshots=self.snapshots,
                submissions=[
                    {
                        "token": token,
                        "source_id": e.source_id,
                        "epoch": e.epoch,
                        "sequence": e.sequence,
                        "pts": e.pts.ticks,
                        "pts_time_base": [1, 1_000_000_000],
                        "submitted_ns": self.submitted_ns[token],
                        "identity_provenance": e.provenance,
                    }
                    for token, e in self.registry.items()
                ],
            )
            if not report["cleanup_null"] or report["extra_python_threads"]:
                report["status"] = "error"
        return report


def run_isolated(config: ExperimentConfig, *, fault: str | None = None) -> dict:
    """A hard process bound covers native calls as well as Python waits."""
    try:
        child = subprocess.run(
            [
                sys.executable,
                "-m",
                "video_freshness_lab.gstreamer_experiment",
                "--child",
                json.dumps({"config": asdict(config), "fault": fault}),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if child.returncode:
            return {
                "config": asdict(config),
                "status": "error",
                "error": "child failed",
                "stderr": child.stderr[-2000:],
            }
        return json.loads(child.stdout)
    except subprocess.TimeoutExpired:
        return {
            "config": asdict(config),
            "status": "error",
            "error": "subprocess watchdog expired",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--child", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        data = json.loads(args.child)
        report = NativeCase(
            ExperimentConfig(**data["config"]), fault=data["fault"]
        ).run()
        print(json.dumps(report))
        return 0
    if not 1 <= args.repeat <= 100:
        parser.error("repeat must be in [1, 100]")
    reports = [
        run_isolated(ExperimentConfig(policy, filtered, workload))
        for _ in range(args.repeat)
        for workload in WORKLOADS
        for policy in ("fifo", "leaky")
        for filtered in (False, True)
    ]
    print(
        json.dumps(
            {"cases": reports, "failures": sum(r["status"] != "ok" for r in reports)}
        )
    )
    return int(any(r["status"] != "ok" for r in reports))


if __name__ == "__main__":
    raise SystemExit(main())
