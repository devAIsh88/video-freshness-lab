# Threaded session boundaries

Milestone 1.5 extends the synthetic learning lab with the PRDs' final-output epoch
contract. The explicit owner task authorizes this narrow contract-model experiment;
it does not advance stamped-image, transport, external-audit, or product gates.
`threaded_sessions.SessionPipeline` reuses the immutable `Frame` model and the
unchanged [Milestone 1.4 mailbox](threaded-mailbox.md). It is separate from the
[virtual simulator](simulation.md), and introduces no runtime dependency.

## Ownership and epochs

One producer submits frames, one consumer holds at most one acquired frame, and
the application controller owns session changes. The pipeline stores the current
logical epoch behind a lock; only `transition()` advances it. Experiments may run
the controller script in the producer thread or the test-owner thread. Thread
identities are not enforced; this is not a multi-camera or multi-consumer service.

The initial epoch is zero. Each transition retires the old epoch, increments the
epoch by one, and resets the next sequence to zero. Epochs are never reused within
a pipeline. `produce(produced_at_ms)` creates and submits a frame under the same
lock, so stamping cannot interleave with a transition. Production timestamps are
caller-supplied nonnegative integer milliseconds in the experiment's clock domain;
the pipeline does not infer wall time, compare ages, or enforce an age budget.
The immutable frame keeps its original epoch throughout processing and reporting.

| Operation | Epoch effect | Waiting item | Output admission |
| --- | --- | --- | --- |
| Produce | Stamp current epoch | Accept or replace | Unchanged |
| Transition | Retire A, activate A+1 | Retain | Reject A at final completion |
| Source close | Keep epoch | Retain and drain | Current epoch still allowed |
| Application shutdown | Keep last epoch for diagnostics | Retain and drain | Suppress every subsequent completion |

Transitions do not close, clear, or reopen the mailbox. They are allowed after
source closure while work drains. Shutdown is permanent and idempotent, rejects
further transitions, and closes input. It records a shutdown event rather than
pretending a transport reconnect or another logical epoch occurred. This model
has no disconnected interval with an unknown/absent epoch.

Waiting frames survive a transition. A newer production may replace them under
the existing one-slot policy. If an old waiting frame survives, it is still
acquired and processed; rejection occurs at final output. This is a deliberate
small contract, not an optimization to avoid obsolete work at dequeue.

## Atomic output boundary

Processing runs outside all mailbox/session locks. It returns an integer synthetic
value. `complete(original_frame, value)` validates that this is the exact active
object, checks shutdown and current epoch, and records an immutable `Completion`
containing the `Result`, observed epoch, and outcome. Duplicate completion or a
copied/forged frame is rejected without changing counters.

The **append to the completion ledger under the epoch lock** is the linearization
point for both successful processing accounting and final delivery. For a
`published` outcome that record is the externally observable output of this
experiment; `snapshot().outputs` returns only those published results, under the
same lock. There is no arbitrary external callback or subsequent unlocked sink
presented as atomic publication.

Validation, append, and the corresponding ordered event all occur while the lock
excludes transitions and output readers. If A publishes first, it is a valid
historical output; a later transition does not retract it. If B activates first,
A's completion is obsolete and cannot enter `outputs`. An unordered race may
choose either ordering, but never validate A, activate B, then publish A. Checking
only when acquiring the frame cannot provide this contract.

Shutdown has priority over obsolescence for outcome accounting: a successful
completion after application shutdown is classified once as `shutdown`, even if
its epoch is also retired. It is neither published nor counted again as obsolete.
An already published result remains a historical output after shutdown.

## Lock ordering and lifecycle

The epoch lock protects current epoch, sequence, produced count, acquisition
reservation, active frame, failures count, completions, and ordered events. Calls
that inspect or mutate the mailbox acquire its condition only while holding the
epoch lock. The blocking `acquire()` is the exception: it reserves the single
consumer under the epoch lock, releases that lock, then waits on the mailbox.
After retrieval releases the mailbox lock, it registers the active frame under
the epoch lock. No code holds the mailbox lock while acquiring the epoch lock.
This avoids preventing a producer/closer from waking an empty consumer.

