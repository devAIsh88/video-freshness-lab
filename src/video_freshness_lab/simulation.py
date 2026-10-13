"""Single-consumer virtual-time experiment; no transport or image decoding."""

from dataclasses import asdict, dataclass
from statistics import fmean
from typing import Literal

from .buffers import FIFO, LatestFrame, Overflow
from .clock import VirtualClock
from .model import Control, Frame, integer


def _validate_controls(controls: tuple[Control, ...], duration_ms: int) -> None:
    if not isinstance(controls, tuple) or not all(
        isinstance(c, Control) for c in controls
    ):
        raise ValueError("controls must be an immutable tuple of Control objects")
    connected, frozen, previous_ms = True, False, -1
    for control in controls:
        if control.at_ms < previous_ms or control.at_ms >= duration_ms:
            raise ValueError(
                "controls must be ordered and strictly before the source horizon"
            )
        previous_ms = control.at_ms
        if control.kind == "disconnect":
            if not connected:
                raise ValueError("disconnect requires a connected source")
            connected, frozen = False, False
        elif control.kind == "reconnect":
            if connected:
                raise ValueError("reconnect requires a disconnected source")
            connected = True
        elif control.kind == "freeze":
            if not connected or frozen:
                raise ValueError("freeze requires a connected, unfrozen source")
            frozen = True
        elif control.kind == "unfreeze":
            if not connected or not frozen:
                raise ValueError("unfreeze requires a connected, frozen source")
            frozen = False


@dataclass(frozen=True, slots=True)
class Config:
    duration_ms: int = 100
    producer_interval_ms: int = 10
    consumer_duration_ms: int = 10
    policy: Literal["fifo", "latest"] = "fifo"
    queue_capacity: int | None = None
    overflow: Overflow = "drop_newest"
    freshness_threshold_ms: int | None = 30
    controls: tuple[Control, ...] = ()
    session_filter: bool = False
    queue_on_disconnect: Literal["retain", "invalidate"] = "retain"
    no_progress_timeout_ms: int | None = None

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
        if type(self.session_filter) is not bool:
            raise ValueError("session_filter must be boolean")
        if self.queue_on_disconnect not in ("retain", "invalidate"):
            raise ValueError("queue_on_disconnect must be retain or invalidate")
        if self.no_progress_timeout_ms is not None:
            integer("no_progress_timeout_ms", self.no_progress_timeout_ms, 1)
        _validate_controls(self.controls, self.duration_ms)


@dataclass(frozen=True, slots=True)
class Event:
    at_ms: int
    kind: str
    session_id: int | None
    queue_depth: int
    frame: Frame | None = None
    reason: str | None = None
    since_ms: int | None = None


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
    emitted: bool = True
    obsolete_at_completion: bool = False


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
    frames_processed: int
    frames_rejected: int
    frames_invalidated: int
    obsolete_session_frames_detected: int
    obsolete_session_outputs: int
    no_progress_intervals: int


