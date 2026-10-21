"""Opt-in finite TCP fault assessment using the existing local RTSP fixture."""

import argparse
import json
import multiprocessing
import os
import signal
import subprocess
import sys
from dataclasses import asdict, dataclass
from threading import Event, Thread
from threading import enumerate as enumerate_threads
from time import monotonic, monotonic_ns

from .gstreamer_contract import PublicationLedger
from .rtsp_contract import RtspConfig
from .rtsp_experiment import Client, OwnedServer
from .transport_relay import FixtureRelay

SCENARIOS = (
    "baseline",
    "delay",
    "close",
    "stall",
    "cycles",
    "slow-interruption",
    "shutdown",
    "epoch",
    "recovery",
)


@dataclass(frozen=True, slots=True)
class FaultConfig:
    scenario: str
    policy: str = "fifo"
    filtered: bool = False

    def __post_init__(self) -> None:
        if self.scenario not in SCENARIOS:
            raise ValueError("unknown transport scenario")
        RtspConfig("normal", self.policy, self.filtered)


def assess(config: FaultConfig, *, fault: str | None = None) -> dict:
    result: dict = {
        "config": asdict(config),
        "status": "error",
        "events": [],
        "decisions": [],
        "recoveries": [],
        "detections": [],
        "resumptions": [],
        "snapshots": [],
        "timeout_count": 0,
        "unsupported": [
            "capture timestamp/age/freshness",
            "source frame identity/lag",
            "physical source epoch",
            "UDP loss",
            "end-to-end frame loss",
        ],
    }
    clients: list[Client] = []
    server: OwnedServer | None = None
    relay: FixtureRelay | None = None
    reader: Thread | None = None
    ledger = PublicationLedger(config.filtered)
    epoch = 0

    def open_client() -> tuple[Client, tuple]:
        attempt = {
            "generation": len(clients),
            "open_request_ns": monotonic_ns(),
            "success": False,
        }
        result["recoveries"].append(attempt)
        client = Client(
            relay.port,
            RtspConfig("normal", config.policy, config.filtered),
            len(clients),
        )
        clients.append(client)
        client.start()
        item = acquire(client)
        attempt.update(success=True, first_receipt_ns=item[1]["receipt_ns"])
        return client, item

    def acquire(client: Client):
        item = client.pull(epoch)
        if item is None:
            raise TimeoutError("acquisition guard expired")
        return item

    def complete(item) -> None:
        evidence, receipt = item
        decision = ledger.complete(len(result["decisions"]), evidence, monotonic_ns())
        decision.update(
            generation=int(evidence.decoder_metadata[0][1]),
            delivery_ordinal=evidence.sequence,
            receipt_to_decision_ns=decision["decision_ns"] - receipt["receipt_ns"],
            capture_age_ns=None,
        )
        result["decisions"].append(decision)

    def drain(client: Client) -> None:
        deadline = monotonic() + 5
        while item := client.pull(epoch, 0.1):
            complete(item)
            if monotonic() >= deadline:
                raise TimeoutError("transport stall drain guard")
        result["events"].append({"empty_receipt_observed_ns": monotonic_ns()})

    def hold_media() -> int:
        after = len(relay.events)
        relay.command("stall")
        event = relay.wait_event("held", after)
        if fault == "abort-held":
            raise RuntimeError("injected abort with transport media retained")
        return event["at_ns"]

    def resume(client: Client) -> None:
        released = relay.command("release")
        item = acquire(client)
        result["resumptions"].append(
            {"release_ns": released, "receipt_ns": item[1]["receipt_ns"]}
        )
        complete(item)

    def cut_detect(client: Client) -> None:
        cut = relay.command("cut")
        deadline = monotonic() + 3
        while monotonic() < deadline:
            item = client.pull(epoch, 0.05)
            if item is not None:
                complete(item)
            if client.symptoms():
                symptom = next(e for e in client.bus_events if e["at_ns"] >= cut)
                result["detections"].append(
                    {
                        "cut_ns": cut,
                        "observed_ns": symptom["at_ns"],
                        "type": symptom["type"],
                    }
                )
                return
        raise TimeoutError("terminal bus symptom guard")

    try:
        server = OwnedServer(result["events"])
        server.ready()
        relay = FixtureRelay(server.port)
        client, held = open_client()
        scenario = config.scenario
        if scenario == "baseline":
            complete(held)
            for _ in range(3):
                complete(acquire(client))
        elif scenario == "delay":
            complete(held)
            after = len(relay.events)
            relay.command("delay")
            relay.wait_event("held", after)
            released = relay.wait_event("forwarded-held", after)
            if released["at_ns"] - released["hold_started_ns"] < 200_000_000:
                raise RuntimeError("declared media delay not applied")
            complete(acquire(client))
        elif scenario in ("close", "cycles", "slow-interruption"):
            if scenario == "slow-interruption":
                server.production_phase(10)
                client.wait(rendered=8 if config.policy == "leaky" else 3, ingress=4)
                result["snapshots"].append(client.snapshot())
            for _ in range(3 if scenario == "cycles" else 1):
                cut_detect(client)
                client.close()
                ledger.transition()
                epoch += 1
                result["events"].append(
                    {"epoch": epoch, "activated_ns": monotonic_ns()}
                )
                client, new_held = open_client()
                complete(held)
                held = new_held
            complete(held)
        else:
            if scenario != "epoch":
                complete(held)
            hold_media()
            drain(client)
            if scenario == "shutdown":
                entered, finished = Event(), Event()
                reading: dict = {}

                def read() -> None:
                    reading["entered_ns"] = monotonic_ns()
                    entered.set()
                    try:
                        reading["sample_returned"] = client.pull(epoch, 5) is not None
                    except Exception as error:
                        reading["error"] = type(error).__name__
                    finally:
                        reading["returned_ns"] = monotonic_ns()
                        finished.set()

                reader = Thread(target=read, name="transport-pending-reader")
                reader.start()
                if not entered.wait(3) or finished.wait(0.1):
                    raise RuntimeError("pending reader control did not remain pending")
                client.close()
                reader.join(3)
                result["pending_read"] = reading
                if (
                    reader.is_alive()
                    or reading.get("sample_returned") is not False
                    or "error" in reading
                ):
                    raise RuntimeError("interrupted reader failed empty NULL wakeup")
                if reading["returned_ns"] < client.close_record["null_request_ns"]:
                    raise RuntimeError("read finished before NULL request")
            else:
                if scenario == "epoch":
                    ledger.transition()
                    epoch += 1
                    result["events"].append(
                        {"epoch": epoch, "activated_ns": monotonic_ns()}
                    )
                    complete(held)
                resume(client)
                if scenario == "recovery":
                    for _ in range(2):
                        complete(acquire(client))
        relay.check()
        for observed in clients:
            if not observed.closed:
                observed.symptoms()
                if observed.bus_events:
                    raise RuntimeError(
                        "unexpected terminal bus symptom on active connection"
                    )
        expected_obsolete = (
            3
            if scenario == "cycles"
            else int(scenario in ("close", "slow-interruption", "epoch"))
        )
        obsolete = [d for d in result["decisions"] if d["obsolete"]]
        if len(obsolete) != expected_obsolete or any(
            d["published"] == config.filtered for d in obsolete
        ):
            raise RuntimeError("held-work epoch control failed")
        result["status"] = "ok"
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error))
        result["timeout_count"] += int(isinstance(error, TimeoutError))
    finally:
        cleanup_errors = []
        if relay is not None:
            try:
                result["relay"] = relay.close()
            except Exception as error:
                cleanup_errors.append("relay: " + str(error))
        for client in reversed(clients):
            try:
                client.close()
            except Exception as error:
                cleanup_errors.append("client: " + str(error))
        if reader is not None:
            reader.join(3)
        if server is not None:
            try:
                server.stop()
            except Exception as error:
                cleanup_errors.append("server: " + str(error))
        result["clients"] = []
        for client in clients:
            pts = [r["pts"] for r in client.receipts]
            deltas = [b - a for a, b in zip(pts, pts[1:], strict=False)]
            result["clients"].append(
                {
                    "generation": client.generation,
                    "receipts": client.receipts,
                    "bus": client.bus_events,
                    "runtime": client.runtime,
                    "rtp_observations": len(client.rtp),
                    "cleanup": client.close_record,
                    "callback_errors": client.callback_errors,
                    "snapshot": getattr(client, "pre_null", None),
                    "continuity": {
                        "domain": f"decoder-generation-{client.generation}",
                        "pts_deltas_ns": deltas,
                        "nonadvancing": sum(d <= 0 for d in deltas),
                        "gaps_over_150ms": sum(d > 150_000_000 for d in deltas),
                        "source_continuity": None,
                    },
                }
            )
            if client.callback_errors or any(d <= 0 for d in deltas):
                result["status"] = "error"
        result["cleanup"] = {
            "errors": cleanup_errors,
            "remaining_owned_children": len(multiprocessing.active_children()),
            "remaining_python_threads": len(enumerate_threads()) - 1,
            "all_clients_null": all(c.closed for c in clients),
        }
        relay_report = result.get("relay", {})
        if (
            cleanup_errors
            or result["cleanup"]["remaining_owned_children"]
            or result["cleanup"]["remaining_python_threads"]
            or not result["cleanup"]["all_clients_null"]
            or not relay_report.get("worker_joined")
            or not relay_report.get("port_refused")
            or not relay_report.get("connected_sockets_closed")
            or relay_report.get("errors")
            or relay_report.get("negotiated_connections") != len(clients)
            or relay_report.get("counts", {}).get("connections") != len(clients)
        ):
            result["status"] = "error"
    return result


