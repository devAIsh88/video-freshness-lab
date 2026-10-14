"""Coordinated real-thread learning demo, separate from the virtual simulator."""

import argparse
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from threading import Event, Lock, Thread
from time import monotonic, monotonic_ns
from typing import Literal

from .model import Frame, integer
from .threaded_mailbox import LatestFrameMailbox, MailboxClosed, MailboxState, seconds


@dataclass(frozen=True, slots=True)
class DemoConfig:
    mode: Literal["normal", "slow", "idle"] = "normal"
    items: int = 10

    def __post_init__(self) -> None:
        if self.mode not in ("normal", "slow", "idle"):
            raise ValueError("mode must be normal, slow, or idle")
        integer("items", self.items)
        if self.mode == "idle" and self.items != 0:
            raise ValueError("idle mode requires zero items")


@dataclass(frozen=True, slots=True)
class DemoResult:
    config: DemoConfig
    produced: int
    rejected_submissions: int
    mailbox: MailboxState
    delivered_frames: tuple[Frame, ...]
    producer_finished: bool
    consumer_finished: bool
    threads_terminated: bool


@dataclass(frozen=True, slots=True)
class WorkerFailure:
    role: str
    error: BaseException


class WorkerFailed(RuntimeError):
    def __init__(self, failures: tuple[WorkerFailure, ...]) -> None:
        self.failures = failures
        # Do not put arbitrary worker exception messages into summary output.
        super().__init__(
            "worker failure: "
            + ", ".join(f"{f.role} ({type(f.error).__name__})" for f in failures)
        )


class ShutdownTimeout(RuntimeError):
    def __init__(self, alive_workers: tuple[str, ...]) -> None:
        self.alive_workers = alive_workers
        super().__init__(
            "workers did not terminate within join budget: " + ", ".join(alive_workers)
        )


class ThreadedDemo:
    """One owner controls a fresh pair of non-daemon, single-use workers.

    Optional processing callbacks run outside the mailbox lock. They must return
    or honor the supplied stop event. Arbitrary blocked Python callbacks cannot
    be killed; join reports them rather than hiding them behind daemon threads.
    """

    def __init__(
        self,
        config: DemoConfig | None = None,
        process: Callable[[Frame, Event], None] | None = None,
    ) -> None:
        if process is not None and not callable(process):
            raise ValueError("process must be callable")
        self.config = config if config is not None else DemoConfig()
        self.mailbox = LatestFrameMailbox()
        self._process = process
        self._stop = Event()
        self._taken = Event()
        self._release_consumer = Event()
        self.producer_finished = Event()
        self.consumer_finished = Event()
        self._delivered: list[Frame] = []
        self._failures: list[WorkerFailure] = []
        self._failure_lock = Lock()
        self._started = False
        self._origin_ns = 0
        self._produced = 0
        self._rejected_submissions = 0
        self._producer = Thread(
            target=self._worker,
            args=("producer", self._produce),
            name="freshness-producer",
            daemon=False,
        )
        self._consumer = Thread(
            target=self._worker,
            args=("consumer", self._consume),
            name="freshness-consumer",
            daemon=False,
        )

    @property
    def alive_workers(self) -> tuple[str, ...]:
        return tuple(t.name for t in (self._producer, self._consumer) if t.is_alive())

    def start(self) -> None:
        if self._started or self._stop.is_set():
            raise ValueError("demo is single-use and cannot start after stopping")
        self._started = True
        self._origin_ns = monotonic_ns()
        try:
            self._consumer.start()
            self._producer.start()
        except BaseException as error:
            with self._failure_lock:
                self._failures.append(WorkerFailure("startup", error))
            self.stop()
            self._join_workers(5.0)
            if self.alive_workers:
                raise ShutdownTimeout(self.alive_workers) from None
            raise

    def stop(self) -> None:
        self._stop.set()
        self.mailbox.close()
        # Wake both the producer acknowledgement and in-progress demo pause.
        self._taken.set()
        self._release_consumer.set()

    def _join_workers(self, timeout_s: float) -> None:
        deadline = monotonic() + timeout_s
        for thread in (self._producer, self._consumer):
            if thread.ident is not None:
                thread.join(max(0.0, deadline - monotonic()))

    def join(self, timeout_s: float = 5.0) -> DemoResult:
        seconds("timeout_s", timeout_s, allow_zero=False)
        if not self._started:
            raise ValueError("start the demo before joining")
        self._join_workers(timeout_s)
        alive = self.alive_workers
        if alive:
            self.stop()
            raise ShutdownTimeout(alive)
        if self._failures:
            failures = tuple(self._failures)
            raise WorkerFailed(failures) from failures[0].error
        return DemoResult(
            self.config,
            self._produced,
            self._rejected_submissions,
            self.mailbox.snapshot(),
            tuple(self._delivered),
            self.producer_finished.is_set(),
            self.consumer_finished.is_set(),
            True,
        )

    def shutdown(self, timeout_s: float = 5.0) -> DemoResult:
        seconds("timeout_s", timeout_s, allow_zero=False)
        self.stop()
        return self.join(timeout_s)

    def _worker(self, role: str, run: Callable[[], None]) -> None:
        try:
            run()
        except BaseException as error:
            with self._failure_lock:
                self._failures.append(WorkerFailure(role, error))
            self.stop()
        finally:
            if role == "producer":
                self.mailbox.close()
                self._release_consumer.set()
                self.producer_finished.set()
            else:
                self.consumer_finished.set()

    def _produce(self) -> None:
        if self.config.mode == "idle":
            self._stop.wait()
            return
        for sequence in range(self.config.items):
            if self._stop.is_set():
                break
            elapsed_ms = (monotonic_ns() - self._origin_ns) // 1_000_000
            frame = Frame(0, sequence, elapsed_ms)
            self._produced += 1
            self._taken.clear()
            try:
                self.mailbox.submit(frame)
            except MailboxClosed:
                self._rejected_submissions += 1
                return
            if self.config.mode == "normal" or sequence == 0:
                self._taken.wait()
                if self._stop.is_set():
                    break

    def _consume(self) -> None:
        while True:
            try:
                frame = self.mailbox.get()
            except MailboxClosed:
                return
            self._delivered.append(frame)
            self._taken.set()
            if self.config.mode == "slow" and frame.sequence == 0:
                self._release_consumer.wait()
            if self._process is not None:
                self._process(frame, self._stop)


