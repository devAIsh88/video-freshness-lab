"""Single-consumer virtual-time experiment; no transport or image decoding."""

from dataclasses import asdict, dataclass
from statistics import fmean
from typing import Literal

from .buffers import FIFO, LatestFrame, Overflow
from .clock import VirtualClock
from .model import Frame, integer


@dataclass(frozen=True, slots=True)
class Config:
    duration_ms: int = 100
    producer_interval_ms: int = 10
    consumer_duration_ms: int = 10
    policy: Literal["fifo", "latest"] = "fifo"
    queue_capacity: int | None = None
    overflow: Overflow = "drop_newest"
    freshness_threshold_ms: int | None = 30

    def __post_init__(self) -> None:
        for name in ("duration_ms", "producer_interval_ms", "consumer_duration_ms"):
            integer(name, getattr(self, name), 1)
        if self.policy not in ("fifo", "latest"):
            raise ValueError("policy must be fifo or latest")
        if self.overflow not in ("drop_newest", "drop_oldest"):
            raise ValueError("unknown overflow policy")
        if self.queue_capacity is not None:
            integer("queue_capacity", self.queue_capacity, 1)
        if self.policy == "latest" and self.queue_capacity not in (None, 1):
            raise ValueError("latest-frame waiting capacity is always one")
        if self.freshness_threshold_ms is not None:
            integer("freshness_threshold_ms", self.freshness_threshold_ms)


@dataclass(frozen=True, slots=True)
class Event:
    at_ms: int
    kind: str
    session_id: int
    queue_depth: int
    frame: Frame | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class Drop:
    frame: Frame
    at_ms: int
    reason: str


@dataclass(frozen=True, slots=True)
class Processing:
    frame: Frame
    started_at_ms: int
    completed_at_ms: int
    age_at_start_ms: int
    age_at_completion_ms: int
    lag_at_start: int
    lag_at_completion: int


@dataclass(frozen=True, slots=True)
class Metrics:
    frames_produced: int
    frames_consumed: int
    frames_dropped: int
    frames_replaced: int
    max_queue_depth: int
    max_start_age_ms: int | None
    mean_start_age_ms: float | None
    max_completion_age_ms: int | None
    mean_completion_age_ms: float | None
    max_processing_lag: int | None
    start_freshness_violations: int
    result_freshness_violations: int
    finished_at_ms: int


@dataclass(frozen=True, slots=True)
class Result:
    config: Config
    metrics: Metrics
    frames: tuple[Frame, ...]
    processing: tuple[Processing, ...]
    drops: tuple[Drop, ...]
    events: tuple[Event, ...]

    def to_dict(self) -> dict:
        return {"schema_version": 1, "timestamp_units": "ms", **asdict(self)}


class Simulator:
    def __init__(self, config: Config, clock: VirtualClock | None = None) -> None:
        self.config = config
        self.clock = clock if clock is not None else VirtualClock()
        if self.clock.now_ms or self.clock.pending_count:
            raise ValueError("simulator requires a fresh virtual clock")
        self.buffer = (
            FIFO(config.queue_capacity, config.overflow)
            if config.policy == "fifo"
            else LatestFrame()
        )
        self.frames: list[Frame] = []
        self.processing: list[Processing] = []
        self.drops: list[Drop] = []
        self.events: list[Event] = []
        self._busy = False
        self._start_pending = False
        self._has_run = False

    def run(self) -> Result:
        if self._has_run:
            raise ValueError("a simulator can run only once")
        self._has_run = True
        self.clock.schedule(0, self._produce, priority=2)
        self.clock.run_until(self.config.duration_ms)
        self.clock.run()
        return Result(
            self.config,
            self._metrics(),
            tuple(self.frames),
            tuple(self.processing),
            tuple(self.drops),
            tuple(self.events),
        )

    def _event(
        self, kind: str, frame: Frame | None = None, reason: str | None = None
    ) -> None:
        self.events.append(
            Event(self.clock.now_ms, kind, 0, len(self.buffer), frame, reason)
        )

    def _drop(self, frame: Frame, reason: str) -> None:
        self.drops.append(Drop(frame, self.clock.now_ms, reason))
        self._event("frame_dropped", frame, reason)

    def _produce(self) -> None:
        frame = Frame(0, len(self.frames), self.clock.now_ms)
        self.frames.append(frame)
        self._event("frame_produced", frame)
        admission = self.buffer.push(frame)
        for dropped in admission.dropped:
            self._drop(dropped, admission.reason or "overflow")
        if admission.admitted:
            self._event("frame_queued", frame)
        self._request_start()
        next_ms = self.clock.now_ms + self.config.producer_interval_ms
        if next_ms < self.config.duration_ms:
            self.clock.schedule(next_ms, self._produce, priority=2)

    def _request_start(self) -> None:
        if not self._busy and not self._start_pending and len(self.buffer):
            self._start_pending = True
            self.clock.schedule(self.clock.now_ms, self._start, priority=3)

    def _head(self) -> int:
        return len(self.frames) - 1

    def _violation(self, age_ms: int) -> bool:
        limit = self.config.freshness_threshold_ms
        return limit is not None and age_ms > limit

    def _start(self) -> None:
        self._start_pending = False
        frame = self.buffer.pop()
        self._busy = True
        start_ms = self.clock.now_ms
        start_head = self._head()
        self._event("processing_started", frame)
        if self._violation(start_ms - frame.produced_at_ms):
            self._event("freshness_violation", frame, "processing_start")

        def complete() -> None:
            end_ms = self.clock.now_ms
            self.processing.append(
                Processing(
                    frame,
                    start_ms,
                    end_ms,
                    start_ms - frame.produced_at_ms,
                    end_ms - frame.produced_at_ms,
                    start_head - frame.sequence,
                    self._head() - frame.sequence,
                )
            )
            self._event("frame_consumed", frame)
            if self._violation(end_ms - frame.produced_at_ms):
                self._event("freshness_violation", frame, "result_emission")
            self._busy = False
            self._request_start()

        self.clock.schedule(
            start_ms + self.config.consumer_duration_ms, complete, priority=1
        )

    def _metrics(self) -> Metrics:
        start_ages = [p.age_at_start_ms for p in self.processing]
        end_ages = [p.age_at_completion_ms for p in self.processing]
        lags = [p.lag_at_completion for p in self.processing]
        return Metrics(
            frames_produced=len(self.frames),
            frames_consumed=len(self.processing),
            frames_dropped=len(self.drops),
            frames_replaced=sum(d.reason == "replaced" for d in self.drops),
            max_queue_depth=max((e.queue_depth for e in self.events), default=0),
            max_start_age_ms=max(start_ages, default=None),
            mean_start_age_ms=fmean(start_ages) if start_ages else None,
            max_completion_age_ms=max(end_ages, default=None),
            mean_completion_age_ms=fmean(end_ages) if end_ages else None,
            max_processing_lag=max(lags, default=None),
            start_freshness_violations=sum(self._violation(a) for a in start_ages),
            result_freshness_violations=sum(self._violation(a) for a in end_ages),
            finished_at_ms=self.clock.now_ms,
        )
