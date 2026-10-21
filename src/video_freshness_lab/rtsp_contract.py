"""Pure configuration and receipt sidecars for the optional loopback experiment."""

from dataclasses import dataclass
from fractions import Fraction

from .evidence import FrameEvidence, Timestamp
from .model import integer

SCENARIOS = ("normal", "interruption", "reconnect", "slow", "blocked-read", "epoch")


@dataclass(frozen=True, slots=True)
class RtspConfig:
    scenario: str
    policy: str = "fifo"
    filtered: bool = False

    def __post_init__(self) -> None:
        if self.scenario not in SCENARIOS or self.policy not in ("fifo", "leaky"):
            raise ValueError("unknown RTSP scenario or queue policy")
        if type(self.filtered) is not bool:
            raise ValueError("filtered must be boolean")


def receipt_evidence(
    *, generation: int, epoch: int, ordinal: int, receipt_ns: int, pts: int | None
) -> FrameEvidence:
    """Assign application lineage, never infer source identity from PTS or RTP."""
    integer("generation", generation)
    return FrameEvidence(
        source_id="loopback-fixture",
        epoch=epoch,
        sequence=ordinal,
        sequence_kind="local_delivery",
        provenance="controller-assigned output epoch; source frame identity unknown",
        arrival_ns=receipt_ns,
        arrival_domain="rtsp-client-monotonic",
        pts=None
        if pts is None
        else Timestamp(
            pts,
            Fraction(1, 1_000_000_000),
            f"decoder-generation-{generation}",
            "decoder buffer PTS; not capture time",
            "reported",
        ),
        decoder_metadata=(("connection_generation", str(generation)),),
    )
