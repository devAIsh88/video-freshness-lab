"""Finite discrete-event clock: timestamp, priority, then insertion order."""

from collections.abc import Callable
from heapq import heappop, heappush

from .model import integer


class VirtualClock:
    def __init__(self) -> None:
        self._now_ms = 0
        self._serial = 0
        self._pending: list[tuple[int, int, int, Callable[[], None]]] = []
        self._running = False

    @property
    def now_ms(self) -> int:
        return self._now_ms

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def schedule(
        self, at_ms: int, callback: Callable[[], None], *, priority: int = 0
    ) -> None:
        integer("at_ms", at_ms, self.now_ms)
        integer("priority", priority)
        if not callable(callback):
            raise ValueError("callback must be callable")
        heappush(self._pending, (at_ms, priority, self._serial, callback))
        self._serial += 1

    def run_until(self, until_ms: int) -> None:
        integer("until_ms", until_ms, self.now_ms)
        self._run(until_ms)
        self._now_ms = until_ms

    def run(self) -> None:
        """Drain the agenda; callers must schedule a finite workload."""
        self._run(None)

    def _run(self, until_ms: int | None) -> None:
        if self._running:
            raise ValueError("clock execution cannot be nested")
        self._running = True
        try:
            while self._pending and (
                until_ms is None or self._pending[0][0] <= until_ms
            ):
                at_ms, _, _, callback = heappop(self._pending)
                self._now_ms = at_ms
                callback()
        finally:
            self._running = False
