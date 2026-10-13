# Deterministic simulation architecture

Milestone 1.2 implements numbered evidence, not pixels or RTSP. The master task
explicitly authorizes in-process milestones beyond the historical foundation
scope. PRD Stage 1 buffering/metrics concepts come first; constant session labels
are provenance metadata here, not recovery claims. Later Milestone 1.3 adds
synthetic epoch contracts after 1.2 acceptance. These milestones do not claim to
complete the broader PRD threaded learning demo, stamped images, transport faults,
external audit, or productization gates. The original PRDs remain authoritative
for those gates and remain untracked.

## Components and clock

- `model.Frame`: frozen integer `session_id`, per-session `sequence`,
  `produced_at_ms`, and deterministic `epoch-N/frame-M` ID. In 1.2 the only epoch
  is zero. There is no image content, decoder, random seed, or source clock drift.
- `clock.VirtualClock`: injectable monotonic integer milliseconds beginning at
  zero. Agenda order is `(timestamp, priority, insertion serial)`. No threads,
  sleeps, sockets, or wall clock. Generic callback users must schedule finite
  workloads and avoid callback priority inversions; the simulator controls this.
- `buffers.FIFO`: unbounded by default; optional positive waiting capacity with
  explicit drop-newest or drop-oldest overflow. Capacity excludes active work.
- `buffers.LatestFrame`: exactly one waiting slot. New arrivals replace the
  waiting item. Already started processing always finishes; it is not cancelled.
- `simulation.Simulator`: finite producer schedule and one non-preemptive consumer,
  with immutable evidence/result snapshots and structured events.
- `experiments` and the module CLI: named reproducible workload configurations,
  concise summaries or full JSON evidence. No new runtime dependencies.

At simultaneous timestamps completion has priority 1, production 2, and processing
start 3. Completion observes the source head before a same-time production;
the next processing start sees that production. Equal priorities use insertion
order. Clock targets are inclusive; production is strictly before the configured
source horizon: `0, interval, ... < duration_ms`. At the horizon the producer stops,
then all admitted waiting and active work drains. The final clock is at least the
source horizon and may extend past it. Positive producer and consumer durations
and a finite source horizon bound the engine's event count. A clock and simulator
begin at zero with an empty agenda; each simulator may run only once.

## Metric definitions

All timestamps/ages are integer milliseconds from the same virtual origin; lag
is a count of source sequences, not a time conversion or claimed frame rate.

| Field | Definition |
| --- | --- |
| `frames_produced` | Number of unique generated numbered evidence items |
| `frames_consumed` | Completed consumer outputs; a dequeue alone is not counted |
| `frames_dropped` | Unique discarded waiting/new arrivals, recorded with reason |
| `frames_replaced` | Subset of drops caused by latest-frame replacement |
| `max_queue_depth` | Maximum number waiting, excluding the one active item |
| `age_at_start_ms` | Processing start minus evidence production |
| `age_at_completion_ms` | Completion/output emission minus evidence production |
| `lag_at_start` / `lag_at_completion` | Source head sequence at that ordered event minus evidence sequence |
| `max_processing_lag` | Maximum completion lag among processed frames |
| `start_freshness_violations` | Count with start age strictly greater than declared limit |
| `result_freshness_violations` | Count with completion age strictly greater than declared limit |
| `finished_at_ms` | Final simulated time after source horizon and drain |

Maxima expose the worst observed evidence age; arithmetic means describe the
processed sample, not all generated frames. Dropping changes that sample, so
always compare age statistics with consumed/drop counts. Empty samples use JSON
`null`, never fabricated zero age. `None` disables age thresholds through the
Python API; zero is a valid threshold. Equality passes. Event traces retain queue
depth, frame provenance, event time, and violation/drop reason. No automatic
wall-time latency, throughput benchmark, clock synchronization, or causal source
truth is inferred beyond the explicitly controlled synthetic model.

For 1.2, complete drain establishes exact conservation:
`produced = consumed + dropped`. Drop reasons distinguish overflow from replacement.
Milestone 1.3 extends the same engine with the policies below and preserves all
Milestone 1.2 baseline tests. Schema version 2 adds recovery configuration,
session context, output acceptance, and recovery metrics to JSON evidence.

## Sessions, interruption, and filtering (Milestone 1.3)

