"""Optional actual-image lineage experiment; NumPy/OpenCV load only on use."""

from __future__ import annotations

import argparse
import json
import struct
import zlib
from dataclasses import asdict, dataclass, replace
from typing import TYPE_CHECKING

from .evidence import FrameEvidence, diagnose
from .model import Frame, integer
from .recovery_experiments import RECOVERY_SCENARIOS
from .simulation import Config, Simulator

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

WIRE = struct.Struct("!4sIII")
SHAPE = (96, 160, 3)
CELL = 4


@dataclass(frozen=True, slots=True)
class Marker:
    source: int
    epoch: int
    sequence: int

    def __post_init__(self) -> None:
        for name in ("source", "epoch", "sequence"):
            integer(name, getattr(self, name))
            if getattr(self, name) > 0xFFFFFFFF:
                raise ValueError("marker identifier exceeds uint32")

    def wire(self) -> bytes:
        body = WIRE.pack(b"VFL3", self.source, self.epoch, self.sequence)
        return body + struct.pack("!I", zlib.crc32(body))

    @classmethod
    def from_wire(cls, wire: bytes) -> Marker | None:
        if len(wire) != WIRE.size + 4:
            return None
        body, checksum = wire[:-4], wire[-4:]
        if struct.pack("!I", zlib.crc32(body)) != checksum:
            return None
        magic, source, epoch, sequence = WIRE.unpack(body)
        return cls(source, epoch, sequence) if magic == b"VFL3" else None


@dataclass(frozen=True, slots=True)
class StampedImage:
    pixels: NDArray[np.uint8]
    evidence: FrameEvidence


def immutable_pixels(pixels: NDArray[np.uint8]) -> NDArray[np.uint8]:
    import numpy as np

    # Immutable bytes backing also prevents re-enabling WRITEABLE on this view.
    return np.frombuffer(pixels.tobytes(), dtype=np.uint8).reshape(pixels.shape)


def generate(frame: Frame, source: int = 7) -> StampedImage:
    """Called at source production, before queue admission or consumption."""
    import cv2
    import numpy as np

    marker = Marker(source, frame.session_id, frame.sequence)
    pixels = np.empty(SHAPE, dtype=np.uint8)
    pixels[:] = (30, 50, 70)
    for i, bit in enumerate(
        np.unpackbits(np.frombuffer(marker.wire(), dtype=np.uint8))
    ):
        row, column = divmod(i, 16)
        pixels[row * CELL : (row + 1) * CELL, column * CELL : (column + 1) * CELL] = (
            240 if bit else 16
        )
    cv2.putText(
        pixels,
        f"s{source} e{frame.session_id} q{frame.sequence}",
        (4, 66),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (240, 240, 240),
        1,
        cv2.LINE_8,
    )
    evidence = FrameEvidence(
        source_id=f"generated-{source}",
        epoch=marker.epoch,
        sequence=marker.sequence,
        provenance="source-generated pixel marker, independently decoded at processing/output",
        sequence_kind="source_order",
        capture=None,
    )
    return StampedImage(immutable_pixels(pixels), evidence)


def read_marker(pixels: NDArray[np.uint8]) -> Marker | None:
    import numpy as np

    if (
        not isinstance(pixels, np.ndarray)
        or pixels.shape != SHAPE
        or pixels.dtype != np.uint8
    ):
        return None
    bits = []
    for i in range((WIRE.size + 4) * 8):
        row, column = divmod(i, 16)
        level = pixels[
            row * CELL : (row + 1) * CELL, column * CELL : (column + 1) * CELL
        ].mean()
        if 64 < level < 192:
            return None
        bits.append(int(level >= 192))
    return Marker.from_wire(np.packbits(bits).tobytes())


def transform(pixels: NDArray[np.uint8]) -> NDArray[np.uint8]:
    """Selected real path: BGR→gray→BGR→lossless PNG encode/decode in memory."""
    import cv2

    gray = cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)
    converted = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    ok, encoded = cv2.imencode(".png", converted)
    if not ok:
        raise RuntimeError("in-memory PNG encoding failed")
    decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if decoded is None:
        raise RuntimeError("in-memory PNG decoding failed")
    return immutable_pixels(decoded)


def verify(pixels: NDArray[np.uint8], evidence: FrameEvidence) -> Marker:
    marker = read_marker(pixels)
    if marker is None:
        raise ValueError("image identity UNKNOWN: unreadable marker")
    if (f"generated-{marker.source}", marker.epoch, marker.sequence) != (
        evidence.source_id,
        evidence.epoch,
        evidence.sequence,
    ):
        raise ValueError("image identity mismatch against original source evidence")
    return marker


