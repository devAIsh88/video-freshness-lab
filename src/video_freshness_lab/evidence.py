"""Pure evidence diagnostics; no clock reads, transport, or publication policy."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

from .model import integer

Trust = Literal["unknown", "reported", "verified"]
AgeStatus = Literal["fresh", "stale", "unknown"]


@dataclass(frozen=True, slots=True)
class Timestamp:
    """Raw ticks and seconds per tick; invalid/missing bases remain diagnosable.

    A domain identifies both a clock origin and its continuous timeline segment.
    Verified means the caller has substantiated the meaning, not authentication.
    """

    ticks: int
    time_base: Fraction | None = None
    domain: str | None = None
    provenance: str | None = None
    trust: Trust = "unknown"

    def __post_init__(self) -> None:
        if type(self.ticks) is not int:
            raise TypeError("timestamp ticks must be an integer")
        if self.time_base is not None and not isinstance(self.time_base, Fraction):
            raise TypeError("time base must be an exact Fraction or None")
        if self.trust not in ("unknown", "reported", "verified"):
            raise ValueError("unknown timestamp trust")
        _optional_text(self.domain, self.provenance)

    def nanoseconds(self) -> Fraction | None:
        if self.time_base is None or self.time_base <= 0:
            return None
        return self.ticks * self.time_base * 1_000_000_000


def _optional_text(*values: str | None) -> None:
    if any(v is not None and (not isinstance(v, str) or not v.strip()) for v in values):
        raise ValueError("text must be nonempty or None")


@dataclass(frozen=True, slots=True)
class FrameEvidence:
    source_id: str | None
    epoch: int | None
    sequence: int | None
    provenance: str | None = None
    sequence_kind: Literal["source_order", "local_delivery", "unknown"] = "unknown"
    arrival_ns: int | None = None
    arrival_domain: str | None = None
    pts: Timestamp | None = None
    capture: Timestamp | None = None
    decoder_metadata: tuple[tuple[str, str], ...] = ()
    admission: Literal["accepted", "rejected", "unknown"] = "unknown"
    admission_reason: str | None = None

    def __post_init__(self) -> None:
        for name in ("epoch", "sequence", "arrival_ns"):
            value = getattr(self, name)
            if value is not None:
                integer(name, value)
        _optional_text(
            self.source_id, self.provenance, self.arrival_domain, self.admission_reason
        )
        if self.sequence_kind not in ("source_order", "local_delivery", "unknown"):
            raise ValueError("unknown sequence kind")
        if self.admission not in ("accepted", "rejected", "unknown"):
            raise ValueError("unknown admission")
        for stamp in (self.pts, self.capture):
            if stamp is not None and not isinstance(stamp, Timestamp):
                raise TypeError("timestamp metadata must be Timestamp or None")
        if type(self.decoder_metadata) is not tuple or any(
            type(pair) is not tuple
            or len(pair) != 2
            or any(not isinstance(part, str) for part in pair)
            for pair in self.decoder_metadata
        ):
            raise TypeError("decoder metadata must be immutable string pairs")


@dataclass(frozen=True, slots=True)
class Diagnostic:
    evidence: FrameEvidence
    session: Literal["current", "obsolete_session", "unknown"]
    age_status: AgeStatus
    age_ns: Fraction | None
    age_reference: Literal["arrival", "capture"]
    issues: tuple[str, ...]


def _timestamp_issues(name: str, stamp: Timestamp | None) -> list[str]:
    if stamp is None:
        return [f"missing_{name}"]
    issues = []
    if stamp.time_base is None:
        issues.append(f"missing_{name}_time_base")
    elif stamp.time_base <= 0:
        issues.append(f"invalid_{name}_time_base")
    if stamp.domain is None:
        issues.append(f"missing_{name}_domain")
    if stamp.provenance is None or stamp.trust == "unknown":
        issues.append(f"missing_{name}_provenance")
    return issues


def diagnose(
    evidence: FrameEvidence,
    *,
    current_source: str | None,
    current_epoch: int | None,
    now_ns: int,
    clock_domain: str,
    max_age_ns: int,
    age_reference: Literal["arrival", "capture"] = "capture",
    previous: FrameEvidence | None = None,
    max_pts_gap_ns: int | None = None,
) -> Diagnostic:
    """Evaluate one observation, optionally against a same-session predecessor.

    Session and age are independent. 'fresh' refers only to age_reference and
    max_age_ns, never an overall admission decision. Equal age passes. An optional
    PTS gap budget detects a declared discontinuity, not a decoder defect.
    """
    integer("now_ns", now_ns)
    integer("max_age_ns", max_age_ns)
    if current_epoch is not None:
        integer("current_epoch", current_epoch)
    if max_pts_gap_ns is not None:
        integer("max_pts_gap_ns", max_pts_gap_ns)
    _optional_text(current_source, clock_domain)
    if clock_domain is None:
        raise ValueError("evaluation requires a clock domain")
    if age_reference not in ("arrival", "capture"):
        raise ValueError("unknown age reference")

    issues = []
    if evidence.provenance is None:
        issues.append("missing_provenance")
    if evidence.sequence is None or evidence.sequence_kind == "unknown":
        issues.append("unknown_frame_order")
    session: Literal["current", "obsolete_session", "unknown"] = "unknown"
    if (
        evidence.source_id is None
        or evidence.epoch is None
        or current_source is None
        or current_epoch is None
    ):
        issues.append("missing_session_provenance")
    elif (evidence.source_id, evidence.epoch) != (current_source, current_epoch):
        session = "obsolete_session"
        issues.append("session_mismatch")
    else:
        session = "current"
    issues.extend(_timestamp_issues("pts", evidence.pts))
    issues.extend(_timestamp_issues("capture", evidence.capture))
    if evidence.arrival_ns is None or evidence.arrival_domain is None:
        issues.append("missing_arrival_reference")

    same_session = (
        previous is not None
        and evidence.source_id is not None
        and evidence.epoch is not None
        and (previous.source_id, previous.epoch) == (evidence.source_id, evidence.epoch)
    )
    if same_session:
        assert previous is not None
        if (
            evidence.sequence_kind != "unknown"
            and evidence.sequence_kind == previous.sequence_kind
            and evidence.provenance is not None
            and evidence.provenance == previous.provenance
            and evidence.sequence is not None
            and previous.sequence is not None
            and evidence.sequence <= previous.sequence
        ):
            issues.append("frame_identity_not_advancing")
        if (
            evidence.arrival_ns is not None
            and previous.arrival_ns is not None
            and evidence.arrival_domain is not None
            and evidence.arrival_domain == previous.arrival_domain
            and evidence.arrival_ns < previous.arrival_ns
        ):
            issues.append("arrival_regression")
        before, after = previous.pts, evidence.pts
        if before is not None and after is not None:
            before_ns, after_ns = before.nanoseconds(), after.nanoseconds()
            if (
                before.domain is None
                or before.domain != after.domain
                or before.provenance is None
                or before.provenance != after.provenance
                or before.trust == "unknown"
                or after.trust == "unknown"
                or before_ns is None
                or after_ns is None
            ):
                issues.append("incomparable_pts")
            else:
                delta = after_ns - before_ns
                if delta < 0:
                    issues.append("pts_regression")
                elif max_pts_gap_ns is not None and delta > max_pts_gap_ns:
                    issues.append("pts_discontinuity")

    reference: Fraction | None = None
    if age_reference == "arrival":
        if evidence.arrival_domain == clock_domain and evidence.arrival_ns is not None:
            reference = Fraction(evidence.arrival_ns)
    elif evidence.capture is not None:
        capture = evidence.capture
        if (
            capture.trust == "verified"
            and capture.provenance is not None
            and capture.domain == clock_domain
        ):
            reference = capture.nanoseconds()
    age = None if reference is None else Fraction(now_ns) - reference
    status: AgeStatus = "unknown"
    if (
        evidence.arrival_domain == clock_domain
        and evidence.arrival_ns is not None
        and evidence.arrival_ns > now_ns
    ):
        issues.append("arrival_after_evaluation")
        age = None
    elif age is None:
        issues.append("insufficient_age_evidence")
    elif age < 0:
        issues.append("future_age_reference")
        age = None
    elif (
        age_reference == "capture"
        and evidence.arrival_domain == clock_domain
        and evidence.arrival_ns is not None
        and reference > evidence.arrival_ns
    ):
        issues.append("capture_after_arrival")
        age = None
    else:
        status = "stale" if age > max_age_ns else "fresh"
        if status == "stale":
            issues.append("age_budget_exceeded")
    return Diagnostic(evidence, session, status, age, age_reference, tuple(issues))