Each run begins with epoch zero. Ordered `Control` objects have priority 0,
before completions, productions, and starts. Controls at the same timestamp use
their declared tuple order. Validation rejects unsorted/out-of-horizon scripts,
duplicate disconnect/reconnect or freeze/unfreeze transitions, and mutable lists.
No source control may occur at or after the finite producer horizon.

- Disconnect ends the active epoch immediately. The active-session context is
  then `None`; production ticks continue but generate no evidence. Recovery
  starts a new, never-reused integer epoch and resets that epoch's sequence to
  zero. Production resumes on the original anchored tick schedule, not on an
  invented immediate recovery frame. Frame timestamps and provenance never change.
- Freeze pauses unique evidence production while retaining the same epoch and
  sequence head. Unfreeze resumes it. This models a producer pause, not a decoder
  that repeatedly returns duplicate pixels. Disconnect also clears a freeze.
- `Control(..., "slowdown", consumer_duration_ms=...)` changes the duration for
  subsequent processing starts, including restoring a faster duration. Active
  work retains its original completion time.
- `queue_on_disconnect="retain"` preserves waiting frames, the deliberately
  permissive baseline. `"invalidate"` drops all waiting frames at disconnect
  and records `invalidated_session`; active work is never cancelled by either
  queue policy. Reconnect does not silently clear retained evidence.
- A frame is obsolete when its epoch differs from the active epoch, including
  the no-active-epoch interval. Detection occurs at dequeue and completion;
  distinct detected IDs are counted once even if both phases produce events.
  The `session_filter` option rejects obsolete waiting frames before starting
  them and suppresses obsolete active results at completion. Each rejection is
  recorded once as a drop. There is no recovery grace period in this strict model.
- Age expiration remains a separate property: age strictly greater than the
  configured budget is a violation; equality passes. Age budgets are observed,
  not enforced by the session filter. A current-epoch FIFO output can still be old.
- Session `started`/`ended` events bracket lifecycle changes. After the source
  horizon the engine drains before recording final `session_ended` with reason
  `simulation_complete`. The experiment horizon alone does not obsolete draining
  work; explicit disconnect is the retirement boundary.

Frame provenance lives in `event.frame.session_id`; `event.session_id` records
the active context at the event. Thus a detected frame may have epoch zero while
the event context is epoch one or `None`. Trace list order is the deterministic
tie order. Sequence lag always uses the head of the evidence's own epoch; it is
never a subtraction across restarted sequences. An apparently low lag can
therefore coexist with obsolete provenance.

`frames_consumed` counts emitted outputs. `frames_processed` counts completed
work including rejected active results. `Processing.emitted` distinguishes the
two, and `obsolete_at_completion` records the observed boundary violation.
Completion/result age statistics and result violations use emitted outputs only;
processing-start statistics use all completed processing attempts, including
rejected active work. Rejected queued items have no processing-age sample.
Always inspect drops, processing attempts, and raw records along with output
statistics to avoid interpreting filtered empty output as success.

`frames_rejected`, `frames_invalidated`, and `frames_replaced` are distinct drop
subsets; FIFO overflow has its own drop reasons. Exact conservation remains
`produced = emitted/consumed + dropped` after drain. `obsolete_session_outputs`
counts emitted obsolete results; `obsolete_session_frames_detected` counts
distinct obsolete frames observed at either check, including suppressed results.

## Source no-progress watchdog

An optional positive `no_progress_timeout_ms` observes unique source identity
production, not consumer throughput or completed results. On each unique frame
or session start it arms a virtual deadline. If no newer frame/epoch supersedes
that deadline, exactly one `no_progress` event per episode records `since_ms` and
`at_ms`. After a frame resumes, a subsequent stall can produce another alert.
Disabled (`None`) means no watchdog events, not proven liveness.

Watchdog priority is 4: new evidence or a new epoch at its exact deadline wins
and resets the baseline. Only deadlines strictly before the known producer
horizon are monitored; post-horizon drain is not a source-stall experiment.
A timeout shorter than the intended production interval can correctly flag
that declared budget even for a normally configured source. Timeout selection
is an application/scenario decision, not a universal health criterion.

All lifecycle and boundary rules above are synthetic oracle conventions. A real
RTSP reconnect need not imply a new physical camera epoch; actual libraries may
retain different queues or expose no trustworthy lineage. No transport-specific
behavior or framework-neutral guarantee has been established here.
