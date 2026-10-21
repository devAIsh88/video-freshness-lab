# Original Stage 5: mature RTSP contract repeatability

Predeclared cohort, 2026-10-21: **100 repetitions of each normal, held-output epoch,
and explicit reconnect configuration × FIFO/leaky × filter off/on = 1200 trials**.
This closes the initial audit's five-repetitions/configuration evidence gap; it
does not change the 1.8 pipelines, transport mode, buffering or output policy.

Acceptance: every trial must satisfy existing 1.8 invariants, decode actual media,
retain acquired sidecars through final output and report clean NULL/server/port
cleanup. Final repeatability gate is ≤1% unexplained failures per configuration;
all failures and timeouts remain visible and are investigated, never retried away.
Normal controls run before fault cases; a failed normal cohort stops faults.
The 30-second trial group watchdog, five-second startup/sample and three-second
NULL/join guards remain unchanged. No universal failure probability follows from
this single-host sample or an exact 100 successes.

```sh
PYTHONPATH=src /usr/bin/python3 integration/repeat_rtsp_contract.py --repeat 100 > /tmp/vfl-stage5-rtsp.json
```

The same output contract is actually connected: Client.pull obtains a decoded
GstSample, records its PTS and local receipt, creates a frozen sidecar with the
connection/controller provenance, and trial.complete passes that exact sidecar
to the existing PublicationLedger. An old held receipt completes after explicit
epoch activation. Native-only admission is the negative control and final epoch
filtering suppresses that result. This is not two separate successful tests.

Source alias is the owned fixture, connection generation is an explicit open,
application epoch is controller policy, and physical source identity is UNKNOWN.
Neither codec-surviving source pixels nor source capture time is asserted. Source
sequence lag is UNKNOWN. Native waiting replacement cannot retract acquired work.
No SDK, server, queue or recovery framework is added. The repetition supervisor
calls the existing isolated cases once each; the lifecycle correction below
strengthens the existing fixture's cleanup evidence.

Local optional integration remains distinct from ordinary GitHub Python 3.11/3.12 CI. Independent
application value and adoption are Stage 6/7 questions, excluded from this execution.

## Initial cohort failure and lifecycle correction (before final cohort)

The first cohort ran **400 normal controls: 399 passed, one failed**. The failed
case was FIFO/filter-on repetition 45, with four decoded receipts and client
NULL, server stop acknowledged, listener refusal and no remaining owned workers.
The server process exited **-11 (SIGSEGV)** instead of 0. Per the declared normal
gate, no epoch/reconnect cohort ran. Per-configuration failures were 0/100,
1/100, 0/100 and 0/100; aggregate 1/400. This is not hidden as a retry or treated
as an accepted full cohort. Raw evidence remains in
`/tmp/vfl-stage5-initial-baseline.json`.

Root cause is not established. The old fixture relied on process/interpreter
exit after removing its listener, while media/native library tasks could still
exist. That is inadequate ownership evidence even if most runs exit successfully.
The correction retains media wrappers until teardown, closes library clients,
removes sessions, explicitly calls media.unprepare, requires each source element
NULL, removes the mount, and calls RTSPThreadPool.cleanup before reporting library
cleanup and exiting. Parent still requires code 0, no forced fallback, exact-port
refusal, and now verified native cleanup metadata. No assertion or timeout budget
is weakened. Native queue/source/codec/epoch/publication settings are unchanged;
server stop is now an explicit library teardown rather than reliance on implicit
interpreter destruction. Interruption timings must be interpreted with that change.

