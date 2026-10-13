# Milestone 1.2: deterministic buffering observations

These are measured outputs from the local numbered-item simulator on Fedora
Python 3.12.15. They are synthetic observations, not evidence of a real RTSP
defect, an existing-library gap, or package demand.

## Reproduce

```sh
.venv/bin/python -m video_freshness_lab
.venv/bin/python -m video_freshness_lab --scenario all --json
.venv/bin/python -m video_freshness_lab --scenario slowdown-fifo --queue-capacity 2 --overflow drop_oldest
.venv/bin/python -m video_freshness_lab --scenario slowdown-latest --freshness-threshold-ms 30
```

JSON contains configuration, metrics, frame IDs, processing start/completion
evidence, drop records, and ordered events. See [architecture and metric
definitions](../architecture/simulation.md). CLI interval/duration/threshold
overrides use integer milliseconds; queue capacity affects FIFO only.

## Actual comparison

All four configurations use producer interval 10 ms, source horizon 100 ms,
10 frames at times 0 through 90 ms, and freshness threshold 80 ms. FIFO is
unbounded here. Consumers take 10 ms (balanced), 25 ms (overload), or 40 ms
(both slowdown scenarios). The same frame schedule is used for both policies.

| Scenario | Consumed | Dropped/replaced | Max waiting | Max start age ms | Max result age ms | Result violations | Finished ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| balanced | 10 | 0/0 | 1 | 0 | 10 | 0 | 100 |
| overload | 10 | 0/0 | 6 | 135 | 160 | 6 | 250 |
| slowdown-fifo | 10 | 0/0 | 7 | 270 | 310 | 8 | 400 |
| slowdown-latest | 4 | 6/6 | 1 | 30 | 70 | 0 | 160 |

FIFO preserves all arrivals but its successful outputs become older. Latest-frame
retains evidence sequences 0, 4, 8, and 9 for processing; it deliberately drops
six waiting items. Its final drain starts item 9 at 120 ms and finishes at 160 ms,
so the maximum result age is 70 ms. Completion/production tie ordering is part
of this result, not an unspecified scheduler effect.

At the stricter threshold 30 ms, the identical latest workload has zero start-age
violations but four result-age violations. Replacing waiting evidence cannot
prevent slow active computation from yielding an old result. The 80 ms threshold
is an explicit example budget, not a recommendation for a real application.

## Verification and limits

The Milestone 1.2 suite passes 54 tests, including deterministic clock/event order,
immutable IDs, FIFO order and both overflow policies, replacements, exact drop
accounting, slow-consumer metrics, equality boundaries, invalid input, finite
drain, installed-package CLI/JSON, and packaging smoke import. Each of the four
named configurations is compared against itself for 100 repeat runs, including
full evidence/events; all match exactly. Tests forbid socket creation and
wall-clock access during that repeat check. This is deterministic in-process
evidence, not an integration flake-rate claim on shared runners.

Ruff lint/format, verbose pytest, pip integrity, and Git whitespace checks are
required before the milestone commit. No runtime dependencies were added.
No concurrency, real frames, transport, backend defaults, disconnects, or external
consumer behavior is exercised here. Thread safety is not asserted for these
single-threaded buffers. PRD requirements for a threaded live demo remain future
work; virtual time deliberately does not substitute for that exit criterion.

## Delivery status

Local implementation/validation is separate from GitHub synchronization.
The owner authorized creation of the PRIVATE repository
`https://github.com/devAIsh88/video-freshness-lab`. CLI identity was verified as
`devAIsh88` using approved network access; restricted-executor authentication
errors did not establish that host credentials were invalid. Repository creation
without extra initial files succeeded, private visibility was verified, and
foundation SHA `6ff7cb3f7aec0ee50175b22f85d0ad8642d052d0` was pushed and confirmed
on remote `main`. No credential workaround was used. This document records the
precommit validation snapshot for 1.2; its commit/push/CI outcomes are reported
after delivery rather than adding a status-only commit. The owner must ensure
GitHub Actions spending controls prevent unexpected overage charges. Only
standard Ubuntu CI runners are configured; no paid services were enabled.
