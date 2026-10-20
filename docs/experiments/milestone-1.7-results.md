# Milestone 1.7: native GStreamer capability validation

## Readiness, authorization, and gates

Actual starting HEAD was verified as
`803c44694100019c2b5c6cf6fdbcaf92a05dfb22`, matching the expected 1.6 milestone.
The only initial untracked files were the two owner-provided PRDs. Both originals,
the validation plan, evidence contract, capability matrix, previous reports,
simulation/threaded contracts and tests, and existing CI were reviewed. Original
PRDs remain unchanged, untracked, and absent from all committed history.

The owner authorized this finite local native-library experiment. PRD gates
still require independent application/third-party behavior, actionable lineage
and lag/order failures, approximately 30-line reference instrumentation, value
beyond a recipe, 100 mature integration repetitions with at most 1% unexplained
failures, maintainer acknowledgment, two unrelated developers' adoption intent,
and proportionate maintenance. Native-library observations below do not satisfy
all those gates or authorize transport/product development.

Preflight found **GStreamer core/tools/app plugin 1.28.6**, and system Python
**3.14.7**, **PyGObject 3.56.3**, **Gst 1.0 and GstApp 1.0** introspection.
Project Python remains **3.12.15**, without GI. Native runtime used system Python;
pure regression checks used the existing editable venv. Exact installed RPM
versions, licenses, prerequisites, properties and settings are in the
[experiment design](../architecture/gstreamer-experiment.md). No bindings or RPMs
were installed, no venv exposure settings changed, and pyproject remains unchanged.
The queried `gstreamer1-plugins-base-tools` package was absent and was unnecessary.

## Method

Direct appsrc → appsink, custom synthetic caps, 13-byte registered identity tokens,
explicit epoch sidecars and PTS. No images, codec, intermediate queue, file source,
network, RTSP endpoint or display. Appsrc has a four-buffer configured limit;
appsink has two waiting slots. The six finite workloads compare native FIFO (A),
native downstream leaky (B), FIFO with final-output filtering (C), and leaky with
filtering (D). See the design for phase order and all property values.

The native-only/filtered pair receives identical token/epoch/PTS data and owner
phase schedule. Actual monotonic times differ. FIFO backpressure prevents a full
burst from entering the sink before pulling resumes; leaky admits the whole burst.
We establish reachable boundaries with pad observations and post-insertion
signals, rather than forcing the simulator's scheduling on GStreamer.

Arrival is locally measured application receipt after acquisition. Processing
starts then, and its completion can be withheld across production/epoch phases.
No inference worker is simulated by sleep. Publication is a locked in-memory
ledger with validation and insertion under the same lock, consistent with 1.5.
The filter adds no waiting queue and does not change native drops.

## Stable outcomes in the final repetition cohort

Twenty fresh subprocess cases per combination: **24 combinations, 480 cases**.
Every case completed with the following identities and counts. Tokens 0/1 are
epoch 0; tokens 2/3 are epoch 1 only in the two epoch workloads.
Native drops and rejections are separate categories.

| Workload | Native policy | Submitted | Acquired tokens | Native drops | Rejected A/B → C/D | Published A/B → C/D | Unpulled at NULL |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Balanced | FIFO or leaky | 4 | 0,1,2,3 | 0 | 0 → 0 | 4 → 4 | 0 |
| Slow consumer | FIFO | 4 | 0,1,2,3 | 0 | 0 → 0 | 4 → 4 | 0 |
| Slow consumer | Leaky | 4 | 0,2,3 | 1 | 0 → 0 | 3 → 3 | 0 |
| Finite pause | FIFO or leaky | 4 | 0,1,2,3 | 0 | 0 → 0 | 4 → 4 | 0 |
| Buffered epoch | FIFO | 4 | 0,1,2,3 | 0 | 0 → 2 | 4 → 2 | 0 |
| Buffered epoch | Leaky | 4 | 2,3 | 2 | 0 → 0 | 2 → 2 | 0 |
| Active epoch | FIFO | 4 | 0,1,2,3 | 0 | 0 → 2 | 4 → 2 | 0 |
| Active epoch | Leaky | 4 | 0,2,3 | 1 | 0 → 1 | 3 → 2 | 0 |
| Pending shutdown | FIFO or leaky | 2 | None | 0 | 0 → 0 | 0 → 0 | 2 |

The useful counterexample is active epoch with leaky buffering: native queue
replacement removes waiting token 1, but token 0 was already acquired. The
native-only application publishes its obsolete result after epoch 1 activates;
the filtered application rejects that completion and publishes only 2/3. This is
a consequence of application-owned processing and the declared epoch policy,
not a GStreamer defect. A buffered old sample that survives FIFO is similarly
processed then rejected at final output. No epoch is inferred from PTS reset.

In the buffered-epoch leaky workload, native replacement already removes both old
waiting samples, so filtering changes nothing. Balanced/pause workloads also gain
nothing from filtering. These are useful controls against assuming every custom
check adds value on every path. The finite pause is an observed empty phase
between two pairs, not a measured-duration freeze or a liveness watchdog test.

## Counters, completeness, and time

Stable final observations in the cohort total **1,760 submitted**, **1,440 acquired**,
**160 native drops**, **100 application rejections**, **1,340 publications**, and
**160 intentionally unpulled shutdown buffers**. Stable native `in` counts match
submissions, `out` matches acquisition, and appsrc forwards every submitted buffer,
with zero final pending buffers and zero appsrc drops.

```text
1760 = 1440 + 160 + 160
1440 = 1340 + 100
```