Official lifecycle references, checked against installed GI signatures:
[media unprepare](https://gstreamer.freedesktop.org/documentation/gst-rtsp-server/rtsp-media.html),
[client filtering](https://gstreamer.freedesktop.org/documentation/gst-rtsp-server/rtsp-server-object.html),
[thread-pool cleanup for tests](https://gstreamer.freedesktop.org/documentation/gst-rtsp-server/rtsp-thread-pool.html).
This is fixture hardening after an observed failure, not attribution of a defect
to an external application or proof of the SIGSEGV's precise cause.

A single normal control with explicit cleanup passed. The optional RTSP suite
then passed 26 cases and the transport suite passed 37, including injected abort
cleanup. A **new 1200-trial cohort at 100/configuration** followed. The original
failure cohort is separate, not pooled into a success rate for the new lifecycle.

## Corrected cohort results

All **1200/1200 trials completed successfully**, 100/100 in each configuration:
zero failed trials, zero unexplained failures and zero reported/watchdog timeouts.
This meets the declared ≤1% observed-failure criterion for this fixture/version
and these event schedules. It is not a confidence bound on a real-world rate,
proof of race freedom or proof of the earlier crash's precise cause.

| Scenario | Native policy | Filter | Trials passed | Acquired / processed | Published | Epoch rejected | Obsolete published |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Normal | FIFO | Off | 100/100 | 400 | 400 | 0 | 0 |
| Normal | FIFO | On | 100/100 | 400 | 400 | 0 | 0 |
| Normal | Leaky | Off | 100/100 | 400 | 400 | 0 | 0 |
| Normal | Leaky | On | 100/100 | 400 | 400 | 0 | 0 |
| Epoch | FIFO | Off | 100/100 | 200 | 200 | 0 | 100 |
| Epoch | FIFO | On | 100/100 | 200 | 100 | 100 | 0 |
| Epoch | Leaky | Off | 100/100 | 200 | 200 | 0 | 100 |
| Epoch | Leaky | On | 100/100 | 200 | 100 | 100 | 0 |
| Reconnect | FIFO | Off | 100/100 | 200 | 200 | 0 | 100 |
| Reconnect | FIFO | On | 100/100 | 200 | 100 | 100 | 0 |
| Reconnect | Leaky | Off | 100/100 | 200 | 200 | 0 | 100 |
| Reconnect | Leaky | On | 100/100 | 200 | 100 | 100 | 0 |

Accounting: 3200 acquired = 3200 processed = 2800 published +400 application
rejected. The 400 obsolete publications are deliberate filter-off controls;
filtered configurations publish **zero obsolete outputs**. Native appsink
snapshot drops are zero in this cohort; these short schedules do not characterize
backlog. Production and total native buffering are not conserved from these
non-atomic snapshots. The existing slowdown and fault experiments provide that
separate evidence.

All 1600 client pipelines reached NULL. All 1600 server processes exited 0,
acknowledged native pool cleanup and reported nonempty all-NULL media evidence.
There were no forced termination fallbacks, listener-refusal failures, remaining
owned children/Python workers or nonempty stderr trials. No forced timeout
occurred; bounded supervisor behavior also has a separate regression test.

### Timing distributions

All values below are measured **milliseconds** from `monotonic_ns` in the trial
client process. Percentile is nearest-rank p95; standard deviation is population
standard deviation. Server acknowledgments' own clocks are not subtracted.

| Interval | n | Min | Median | p95 | Max | Std dev |
| --- | --- | --- | --- | --- | --- | --- |
| Epoch activation → first new-generation receipt | 400 | 110.427 | 119.911 | 124.211 | 166.264 | 4.697 |
| New client open → first receipt | 400 | 11.226 | 12.832 | 13.977 | 39.585 | 1.536 |
| Observed old server exit → ERROR/EOS observation | 400 | 1.445 | 1.603 | 2.009 | 3.607 | 0.189 |
| Client NULL request → observed NULL | 1600 | 0.492 | 0.760 | 1.656 | 4.153 | 0.382 |
| Decoder-pad observation → receipt | 3200 | 0.028 | 0.124 | 0.521 | 0.976 | 0.189 |
| Receipt → final output decision | 3200 | 0.063 | 0.106 | 155.149 | 205.608 | 51.325 |

Recovery succeeded in **400/400 explicit reconnects**. Activation-to-receipt
includes fresh owned-server process startup. Client-open-to-receipt starts after
server readiness and client construction; it is not full recovery duration.
Exit-to-bus is observation latency after explicit fixture teardown, not physical
fault-onset detection latency. The mixed receipt-to-decision distribution includes
intentionally held old work, so its long tail is expected. Per-configuration
distributions are retained in the [sanitized summary](rtsp-contract-reliability-summary.json).
Decoder PTS advanced within every connection; a new connection has a separate
PTS domain. No continuity or source identity is inferred across connections.

Raw final output: `/tmp/vfl-stage5-rtsp-final.json`, SHA-256
`0712846d3a22c95194b290b0be346ed183193a9745492e9ece69299a2fdf3461`.
Initial cohort SHA-256:
`fd80bfc1aebf7083b5439fb4f98a574659916901b23e20af469090d13fbbe778`.
Raw records remain local; they are not Git artifacts. The tracked summary contains
configuration counts, variability and the negative initial result without ports
or uncontrolled native metadata. Exact native versions and reproduction settings
are in the [testbed architecture](../architecture/local-rtsp-testbed.md).

### Decision

**PASS for the declared local application-epoch/output contract and measured
repeatability**, with the initial teardown failure and corrected lifecycle
explicitly recorded. Source-generated pixel identity and physical capture age
remain UNKNOWN on this unstamped JPEG source. Image lineage is established only
for the separate declared OpenCV/PNG path. This closes the original Stage 5
technical gap under that narrow contract, not every real-camera freshness claim.
PIVOT remains appropriate: native waiting-buffer configuration plus the small
final-output check, without a new transport/buffering framework. Independent
consumer value, Windows, physical camera/network/UDP behavior and adoption
remain unverified. Stop before original Stages 6–7.
