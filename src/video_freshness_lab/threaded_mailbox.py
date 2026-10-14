"""Single-producer/single-consumer latest-frame handoff with drain-on-close."""

from dataclasses import dataclass
from threading import TIMEOUT_MAX, Condition

from .model import Frame


def seconds(name: str, value: float, *, allow_zero: bool = True) -> None:
    if (
        type(value) not in (int, float)
        or not 0 <= value <= TIMEOUT_MAX
        or (not allow_zero and value == 0)
    ):
        raise ValueError(
            f"{name} must be finite {'nonnegative' if allow_zero else 'positive'} seconds <= threading.TIMEOUT_MAX"
        )


class MailboxClosed(RuntimeError):
    """The mailbox cannot accept more frames, or is closed and drained."""


@dataclass(frozen=True, slots=True)
class MailboxState:
    accepted: int
    delivered: int
    replaced: int
    pending: int
    closed: bool
    waiting_consumers: int


class LatestFrameMailbox:
    """One waiting slot; retrieval transfers the original immutable Frame.

    Accepted (session_id, sequence) pairs must strictly increase. Closure is
    permanent and idempotent. A closed mailbox drains its pending frame once;
    then get raises MailboxClosed. Rejected submissions do not change counters.
    """

    def __init__(self) -> None:
        self._condition = Condition()
        self._pending: Frame | None = None
        self._last_identity: tuple[int, int] | None = None
        self._closed = False
        self._accepted = self._delivered = self._replaced = self._waiting = 0

    def submit(self, frame: Frame) -> Frame | None:
        """Accept immediately and return any replaced waiting frame."""
        with self._condition:
            if self._closed:
                raise MailboxClosed("submission after close")
            if not isinstance(frame, Frame):
                raise TypeError("mailbox requires immutable Frame metadata")
            identity = (frame.session_id, frame.sequence)
            if self._last_identity is not None and identity <= self._last_identity:
                raise ValueError("accepted frame identities must strictly increase")
            previous = self._pending
            if previous is not None:
                self._replaced += 1
            self._pending = frame
            self._last_identity = identity
            self._accepted += 1
            self._condition.notify_all()
            return previous

    def get(self, timeout_s: float | None = None) -> Frame:
        """Block while open/empty; zero timeout polls once without waiting."""
        if timeout_s is not None:
            seconds("timeout_s", timeout_s)
        with self._condition:
            if self._pending is None and not self._closed:
                self._waiting += 1
                self._condition.notify_all()
                try:
                    ready = self._condition.wait_for(
                        lambda: self._pending is not None or self._closed, timeout_s
                    )
                    if not ready:
                        raise TimeoutError("mailbox remained empty")
                finally:
                    self._waiting -= 1
                    self._condition.notify_all()
            if self._pending is None:
                raise MailboxClosed("mailbox is closed and drained")
            frame = self._pending
            self._pending = None
            self._delivered += 1
            return frame

    def close(self) -> None:
        """Stop acceptance, retain the final waiting frame, and wake consumers."""
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    def snapshot(self) -> MailboxState:
        with self._condition:
            return MailboxState(
                self._accepted,
                self._delivered,
                self._replaced,
                int(self._pending is not None),
                self._closed,
                self._waiting,
            )

    def wait_until_waiting(self, timeout_s: float) -> bool:
        """Bounded observation for coordinating the owner with an empty consumer.

        True records an observed wait, not a reservation: concurrent submission
        may wake the consumer immediately after this method returns.
        """
        seconds("timeout_s", timeout_s)
        with self._condition:
            self._condition.wait_for(
                lambda: self._waiting > 0 or self._closed, timeout_s
            )
            return self._waiting > 0