@dataclass(frozen=True, slots=True)
class Result:
    config: Config
    metrics: Metrics
    frames: tuple[Frame, ...]
    processing: tuple[Processing, ...]
    drops: tuple[Drop, ...]
    events: tuple[Event, ...]

    def to_dict(self) -> dict:
        return {"schema_version": 2, "timestamp_units": "ms", **asdict(self)}


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
        self._active_session: int | None = None
        self._next_session = 0
        self._heads: dict[int, int] = {}
        self._frozen = False
        self._consumer_duration_ms = config.consumer_duration_ms
        self._old_detected: set[str] = set()
        self._progress_generation = 0

    def run(self) -> Result:
        if self._has_run:
            raise ValueError("a simulator can run only once")
        self._has_run = True
        self._start_session()
        for control in self.config.controls:
            self.clock.schedule(
                control.at_ms, lambda c=control: self._control(c), priority=0
            )
        self.clock.schedule(0, self._produce, priority=2)
        self.clock.run_until(self.config.duration_ms)
        self.clock.run()
        if self._active_session is not None:
            self._event("session_ended", reason="simulation_complete")
            self._active_session = None
        return Result(
            self.config,
            self._metrics(),
            tuple(self.frames),
            tuple(self.processing),
            tuple(self.drops),
            tuple(self.events),
        )

    def _event(
        self,
        kind: str,
        frame: Frame | None = None,
        reason: str | None = None,
        since_ms: int | None = None,
    ) -> None:
        self.events.append(
            Event(
                self.clock.now_ms,
                kind,
                self._active_session,
                len(self.buffer),
                frame,
                reason,
                since_ms,
            )
        )

    def _start_session(self) -> None:
        self._active_session = self._next_session
        self._next_session += 1
        self._heads[self._active_session] = -1
        self._event("session_started")
        self._arm_watchdog()

    def _arm_watchdog(self) -> None:
        self._progress_generation += 1
        timeout = self.config.no_progress_timeout_ms
        if timeout is None:
            return
        generation = self._progress_generation
        since_ms = self.clock.now_ms
        deadline_ms = since_ms + timeout
        if deadline_ms >= self.config.duration_ms:
            return

        def check_progress() -> None:
            if generation == self._progress_generation:
                self._event("no_progress", reason="source_identity", since_ms=since_ms)

        self.clock.schedule(deadline_ms, check_progress, priority=4)

    def _control(self, control: Control) -> None:
        if control.kind == "disconnect":
            self._event("session_ended", reason="disconnect")
            self._active_session = None
            self._frozen = False
            self._event("stream_interrupted", reason="disconnect")
            if self.config.queue_on_disconnect == "invalidate":
                for frame in self.buffer.clear():
                    self._drop(frame, "invalidated_session")
        elif control.kind == "reconnect":
            self._start_session()
            self._event("stream_recovered", reason="reconnect")
        elif control.kind in ("freeze", "unfreeze"):
            self._frozen = control.kind == "freeze"
            self._event(
                "stream_interrupted" if self._frozen else "stream_recovered",
                reason=control.kind,
            )
        else:
            self._consumer_duration_ms = control.consumer_duration_ms
            self._event(
                "consumer_duration_changed",
                reason=f"duration_ms={control.consumer_duration_ms}",
            )

    def _obsolete(self, frame: Frame) -> bool:
        return frame.session_id != self._active_session

    def _detect_old(self, frame: Frame, phase: str) -> None:
        self._old_detected.add(frame.frame_id)
        self._event("old_session_frame_detected", frame, phase)

    def _drop(self, frame: Frame, reason: str) -> None:
        self.drops.append(Drop(frame, self.clock.now_ms, reason))
        self._event("frame_dropped", frame, reason)

    def _produce(self) -> None:
        if self._active_session is not None and not self._frozen:
            sequence = self._heads[self._active_session] + 1
            frame = Frame(self._active_session, sequence, self.clock.now_ms)
            self._heads[self._active_session] = sequence
            self.frames.append(frame)
            self._arm_watchdog()
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

    def _head(self, frame: Frame) -> int:
        # Sequence lag is only comparable within the evidence's own epoch.
        return self._heads[frame.session_id]

    def _violation(self, age_ms: int) -> bool:
        limit = self.config.freshness_threshold_ms
        return limit is not None and age_ms > limit

    def _start(self) -> None:
        self._start_pending = False
        if not len(self.buffer):
            return
        frame = self.buffer.pop()
        while self._obsolete(frame):
            self._detect_old(frame, "processing_start")
            if not self.config.session_filter:
                break
            self._drop(frame, "obsolete_session")
            if not len(self.buffer):
                return
            frame = self.buffer.pop()
        self._busy = True
        start_ms = self.clock.now_ms
        start_head = self._head(frame)
        self._event("processing_started", frame)
        if self._violation(start_ms - frame.produced_at_ms):
            self._event("freshness_violation", frame, "processing_start")

        def complete() -> None:
            end_ms = self.clock.now_ms
            obsolete = self._obsolete(frame)
            if obsolete:
                self._detect_old(frame, "result_emission")
            emitted = not (obsolete and self.config.session_filter)
            self.processing.append(
                Processing(
                    frame,
                    start_ms,
                    end_ms,
                    start_ms - frame.produced_at_ms,
                    end_ms - frame.produced_at_ms,
                    start_head - frame.sequence,
                    self._head(frame) - frame.sequence,
                    emitted,
                    obsolete,
                )
            )
            if emitted:
                self._event("frame_consumed", frame)
            else:
                self._drop(frame, "obsolete_session")
            if emitted and self._violation(end_ms - frame.produced_at_ms):
                self._event("freshness_violation", frame, "result_emission")
            self._busy = False
            self._request_start()

        self.clock.schedule(start_ms + self._consumer_duration_ms, complete, priority=1)

    def _metrics(self) -> Metrics:
        start_ages = [p.age_at_start_ms for p in self.processing]
        emitted = [p for p in self.processing if p.emitted]
        end_ages = [p.age_at_completion_ms for p in emitted]
        lags = [p.lag_at_completion for p in emitted]
        return Metrics(
            frames_produced=len(self.frames),
            frames_consumed=len(emitted),
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
            frames_processed=len(self.processing),
            frames_rejected=sum(d.reason == "obsolete_session" for d in self.drops),
            frames_invalidated=sum(
                d.reason == "invalidated_session" for d in self.drops
            ),
            obsolete_session_frames_detected=len(self._old_detected),
            obsolete_session_outputs=sum(p.obsolete_at_completion for p in emitted),
            no_progress_intervals=sum(e.kind == "no_progress" for e in self.events),
        )