def run_demo(config: DemoConfig, timeout_s: float = 5.0) -> DemoResult:
    seconds("timeout_s", timeout_s, allow_zero=False)
    demo = ThreadedDemo(config)
    demo.start()
    try:
        if config.mode == "idle":
            if not demo.mailbox.wait_until_waiting(timeout_s):
                raise ShutdownTimeout(demo.alive_workers)
            return demo.shutdown(timeout_s)
        return demo.join(timeout_s)
    finally:
        # CLI workers are cooperative; this also cleans up owner interruption.
        demo.stop()
        demo._join_workers(timeout_s)
        if demo.alive_workers:
            raise ShutdownTimeout(demo.alive_workers)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Thread-safe synthetic frame mailbox demo"
    )
    parser.add_argument("--mode", choices=["normal", "slow", "idle"], default="normal")
    parser.add_argument("--items", type=int)
    parser.add_argument("--timeout-s", type=float, default=5.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        config = DemoConfig(
            args.mode,
            args.items
            if args.items is not None
            else (0 if args.mode == "idle" else 10),
        )
        seconds("timeout_s", args.timeout_s, allow_zero=False)
    except ValueError as error:
        parser.error(str(error))
    try:
        result = run_demo(config, args.timeout_s)
    except (WorkerFailed, ShutdownTimeout) as error:
        print(str(error))
        return 1
    if args.json:
        print(json.dumps(asdict(result), sort_keys=True))
    else:
        state = result.mailbox
        print(
            f"mode={config.mode} produced={result.produced} accepted={state.accepted} "
            f"delivered={state.delivered} replaced={state.replaced} "
            f"rejected_submissions={result.rejected_submissions}"
        )
        print(
            "delivered IDs: "
            + ", ".join(f.frame_id for f in result.delivered_frames[:16])
            + (
                f" ... ({len(result.delivered_frames)} total)"
                if len(result.delivered_frames) > 16
                else ""
            )
        )
        print(
            f"producer_finished={result.producer_finished} consumer_finished={result.consumer_finished} threads_terminated={result.threads_terminated}"
        )
        print(
            f"mailbox: closed={state.closed} pending={state.pending} waiting_consumers={state.waiting_consumers}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
