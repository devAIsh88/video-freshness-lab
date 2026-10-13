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
are single-use together; a simulator rejects a previously used or populated clock.

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
Session-aware filtering and interruption semantics are intentionally reserved for
Milestone 1.3, whose additions must preserve these baseline tests.
