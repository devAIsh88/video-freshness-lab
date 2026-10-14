"""Synthetic SPSC provenance checks at an atomic, in-memory output boundary."""

from collections.abc import Callable
from dataclasses import dataclass
from threading import Event, Lock
from typing import Literal

from .model import Frame
from .threaded_mailbox import LatestFrameMailbox, MailboxClosed, MailboxState


@dataclass(frozen=True, slots=True)
class Result:
    frame: Frame
    value: int


@dataclass(frozen=True, slots=True)
class Completion:
    result: Result
    current_epoch: int
    outcome: Literal["published", "obsolete", "shutdown"]


@dataclass(frozen=True, slots=True)
class BoundaryEvent:
    order: int
    kind: str
    epoch: int
    frame: Frame | None = None


@dataclass(frozen=True, slots=True)
class SessionState:
    epoch: int
    mailbox: MailboxState
    shutdown: bool
    produced: int
    acquired: int
    processed: int
    processing_failed: int
    in_progress: int
    rejected_obsolete: int
    published: int
    discarded_shutdown: int
    outputs: tuple[Result, ...]
    completions: tuple[Completion, ...]
    events: tuple[BoundaryEvent, ...]


class SessionPipeline:
    """One producer, one consumer, and a controller of logical epoch changes.

    Waiting items survive transitions. Every successful processing attempt is
    checked at final delivery; validation and output insertion share the epoch
    lock. The output ledger is the external delivery boundary for this demo.
    Mailbox closure stops production only. Application shutdown also disables
    publication, while retaining mailbox drain-on-close.
    """

    def __init__(self) -> None:
        self._mailbox = LatestFrameMailbox()
        self._lock = Lock()
        self._epoch = self._sequence = self._produced = self._failed = 0
        self._shutdown = self._acquiring = False
        self._active: Frame | None = None
        self._completions: list[Completion] = []
        self._events: list[BoundaryEvent] = []
        self._record("session_started")

    def _record(self, kind: str, frame: Frame | None = None) -> None:
        # Caller holds the epoch lock (except single-threaded construction).
        self._events.append(BoundaryEvent(len(self._events), kind, self._epoch, frame))

    def transition(self) -> int:
        """Retire the current epoch and activate the next; never reopen input."""
        with self._lock:
            if self._shutdown:
                raise RuntimeError("session transition after application shutdown")
            self._record("session_ended")
            self._epoch += 1
            self._sequence = 0
            self._record("session_started")
            return self._epoch

    def produce(self, produced_at_ms: int = 0) -> Frame:
        """Stamp and submit under the epoch lock; timestamps are caller-supplied ms."""
        with self._lock:
            if self._mailbox.snapshot().closed:
                raise MailboxClosed("production after source closure")
            frame = Frame(self._epoch, self._sequence, produced_at_ms)
            replaced = self._mailbox.submit(frame)
            self._sequence += 1
            self._produced += 1
            self._record("produced", frame)
            if replaced is not None:
                self._record("replaced", replaced)
            return frame

    def acquire(self, timeout_s: float | None = None) -> Frame:
        """Transfer one item; block without holding the epoch lock."""
        with self._lock:
            if self._active is not None or self._acquiring:
                raise RuntimeError("single consumer already has an outstanding item")
            self._acquiring = True
        try:
            frame = self._mailbox.get(timeout_s)
        except BaseException:
            with self._lock:
                self._acquiring = False
            raise
        with self._lock:
            self._acquiring = False
            self._active = frame
            self._record("acquired", frame)
            return frame

    def _require_active(self, frame: Frame) -> None:
        if self._active is None or self._active is not frame:
            raise ValueError("completion must reference the original active frame once")

    def complete(self, frame: Frame, value: int) -> Completion:
        """Record successful processing and atomically decide final delivery."""
        if type(value) is not int:
            raise TypeError("synthetic processing must return an integer result")
        with self._lock:
            self._require_active(frame)
            outcome: Literal["published", "obsolete", "shutdown"]
            if self._shutdown:
                outcome = "shutdown"
            elif frame.session_id != self._epoch:
                outcome = "obsolete"
            else:
                outcome = "published"
            completion = Completion(Result(frame, value), self._epoch, outcome)
            # This append is the delivery linearization point. Neither an epoch
            # change nor an output reader can interleave with validation above.
            self._completions.append(completion)
            self._active = None
            self._record(outcome, frame)
            return completion

    def fail_processing(self, frame: Frame) -> None:
        with self._lock:
            self._require_active(frame)
            self._active = None
            self._failed += 1
            self._record("processing_failed", frame)

    def close(self) -> None:
        """End source input; keep current epoch and output admission unchanged."""
        with self._lock:
            if not self._mailbox.snapshot().closed:
                self._mailbox.close()
                self._record("source_closed")

    def shutdown(self) -> None:
        """Disable output admission and close input, retaining pending drainage."""
        with self._lock:
            if not self._shutdown:
                self._shutdown = True
                self._mailbox.close()
                self._record("shutdown")

    def wait_until_waiting(self, timeout_s: float) -> bool:
        return self._mailbox.wait_until_waiting(timeout_s)

    def snapshot(self) -> SessionState:
        with self._lock:
            mailbox = self._mailbox.snapshot()
            completions = tuple(self._completions)
            outputs = tuple(c.result for c in completions if c.outcome == "published")
            return SessionState(
                self._epoch,
                mailbox,
                self._shutdown,
                self._produced,
                mailbox.delivered,
                len(completions),
                self._failed,
                mailbox.delivered - len(completions) - self._failed,
                sum(c.outcome == "obsolete" for c in completions),
                len(outputs),
                sum(c.outcome == "shutdown" for c in completions),
                outputs,
                completions,
                tuple(self._events),
            )

    def run_producer(
        self, source: Callable[["SessionPipeline", Event], None], stop: Event
    ) -> None:
        """Run a finite/cooperative source; propagate failures to its thread owner."""
        try:
            source(self, stop)
        except BaseException:
            self.shutdown()
            stop.set()
            raise
        finally:
            self.close()

    def consume(self, process: Callable[[Frame, Event], int], stop: Event) -> None:
        """Drain, process outside locks, then validate every output at completion.

        Shutdown is cooperative: callbacks must return or honor stop. Even items
        drained after shutdown are processed and counted, but never published.
        """
        try:
            while True:
                try:
                    frame = self.acquire()
                except MailboxClosed:
                    return
                try:
                    value = process(frame, stop)
                    self.complete(frame, value)
                except BaseException:
                    self.fail_processing(frame)
                    raise
        except BaseException:
            self.shutdown()
            stop.set()
            raise