def run_isolated(
    config: FaultConfig, *, timeout_s: float = 30, fault: str | None = None
) -> dict:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "video_freshness_lab.transport_experiment",
            "--trial",
            json.dumps({"config": asdict(config), "fault": fault}),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        return {
            "config": asdict(config),
            "status": "error",
            "timeout_count": 1,
            "error": "process-group watchdog expired",
            "cleanup": None,
        }
    try:
        result = json.loads(stdout)
    except ValueError:
        return {
            "config": asdict(config),
            "status": "error",
            "error": "invalid child report",
            "stderr": stderr,
            "timeout_count": 0,
        }
    result.update(child_exitcode=process.returncode, stderr=stderr)
    if process.returncode:
        result["status"] = "error"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial")
    parser.add_argument("--repeat", type=int, default=20)
    parser.add_argument("--scenario", choices=SCENARIOS, action="append")
    args = parser.parse_args()
    if args.trial:
        payload = json.loads(args.trial)
        result = assess(FaultConfig(**payload["config"]), fault=payload.get("fault"))
        print(json.dumps(result))
        raise SystemExit(int(result["status"] != "ok"))
    if not 1 <= args.repeat <= 100:
        parser.error("repeat must be in [1, 100]")
    results = []
    for scenario in args.scenario or SCENARIOS:
        for policy in ("fifo", "leaky"):
            for filtered in (False, True):
                for repetition in range(args.repeat):
                    result = run_isolated(FaultConfig(scenario, policy, filtered))
                    result["repetition"] = repetition
                    results.append(result)
                    print(
                        f"{scenario}/{policy}/{filtered}/{repetition}: {result['status']}",
                        file=sys.stderr,
                        flush=True,
                    )
        if scenario == "baseline" and any(r["status"] != "ok" for r in results):
            break
    print(json.dumps({"results": results}))
    raise SystemExit(int(any(r["status"] != "ok" for r in results)))


if __name__ == "__main__":
    main()