At the withheld-consumer boundary every observed sink occupancy is 2. FIFO's
buffered-epoch phase observes one appsrc buffer still queued; the corresponding
leaky phase observes zero. A native buffer can also be in transit/blocked during
sink admission. Independent `get_property` reads are explicitly non-atomic;
intermediate snapshots are not summed into conservation or called global peaks.
The quiescent pre-NULL observations supply the accounting. Native counters reset
on state changes, so post-NULL zeros are not used to claim no loss.

All timing is local monotonic observation, not source capture age. Arrival age
means decision minus application receipt, processing delay means decision minus
processing start, and pad-to-receipt residence covers the native sink path.
Capture age is `null` for every receipt; PTS is not subtracted from local time.
The JSON records per-observation values and provenance. Across all **1,440**
completed/acquired observations, distributions in milliseconds were:

| Local measurement | Minimum | Median | Maximum |
| --- | --- | --- | --- |
| Receipt-to-decision age | 0.015527 | 0.042632 | 1.958530 |
| Processing start to decision | 0.001245 | 0.003144 | 1.897652 |
| Sink-pad entry to receipt | 0.028119 | 0.283364 | 4.325464 |

These pooled descriptive samples include both published and rejected attempts;
they exclude native drops and unpulled shutdown buffers. They mix workloads and
are not comparative performance estimates or freshness budgets. Exact time
equivalence is neither expected nor claimed. Per-case JSON permits separating
the observations by workload, policy and filter.

## Reproduction, regression, and cleanup

```sh
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -v
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.gstreamer_experiment --repeat 20 > /tmp/vfl17-results.json
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
git diff --check
git diff --cached --check
```

The normal suite passes **265 tests**, preserving all **259 previous tests**.
Six focused pure tests cover configuration, exact evidence association, metric
conservation, admission/snapshot ownership, process failure and watchdog handling.
Existing package-import and CLI tests remain active. Lint/format checks pass for
26 Python files; pip integrity and working/staged whitespace checks pass. Editable
installation succeeded after sandbox PyPI DNS failure and approved escalation;
the cache warning was nonfatal. No dependencies or system packages changed.

The explicit system-Python integration command passes **3 unittest methods**
covering **30 subprocess cases**: 24 native/filter comparisons, two `wait-on-eos=true`
drain controls, and four injected failure paths. Missing bindings are failures,
not skips. Ordinary Python 3.11/3.12 GitHub CI executes only the Python-only suite;
it does not install GStreamer or claim these runtime cases ran on Ubuntu.

Pending shutdown uses `wait-on-eos=false`: EOS is observed with two queued samples,
then NULL intentionally abandons them without inventing session rejection counts.
With `wait-on-eos=true`, the integration control observes EOS at the sink pad
with two pending buffers, verifies no bus EOS at that boundary, drains, and then
observes bus EOS. Explicit NULL succeeds in every successful and injected-failure
case. No new Python worker threads remain. Native tasks stop with NULL and each
case exits its process; no live native task can carry into the next case.

Injected real bus messages preserve error domain/code; unregistered payload,
processing failure, and owner abort with a full FIFO also produce failed reports
and NULL cleanup. Native calls and Python waits have guards; the 15-second child
watchdog is separately tested without waiting 15 real seconds. There is no silent
retry. No naturally occurring library error was observed in the formal cohort.

## Development failures and variability

The first 24-case pilot had **11 false EOS timeout reports**. Its error-only bus
poll discarded EOS messages before the EOS wait. All 24 pipelines still reached
NULL. This was a harness error, not unexplained flakiness or a decoder defect.
The corrected pilot completed all 24 cases, and a first 480-case repetition
cohort then had zero failures. Final review additionally isolated ledger snapshots
from caller-owned dictionaries; focused and integration tests were rerun, followed
by the final cohort reported above. Earlier cohorts are not silently pooled into
the final timing distribution or hidden as retries.

Stable counts/identities follow tight gates and small workloads. Runtime scheduling
and timing vary; repeated timestamps and snapshots are not byte-identical. Twenty
repetitions per final configuration do not meet the PRD's later 100-repeat mature
integration gate. This experiment does not establish universal race freedom,
throughput, long-run memory behavior, Windows portability, decoder behavior, or
real-library correctness under every configuration.

## Security, delivery, and decision

Review includes intended source/tests/docs, staged contents, relevant Git history,
ignored artifact inventory, original PRD hashes, and document-container members.
Only synthetic payload IDs, opaque local aliases and technical measurements are
used. Generated reports remain local under `/tmp`; no binary media or datasets
are committed. No secrets, credentials, private URLs, licensing changes, paid
services, deployment, release or package publishing are introduced. The existing
read-only SHA-pinned CI workflow is unchanged. Private repository identity and
visibility must be confirmed before delivery; exact commit/push/CI outcomes are
reported after the single milestone commit, without an artificial status commit.

**Recommendation: PIVOT.** Native GStreamer supplies the tested bounded queue and
leaky policies; minimal application integration supplies the separate logical
epoch/output rule. A second buffering framework adds no demonstrated value.
Prefer validation tests, configuration guidance and a small reference integration.
The final-output check is useful here, but its deliberately constructed baseline
does not justify a standalone package or claim an external consumer defect.

Remaining transport evidence includes codec/image lineage, RTP/RTCP timing and
clock uncertainty, trustworthy physical source/session boundaries, real reconnect
behavior, backend buffering under loss, blocked network-read shutdown, independent
consumer reproduction and adapter burden. Physical capture freshness remains
insufficiently evidenced. Maintainer/adoption and licensing decisions remain open.
Any later local-image or RTSP milestone needs new owner authorization and declared
test budgets; it must not inherit a capture-freshness pass from this experiment.
Stop after 1.7.