Snapshots count acquisition at the mailbox transfer point. A transfer briefly
awaiting active registration already counts as in progress; its `acquired` event
is recorded later. Events provide the total order of recorded application
operations, not every internal mailbox scheduling instruction. The exact transfer
versus transition order does not replace final-completion validation.

`run_producer(source, stop)` runs a finite/cooperative callback and closes input
on return. `consume(process, stop)` drains until closed/empty, calls processing
outside locks, and validates every successful completion. Both propagate original
exceptions to their thread owner, first disabling output admission, then setting
the shared stop event to wake cooperative callbacks. A processing exception is
recorded once as failed work, not successful processing or session rejection.
Failed consumers can leave a pending frame for explicit owner drainage; it is
never silently lost or reported as successful cleanup of all work.

The thread owner must call `shutdown()` **before** setting the shared stop event
when suppressing shutdown outputs, then perform bounded joins. The stop event
alone does not invalidate sessions or disable output admission. Tests implement
this ordering in a small test-only owner that launches explicit non-daemon
threads, aggregates role/exception failures using the existing `WorkerFailed`
type, and joins with one common deadline. It reports `ShutdownTimeout` instead
of concealing a live worker. All event/barrier waits have hang-safeguard budgets.

The pipeline itself creates no background thread and does not own thread start,
restart, join, or stop-event lifetime. A fresh pipeline and worker pair are used
for each lifecycle test. Callbacks must return or honor stop; Python cannot force
an uncooperative callback to terminate. No sleeps or busy-wait loops are used.

## Accounting

Immutable snapshots separate these quantities:

| Field | Definition |
| --- | --- |
| `produced` | Frames constructed and successfully submitted by `produce` |
| `mailbox.accepted` | Accepted submissions; equal to produced in this controlled API |
| `mailbox.replaced` | Accepted waiting frames displaced by newer submissions |
| `mailbox.pending` | Waiting frames, zero or one |
| `acquired` | Transfers from mailbox into consumer ownership |
| `processed` | Successful integer-result completions, regardless of admission |
| `processing_failed` | Acquired frames whose processing raised or returned invalid data |
| `in_progress` | Acquired work not yet completed or failed |
| `rejected_obsolete` | Successful completions suppressed for a retired epoch |
| `published` | Successful completions admitted to the observable output ledger |
| `discarded_shutdown` | Successful completions suppressed after application shutdown |

```text
produced = mailbox.accepted
mailbox.accepted = mailbox.replaced + mailbox.pending + acquired
acquired = processed + processing_failed + in_progress
processed = published + rejected_obsolete + discarded_shutdown
```

Shutdown retains pending frames and permits their processing; the last field
counts discarded **results**, not silently removed mailbox items. Invalid
production input and post-close attempts raise before constructing an admitted
frame and do not count as produced. Failed production callbacks can therefore
leave previously produced work, but create no invented failed-frame count.
Consumers must use this API, not bypass its private mailbox or mutate its private
lists. Each frame has one final outcome; replacement, failed processing, and
successful completion categories do not double-count one admitted frame.

## Relationship and limits

The virtual simulator's filtered mode checks at dequeue and completion. This
threaded experiment instead retains and processes all surviving queued evidence,
checking at the final in-memory output boundary only. It demonstrates the critical
in-progress boundary without duplicating virtual-clock fault scheduling or age
metrics. Current epoch is a provenance property, independent of evidence age.

Uncoordinated races retain scheduling nondeterminism; the contract defines legal
linearizations rather than a preferred winning thread. Finite repetitions cannot
prove complete race freedom or a general integration flake rate. Output/event
history grows with workload and is intended for small synthetic experiments.
There is no real transport, camera identity discovery, image ownership contract,
external sink transaction, throughput guarantee, or validation of RTSP reconnects.