class ImageSimulator(Simulator):
    """Thin image observation hook over the existing schedule and buffers."""

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.images: dict[str, StampedImage] = {}
        self.active_images: dict[str, StampedImage] = {}
        self.image_outputs: list[dict] = []

    def _event(self, kind, frame=None, reason=None, since_ms=None) -> None:
        if kind == "frame_produced":
            self.images[frame.frame_id] = generate(frame)
        elif kind == "processing_started":
            original = self.images[frame.frame_id]
            decoded = transform(original.pixels)
            verify(decoded, original.evidence)
            self.active_images[frame.frame_id] = StampedImage(
                decoded,
                replace(
                    original.evidence,
                    arrival_ns=self.clock.now_ms * 1_000_000,
                    arrival_domain="image-virtual-clock",
                ),
            )
        elif (
            frame is not None
            and kind in ("frame_consumed", "frame_dropped")
            and frame.frame_id in self.active_images
        ):
            active = self.active_images.pop(frame.frame_id)
            marker = verify(active.pixels, active.evidence)
            self.image_outputs.append(
                {
                    "marker": asdict(marker),
                    "decision_ms": self.clock.now_ms,
                    "published": kind == "frame_consumed",
                    "reason": reason,
                    "capture_age_ns": None,
                }
            )
        super()._event(kind, frame, reason, since_ms)


def workloads() -> dict[str, Config]:
    result = {}
    for policy in ("fifo", "latest"):
        result[f"balanced-{policy}"] = Config(policy=policy, freshness_threshold_ms=80)
        result[f"slow-{policy}"] = Config(
            policy=policy, consumer_duration_ms=40, freshness_threshold_ms=80
        )
        result[f"pause-{policy}"] = replace(RECOVERY_SCENARIOS["freeze"], policy=policy)
        for filtered in (False, True):
            result[f"restart-{policy}-{filtered}"] = replace(
                RECOVERY_SCENARIOS["reconnect"], policy=policy, session_filter=filtered
            )
    return result


def run_images(config: Config) -> dict:
    experiment = ImageSimulator(config)
    result = experiment.run()
    if (
        experiment.active_images
        or len(experiment.image_outputs) != result.metrics.frames_processed
    ):
        raise RuntimeError("image processing lineage did not drain")
    return {
        "metrics": asdict(result.metrics),
        "outputs": experiment.image_outputs,
        "produced_markers": [
            asdict(verify(i.pixels, i.evidence)) for i in experiment.images.values()
        ],
        "processing": result.to_dict()["processing"],
        "events": result.to_dict()["events"],
        "capture_freshness": "UNKNOWN",
        "time_reference": "injected simulator milliseconds",
    }


def repeated_content() -> dict:
    import numpy as np

    old = generate(Frame(0, 0, 0))
    delivered = [transform(old.pixels) for _ in range(3)]
    prior = None
    observations = []
    for ordinal, pixels in enumerate(delivered):
        marker = verify(pixels, old.evidence)
        evidence = replace(
            old.evidence, arrival_ns=ordinal * 10, arrival_domain="repeated-fixture"
        )
        d = diagnose(
            evidence,
            current_source=old.evidence.source_id,
            current_epoch=0,
            now_ns=30,
            clock_domain="repeated-fixture",
            max_age_ns=100,
            previous=prior,
        )
        observations.append(
            {
                "local_delivery": ordinal,
                "marker": asdict(marker),
                "repeated_identity": "frame_identity_not_advancing" in d.issues,
                "capture_freshness": d.age_status,
                "arrival_ns": evidence.arrival_ns,
            }
        )
        prior = evidence
    static = [transform(generate(Frame(0, i, i * 10)).pixels) for i in range(3)]
    return {
        "no_data_deliveries": 0,
        "repeat_observations": observations,
        "new_buffer_objects": len({id(p) for p in delivered}) == 3,
        "no_shared_memory": all(
            not np.shares_memory(a, b)
            for a, b in zip(delivered, delivered[1:], strict=False)
        ),
        "identical_repeated_pixels": all(
            np.array_equal(delivered[0], p) for p in delivered
        ),
        "static_scene_roi_equal": all(
            np.array_equal(static[0][80:], p[80:]) for p in static
        ),
        "static_scene_markers": [asdict(read_marker(p)) for p in static],
    }


def main() -> None:
    import cv2
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.repeat <= 100:
        parser.error("repeat must be in [1, 100]")
    cv2.setNumThreads(1)
    cases = {}
    for name, config in workloads().items():
        expected = run_images(config)
        failures = 0
        for _ in range(args.repeat):
            failures += run_images(config) != expected
        cases[name] = {"trials": args.repeat, "failed": failures, "result": expected}
    print(
        json.dumps(
            {
                "python_optional_versions": {
                    "opencv": cv2.__version__,
                    "numpy": np.__version__,
                },
                "cases": cases,
                "repeated_content": repeated_content(),
            }
        )
    )
    raise SystemExit(int(any(c["failed"] for c in cases.values())))


if __name__ == "__main__":
    main()
