"""Small pure helpers for the optional appsrc/appsink research experiment."""

import math
import struct
from dataclasses import dataclass
from threading import Lock
from typing import Literal

from .evidence import FrameEvidence
from .model import integer

WORKLOADS = ("balanced", "slow", "pause", "buffered-epoch", "active-epoch", "shutdown")
WIRE = struct.Struct("!5sQ")


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    policy: Literal["fifo", "leaky"]
    session_filter: bool
    workload: str
    guard_s: float = 3.0

    def __post_init__(self) -> None:
        if self.policy not in ("fifo", "leaky") or self.workload not in WORKLOADS:
            raise ValueError("unknown experimental policy/workload")
        if type(self.session_filter) is not bool:
            raise ValueError("session_filter must be boolean")
        if (
            isinstance(self.guard_s, bool)
            or not isinstance(self.guard_s, int | float)
            or not math.isfinite(self.guard_s)
            or not 0 < self.guard_s <= 10
        ):
            raise ValueError("guard_s must be finite and in (0, 10]")


def encode_id(token: int) -> bytes:
    integer("token", token)
    return WIRE.pack(b"VFL17", token)


def associate(
    payload: bytes, registry: dict[int, FrameEvidence]
) -> tuple[int, FrameEvidence]:
    """Resolve a wire token against the producer's explicit immutable sidecar."""
    if len(payload) != WIRE.size:
        raise ValueError("invalid synthetic payload length")
    magic, token = WIRE.unpack(payload)
    if magic != b"VFL17" or token not in registry:
        raise ValueError("unregistered synthetic payload ID")
    return token, registry[token]


class PublicationLedger:
    """Experiment-only final output boundary, equivalent to the 1.5 lock rule."""

    def __init__(self, session_filter: bool) -> None:
        if type(session_filter) is not bool:
            raise ValueError("session_filter must be boolean")
        self._lock = Lock()
        self._filter = session_filter
        self._epoch = 0
        self._events: list[dict[str, int | bool | None]] = []

    @property
    def events(self) -> tuple[dict[str, int | bool | None], ...]:
        with self._lock:
            return tuple(dict(event) for event in self._events)

    def transition(self) -> None:
        with self._lock:
            self._epoch += 1
            self._events.append({"transition": self._epoch})

    def complete(self, token: int, evidence: FrameEvidence, at_ns: int) -> dict:
        integer("decision_ns", at_ns)
        with self._lock:
            obsolete = evidence.epoch != self._epoch
            decision = {
                "token": token,
                "epoch": evidence.epoch,
                "current_epoch": self._epoch,
                "obsolete": obsolete,
                "published": not (self._filter and obsolete),
                "decision_ns": at_ns,
            }
            self._events.append(dict(decision))
            return decision


def accounting(
    *,
    submitted: int,
    received: int,
    native_drops: int,
    rejected: int,
    published: int,
    unpulled: int,
) -> dict[str, int]:
    values = dict(
        submitted=submitted,
        received=received,
        native_drops=native_drops,
        rejected=rejected,
        published=published,
        unpulled=unpulled,
    )
    for name, value in values.items():
        integer(name, value)
    if submitted != received + native_drops + unpulled:
        raise ValueError("native accounting does not conserve submissions")
    if received != rejected + published:
        raise ValueError("application accounting does not conserve receipts")
    return values
