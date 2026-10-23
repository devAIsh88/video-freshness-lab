"""Optional audit of unchanged FrameGrab's supported file reader, outside pure CI."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
from dataclasses import asdict
from pathlib import Path
from time import monotonic_ns
from typing import TYPE_CHECKING

from video_freshness_lab.evidence import FrameEvidence, diagnose
from video_freshness_lab.gstreamer_contract import PublicationLedger
from video_freshness_lab.model import Frame
from video_freshness_lab.stamped_images import generate, read_marker

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

TARGET_SHA = "17f550890b33925cbd92cf997776e64600954f87"
SCENARIOS = (
    "replay",
    "decimate",
    "static",
    "repeated",
    "seek",
    "crop",
    "epoch-native",
    "epoch-filtered",
)


def observe(pixels: NDArray[np.uint8], received_ns: int) -> FrameEvidence:
    """Decode source evidence; an unreadable stamp never gains a delivery ID."""
    marker = read_marker(pixels)
    return FrameEvidence(
        source_id=None if marker is None else f"generated-{marker.source}",
        epoch=None if marker is None else marker.epoch,
        sequence=None if marker is None else marker.sequence,
        sequence_kind="unknown" if marker is None else "source_order",
        provenance=None
        if marker is None
        else "source marker through FFV1/file consumer",
        arrival_ns=received_ns,
        arrival_domain="framegrab-audit-monotonic",
        capture=None,
    )


def write_fixture(path: Path, epoch: int, *, repeated: bool = False) -> None:
    import cv2

    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"FFV1"), 20, (160, 96))
    if not writer.isOpened():
        raise RuntimeError("FFV1 fixture writer unavailable")
    try:
        for slot in range(12):
            writer.write(generate(Frame(epoch, 0 if repeated else slot, 0)).pixels)
    finally:
        writer.release()


def trial(scenario: str, files: dict[str, Path], baseline_tasks: set[str]) -> dict:
    import numpy as np
    from framegrab import FrameGrabber

    owned = []
    records = []
    events = []
    previous = None
    result = {
        "scenario": scenario,
        "status": "error",
        "observations": records,
        "events": events,
        "decisions": [],
        "eof_observed": False,
    }
    started = monotonic_ns()
    workers = {t.ident for t in threading.enumerate()}

    def opened(name: str, max_fps: int = 30):
        grabber = FrameGrabber.create_grabber(
            {
                "input_type": "file",
                "name": "synthetic-file",
                "id": {"filename": str(files[name])},
                "options": {"max_fps": max_fps},
            }
        )
        owned.append(grabber)
        events.append({"kind": "opened", "at_ns": monotonic_ns()})
        result["backend"] = grabber.capture.getBackendName()
        assert grabber.get_fps() == 20
        return grabber

    def acquired(grabber, expected_epoch=0):
        nonlocal previous
        pixels = grabber.grab()
        evidence = observe(pixels, monotonic_ns())
        diagnostic = diagnose(
            evidence,
            current_source="generated-7",
            current_epoch=expected_epoch,
            now_ns=monotonic_ns(),
            clock_domain="framegrab-audit-monotonic",
            max_age_ns=0,
            previous=previous,
        )
        previous = evidence
        records.append(
            {
                "file_slot": grabber.get_last_frame_read_number(),
                "marker": None
                if read_marker(pixels) is None
                else asdict(read_marker(pixels)),
                "session": diagnostic.session,
                "capture_age": diagnostic.age_status,
                "source_sequence_lag": None,
                "issues": diagnostic.issues,
                "received_ns": evidence.arrival_ns,
            }
        )
        assert diagnostic.age_status == "unknown"
        events.append(
            {
                "kind": "acquired",
                "epoch": evidence.epoch,
                "sequence": evidence.sequence,
                "at_ns": evidence.arrival_ns,
            }
        )
        return pixels, evidence

    try:
        if scenario.startswith("epoch-"):
            old_grabber = opened("normal")
            old_pixels, old = acquired(old_grabber)
            old_grabber.release()
            ledger = PublicationLedger(scenario == "epoch-filtered")
            ledger.transition()
            events.append(
                {"kind": "epoch_activated", "epoch": 1, "at_ns": monotonic_ns()}
            )
            new_grabber = opened("new")
            _, new = acquired(new_grabber, 1)
            assert read_marker(old_pixels).epoch == 0
            for token, evidence in ((1, new), (0, old)):
                result["decisions"].append(
                    ledger.complete(token, evidence, monotonic_ns())
                )
            current, obsolete = result["decisions"]
            assert current["published"] and not current["obsolete"]
            assert obsolete["obsolete"]
            assert obsolete["published"] == (scenario == "epoch-native")
            result["old_output_diagnostic"] = asdict(
                diagnose(
                    old,
                    current_source="generated-7",
                    current_epoch=1,
                    now_ns=monotonic_ns(),
                    clock_domain="framegrab-audit-monotonic",
                    max_age_ns=0,
                )
            )
        else:
            grabber = opened(
                "repeated" if scenario == "repeated" else "normal",
                5 if scenario == "decimate" else 30,
            )
            if scenario == "crop":
                acquired(grabber)
                grabber.apply_options({"crop": {"pixels": {"top": 40}}})
                _, missing = acquired(grabber)
                assert missing.sequence is None and missing.epoch is None
                assert records[-1]["session"] == "unknown"
            elif scenario == "seek":
                acquired(grabber)
                acquired(grabber)
                grabber.seek_to_beginning()
                events.append({"kind": "seek_to_beginning", "at_ns": monotonic_ns()})
                acquired(grabber)
                assert [r["marker"]["sequence"] for r in records] == [0, 1, 0]
                assert "frame_identity_not_advancing" in records[-1]["issues"]
            else:
                count = 3 if scenario == "decimate" else 12
                pixels_seen = []
                for _ in range(count):
                    pixels, _ = acquired(grabber)
                    pixels_seen.append(pixels)
                expected = [3, 7, 11] if scenario == "decimate" else list(range(12))
                assert [r["file_slot"] for r in records] == expected
                assert [r["marker"]["sequence"] for r in records] == (
                    [0] * 12 if scenario == "repeated" else expected
                )
                repeats = sum(
                    "frame_identity_not_advancing" in r["issues"] for r in records
                )
                assert repeats == (11 if scenario == "repeated" else 0)
                if scenario in ("static", "repeated"):
                    roi = slice(None) if scenario == "repeated" else slice(80, None)
                    assert all(
                        np.array_equal(pixels_seen[0][roi], p[roi]) for p in pixels_seen
                    )
                    assert len({id(p) for p in pixels_seen}) == count
                try:
                    grabber.grab()
                except RuntimeWarning:
                    result["eof_observed"] = True
                assert result["eof_observed"], "finite source did not signal EOF"
        result["status"] = "ok"
    except Exception as error:
        result.update(status="error", error_type=type(error).__name__, error=str(error))
    finally:
        for grabber in owned:
            grabber.release()
        result["captures_closed"] = [not g.capture.isOpened() for g in owned]
        result["extra_python_threads"] = len(
            {t.ident for t in threading.enumerate()} - workers
        )
        cleanup_started = monotonic_ns()
        pending = {p.name for p in Path("/proc/self/task").iterdir()} - baseline_tasks
        result["immediate_native_tasks"] = len(pending)
        # Kernel task disappearance can follow capture.release(). Observe the
        # actual predicate within a guard, rather than infer exit from a sleep.
        while pending and monotonic_ns() - cleanup_started < 1_000_000_000:
            threading.Event().wait(0.001)
            pending = {
                p.name for p in Path("/proc/self/task").iterdir()
            } - baseline_tasks
        result["extra_native_tasks"] = len(pending)
        result["native_cleanup_observation_ns"] = monotonic_ns() - cleanup_started
        result["duration_ns"] = monotonic_ns() - started
        if (
            not all(result["captures_closed"])
            or result["extra_python_threads"]
            or result["extra_native_tasks"]
        ):
            result.update(status="error", error="cleanup invariant failed")
    return result


def worker(repeat: int) -> dict:
    def deny_socket(event, args):
        if event == "socket.__new__":
            raise RuntimeError("audit forbids Python socket creation")

    sys.addaudithook(deny_socket)
    import cv2
    import framegrab
    import framegrab.grabber
    import numpy as np

    cv2.setNumThreads(1)
    for module, expected in (
        (
            framegrab.grabber,
            "079bafebfdd58a00856b6380cfcb8cd222b1ffede4406e8167121a4b20800899",
        ),
        (
            sys.modules["framegrab.config"],
            "37bd98c5b6d9f341cec4da73844acc53a8ed9a4513590d7b2e3ce9c7f3958417",
        ),
    ):
        if hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() != expected:
            raise RuntimeError("target source differs from reviewed commit")
    build = cv2.getBuildInformation()
    gst_line = next(line.strip() for line in build.splitlines() if "GStreamer:" in line)
    baseline_tasks = {p.name for p in Path("/proc/self/task").iterdir()}
    results = []
    with tempfile.TemporaryDirectory(prefix="vfl-framegrab-media-") as directory:
        root = Path(directory)
        files = {name: root / f"{name}.avi" for name in ("normal", "repeated", "new")}
        write_fixture(files["normal"], 0)
        write_fixture(files["repeated"], 0, repeated=True)
        write_fixture(files["new"], 1)
        for scenario in SCENARIOS:
            for repetition in range(repeat):
                result = trial(scenario, files, baseline_tasks)
                result["repetition"] = repetition
                results.append(result)
            if scenario == "replay" and any(r["status"] != "ok" for r in results):
                break
    return {
        "target_commit": TARGET_SHA,
        "target_module_sha256": hashlib.sha256(
            Path(framegrab.grabber.__file__).read_bytes()
        ).hexdigest(),
        "versions": {
            "python": sys.version.split()[0],
            "framegrab": framegrab.__version__,
            "opencv": cv2.__version__,
            "numpy": np.__version__,
        },
        "installed": {
            d.metadata["Name"]: d.version for d in importlib.metadata.distributions()
        },
        "gstreamer_build_line": gst_line,
        "upstream_readme_check_claims_gstreamer": "GStreamer" in build,
        "open_socket_descriptors": sum(
            p.is_symlink() and os.readlink(p).startswith("socket:")
            for p in Path("/proc/self/fd").iterdir()
            if p.exists()
        ),
        "temporary_media_removed": not root.exists(),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=100)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 1 <= args.repeat <= 100:
        parser.error("repeat must be in [1, 100]")
    if args.worker:
        result = worker(args.repeat)
    else:
        child = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--repeat",
                str(args.repeat),
                "--worker",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            stdout, stderr = child.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.communicate()
            result = {
                "status": "error",
                "error": "120-second process-group watchdog",
                "returncode": child.returncode,
                "cleanup": "UNKNOWN",
                "results": [],
            }
        else:
            result = json.loads(stdout) if stdout else {"results": []}
            result.update(returncode=child.returncode, stderr=stderr)
    print(json.dumps(result))
    raise SystemExit(
        int(
            result.get("returncode", 0) != 0
            or not result.get("results")
            or any(r["status"] != "ok" for r in result.get("results", []))
        )
    )


if __name__ == "__main__":
    main()
