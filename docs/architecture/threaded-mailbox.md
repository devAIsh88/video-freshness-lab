# Threaded mailbox and shutdown contract

Milestone 1.4 implements the PRD's thread-safe handoff and clean-shutdown learning
requirements using synthetic metadata. It does not implement the broader Stage 1
lab or validate real RTSP reconnection behavior. The deterministic simulator and
its single-threaded buffers remain unchanged.

## Ownership and admission

`LatestFrameMailbox` supports one producer, one consumer, and one lifecycle owner.
It retains at most one waiting `Frame`. The existing frozen, slotted frame model
contains only immutable integers: session ID, sequence, and production timestamp
in milliseconds. Retrieval returns the exact submitted object; there is no
mutable image payload or copy operation. Thread identities are not enforced, and
multi-producer fairness or multi-consumer ordering is outside this contract.

Accepted `(session_id, sequence)` pairs must strictly increase lexicographically,
including after retrieval. A new higher session may restart sequence numbering.
Duplicate/backwards identities raise `ValueError`; other object types raise
`TypeError`. This synthetic admission rule does not discover real stream epochs
or filter an already processing frame against an external session state.

`submit` replaces only the waiting frame and returns that displaced object, or
`None` if the slot was empty. A retrieved frame belongs to the consumer and cannot
be replaced. The mailbox lock is never held during consumer processing.

## Synchronization and close

One `threading.Condition` protects the pending slot, identity, counters, closed
flag, and waiting-consumer count. Submission, retrieval, close, and snapshots are
atomic under this lock. `get()` waits on the predicate `pending or closed`,
rechecking after notifications. Registering a wait and releasing the lock are
coordinated by the condition, preventing the ordinary check-then-wait lost-wakeup
race. Spurious notifications do not yield phantom frames.

| State | Submit | Get | Close |
| --- | --- | --- | --- |
| Open, empty | Accept | Wait or time out | Closed, empty; notify |
| Open, full | Replace waiting item | Transfer item | Closed, full; notify |
| Closed, full | Raise `MailboxClosed` | Transfer final item | No change; notify |
| Closed, empty | Raise `MailboxClosed` | Raise `MailboxClosed` | No change; notify |

Closure is permanent and idempotent. **Shutdown drains the final pending item.**
It neither discards that item nor retracts a frame already retrieved. A blocked
consumer is notified on closure and then drains or terminates. Post-close
submission always raises `MailboxClosed` before inspecting the input and never
changes counters. An empty open mailbox can intentionally wait indefinitely
with `get()`; normal shutdown must call `close()`.

`get(timeout_s=0)` polls; positive timeouts use seconds and raise `TimeoutError`
when still open/empty. Timeouts must be finite, nonnegative, and at most
`threading.TIMEOUT_MAX`. `wait_until_waiting(timeout_s)` provides a bounded
observation for owner/test coordination; it is not a reservation against a
concurrent wakeup. No busy-waiting loop is used.

Atomic snapshots satisfy:

```text
accepted = delivered + replaced + pending
pending is 0 or 1
```

`delivered` counts retrieval, not successful processing. `replaced` counts dropped
waiting items only. Invalid or closed submissions are not accepted or replaced.
The demo separately counts constructed source frames and closed-mailbox submission
rejections: during stop, one constructed frame may be rejected before acceptance.

## Demo lifecycle

`ThreadedDemo` owns two explicitly non-daemon workers. Its owner-facing lifecycle
is single-use: constructed → started → stopping → joined, or failed. Repeated
experiments create fresh objects. Owner methods are not designed for simultaneous
calls by multiple lifecycle owners.

- Normal mode acknowledges each retrieval with an `Event` before generating the
  next item. An acknowledgement means handoff, not processing completion.
- Slow mode holds the first retrieved frame on an event outside the mailbox lock
  while the producer submits the remaining items. Producer completion closes the
  mailbox and releases the consumer to drain the newest waiting frame.
- Idle mode leaves the producer waiting for stop and the consumer waiting on an
  empty mailbox. The CLI observes the registered wait before requesting shutdown.

The producer closes the mailbox in its `finally` path. Worker completion events
are set only when their worker exits. Owner `stop()` sets the stop event, closes
the mailbox, and releases both acknowledgement and consumer-hold events. This
wakes all built-in waits, including shutdown during an in-progress frame or a
producer acknowledgement. `shutdown()` then joins both workers using a common
positive timeout budget. Repeated stop/close/shutdown after successful startup
and completion is safe; restarting the same object is rejected.

Worker exceptions are recorded under a lock, stop the peer, and propagate as
`WorkerFailed` with role/type and original exception cause. Arbitrary exception
messages are excluded from the CLI summary. Partial thread-start failures also
request stop and join any launched worker before reporting failure. A failed
consumer can leave a closed pending frame inspectable/drainable by the owner;
this is not reported as a successful demo.

Optional processing callbacks run outside the lock and receive the stop event.
They must return or cooperate with it. Python cannot forcibly terminate an
arbitrary blocked callback. A bounded join reports `ShutdownTimeout` with the
workers observed alive and requests stop; it does not pretend those threads have
terminated. The owner must resolve the blocking callback and join again. The CLI
uses only cooperative built-in operations and attempts bounded cleanup even on
owner interruption.

## Time and evidence limits

The threaded demo stamps production with integer elapsed milliseconds from a
`monotonic_ns()` origin. These are process-relative observations, not UTC, virtual
time, source-camera timestamps, or a freshness guarantee. Actual stamp values
vary with scheduling; coordinated identities and counts are repeatable. Use the
unchanged virtual simulator for deterministic age/threshold experiments.

Tests use events, barriers, and condition predicates to establish ordering, with
timeouts as hang safeguards. They cover submit/close and get/close races, spurious
notifications, waiting wakeups, exception paths, pending drain, strict identities,
and repeated fresh lifecycles. A finite suite cannot establish freedom from all
races. No performance, OS-wide fairness, Windows portability, real image ownership,
or real transport/reconnection claim follows from this milestone.
