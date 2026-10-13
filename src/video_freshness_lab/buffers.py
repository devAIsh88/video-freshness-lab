"""Waiting-frame policies; neither buffer owns in-progress work."""

from collections import deque
from dataclasses import dataclass
from typing import Literal

from .model import Frame, integer

Overflow = Literal["drop_newest", "drop_oldest"]


@dataclass(frozen=True, slots=True)
class Admission:
    admitted: bool
    dropped: tuple[Frame, ...] = ()
    reason: str | None = None


class FIFO:
    def __init__(
        self, capacity: int | None = None, overflow: Overflow = "drop_newest"
    ) -> None:
        if capacity is not None:
            integer("capacity", capacity, 1)
        if overflow not in ("drop_newest", "drop_oldest"):
            raise ValueError("unknown overflow policy")
        self.capacity = capacity
        self.overflow = overflow
        self._waiting: deque[Frame] = deque()

    def __len__(self) -> int:
        return len(self._waiting)

    def push(self, frame: Frame) -> Admission:
        dropped: tuple[Frame, ...] = ()
        reason = None
        if self.capacity is not None and len(self) == self.capacity:
            reason = f"overflow_{self.overflow}"
            if self.overflow == "drop_newest":
                return Admission(False, (frame,), reason)
            dropped = (self._waiting.popleft(),)
        self._waiting.append(frame)
        return Admission(True, dropped, reason)

    def pop(self) -> Frame:
        return self._waiting.popleft()

    def clear(self) -> tuple[Frame, ...]:
        removed = tuple(self._waiting)
        self._waiting.clear()
        return removed


class LatestFrame:
    def __init__(self) -> None:
        self._waiting: deque[Frame] = deque()

    def __len__(self) -> int:
        return len(self._waiting)

    def push(self, frame: Frame) -> Admission:
        dropped = (self._waiting.pop(),) if self._waiting else ()
        self._waiting.append(frame)
        return Admission(True, dropped, "replaced" if dropped else None)

    def pop(self) -> Frame:
        return self._waiting.popleft()

    def clear(self) -> tuple[Frame, ...]:
        removed = tuple(self._waiting)
        self._waiting.clear()
        return removed
