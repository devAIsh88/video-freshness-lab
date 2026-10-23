# Final research report

Completed 2026-10-23, Asia/Kolkata. Research outcome: **PIVOT to a documented
reference recipe and validation toolkit**. Bounded research stages have outputs;
external adoption, Windows, physical-camera evidence and package-release gates
remain incomplete. The final decision does not authorize publication or more work.

## Objective and background

Investigate whether an application can keep successfully receiving/processing
video while publishing results from old or obsolete evidence, and whether a
small trustworthy contract adds value beyond existing media-library controls.
Both original PRDs require staged learning, evidence provenance, fault testing,
real RTSP integration, independent consumer evaluation and an evidence-based
package/upstream/recipe/stop choice. Implementation milestones are not PRD stages.
The [final compliance audit](../audits/FINAL_PRD_COMPLIANCE.md) maps every stage,
functional/nonfunctional requirement and technical/adoption gate.

A queue limits waiting work. A final result may already be in processing outside
that queue. Correctly testing the latter requires original evidence to survive
through processing and to be checked against the current application epoch at
publication. Successful receipt, PTS progression, a recent arrival timestamp and
physical capture freshness are different claims.

## Implemented architecture and methodology

The standard-library core has frozen numbered frames, a deterministic event
clock, FIFO/latest policies, a Condition-protected one-slot mailbox, synchronized
session transitions, immutable evidence and pure diagnostics. Output examples
validate epochs and record decisions atomically under the epoch lock. Optional
images, native GStreamer, actual local RTSP and an external consumer use separate
explicit adapters and measurement boundaries. [Code guide](../guides/CODEBASE_GUIDE.md)
and architecture documents describe actual symbols and lifecycle.

Correctness assertions prefer source identity, legal event order, injected clocks,
explicit events and pipe acknowledgments. Finite native cases have bounded waits,
process supervision and positive cleanup checks. Reliability cohorts have declared
configurations and no hidden per-trial retries. A failed initial cohort remains
separate after a correction or observation-boundary change. Timings use monotonic
clocks in identified processes; cross-domain subtraction is not assumed valid.

## Results by evidence environment

These rows are separate experimental populations. They must not be summed into
a claimed overall real-world success rate.

| Layer | Actual evidence | Conclusion / boundary |
| --- | --- | --- |
| Virtual numbered simulation | Slow FIFO: 10 results, max age 310 virtual ms, 8 over 80 ms budget. Latest: sequences 0,4,8,9, 6 replacements, max 70 ms, 0 violations. Recovery 36 configurations ×100=3600 identical traces | Availability/completion can coexist with stale evidence. Latest alone still fails stricter budgets and emits obsolete held work |
| Real Python threads | Controlled slow handoff: accepted 10, delivered 2, replaced 8. 100 normal/slow/idle lifecycles each, 600 workers joined; session held-work/legal-order tests | Demonstrates explicit ownership, blocking wake and locked final epoch rule; not a scheduling benchmark or proof of all races absent |
| Native appsrc/appsink, historical 1.7 | 480/480, 24 configurations ×20; submitted 1760=received1440+native drops160+unpulled160; received=published1340+rejected100 | Existing native leaky waiting policy suffices; an acquired result needs application output policy. Raw token lineage is not image-codec lineage |
| Source-stamped OpenCV images | 1000/1000 full-trace matches, ten configurations ×100; references excluded. Six optional image methods, seven pure marker cases | Original source/epoch/sequence survives BGR/gray/PNG path; repeated decoded old stamps differ from pause, static scene and queued old work |
| Local RTSP 1.8 | 120/120, six scenarios ×four queue/filter modes ×five | Real JPEG/RTP-over-TCP/decode receipts reach final ledger; short initial repeat count alone did not meet mature PRD gate |
| Controlled TCP faults 1.9 | 720/720, nine scenarios ×four modes ×20; 400/400 explicit recoveries | Delay/stall/cuts, repeated recovery, slow consumer and shutdown evidence only for owned loopback TCP fixture |
| Corrected mature original Stage 5 RTSP | 1200/1200, normal/epoch/reconnect ×four modes ×100; 400/400 explicit recoveries | Same final logical application contract tested on actual decoded receipts with measured local repeatability |
| Independent FrameGrab supported file path | Final 800/800, eight scenarios ×100; 4800 public arrays, 4700 readable markers, 100 intentionally removed markers | Supported native behavior confirmed; source marker survives FFV1/FFmpeg/public consumer path; no reusable freshness defect observed |

Historical native version 1.7 used GStreamer/app 1.28.6. Later RTSP/cohorts and
handover use core/base/server 1.28.8, JPEG/RTP/rtspsrc 1.28.6, system Python
3.14.7, PyGObject 3.56.3. Handover native CLI reports app 1.28.8; historical
measurements are not relabeled as new-version repetitions. Pure Python and
optional images use 3.12.15. NumPy is 2.2.6, OpenCV package 4.12.0.88 (cv2 4.12.0).
The target commit/version and complete external environment are pinned in its audit.

## Buffer, epoch and timestamp findings

The source creates image identities before buffering. Metadata attachment alone
was not accepted as image-codec lineage. Actual transformation output is decoded
and checked against original sidecars. A crop/corrupt marker fails closed or becomes
UNKNOWN. FFV1 evidence from the independent audit does not add pixel identity to
the unstamped JPEG RTSP source.

The RTSP Client.pull boundary creates receipt evidence for the exact decoded
sample used by the trial. Connection generation, local delivery ordinal and
controller application epoch remain distinct. The same sidecar reaches the final
PublicationLedger. This directly exercises the session rule in the RTSP path;
separate successful transport/session unit tests are not substituted for integration.

In the mature RTSP cohort, acquired/processed 3200 = published 2800 + epoch-rejected 400.
All 400 obsolete publications occur in permissive controls; filtered configurations
publish zero obsolete results. Native waiting drops are separately observed, zero
in these short mature cases. In the 1.9 cohort, acquired/processed 2200 =
published 1960 + rejected 240; native waiting drops 240 are separate; obsolete published
240 only in permissive controls. In the external file epoch controls, 400 decisions
produce 300 publications (100 intentionally obsolete controls) and 100 rejections.
Constructor reads/native internal decimation are not counted as observed public
acquisitions. Exact end-to-end native file buffer/drop totals are unavailable.

RTSP decoder PTS progresses within connection domains but does not prove capture
age or physical source continuity. A PTS gap is not packet-loss evidence; the 1.9
cohort includes gaps even in baseline. Physical capture time, live source-head lag
and authenticated camera session identity remain UNKNOWN. The external file audit
also keeps capture age and live source lag UNKNOWN despite verified pixel markers.

## Recovery timing and variability

| Measurement / monotonic reference | n | Minimum / median / p95 / maximum ms | Scope |
| --- | --- | --- | --- | --- |
| 1.9 explicit recovery after controlled fault ends | 400 | 44.614 / 46.028 / 47.546 / 49.204 | Local fixture metric defined in 1.9 report; not camera/network recovery SLA |
| Stage 5 application epoch activation → first new receipt | 400 | 110.427 / 119.911 / 124.211 / 166.264 | Includes owned new-server startup; population SD 4.697 ms |
| Stage 5 new client open → first receipt | 400 | 11.226 / 12.832 / 13.977 / 39.585 | Excludes server readiness and construction |
| Stage 5 observed server exit → bus observation | 400 | 1.445 / 1.603 / 2.009 / 3.607 | Observation latency, not true physical fault-onset detection |
| Stage 5 client NULL transition | 1600 | 0.492 / 0.760 / 1.656 / 4.153 | Explicit finite teardown path |

The original reports define collection boundaries, quantile methods, distributions
and raw hashes. The external audit's durations are whole-trial execution times,
not connection recovery or capture freshness. They are reported separately in
[its audit and summary](../audits/THIRD_PARTY_CONSUMER_AUDIT.md).

## Failure history, repeatability and cleanup

1. The early 1.7 pilot had false EOS timeout observations due to harness bus polling;
   its investigation remains in the historical report.
2. The first mature RTSP baseline had 399/400 successes and one server exit -11
   during teardown. Media flow/client NULL/port release alone did not earn a pass.
   The exact native cause remains unproven. After explicit media unprepare/NULL,
   client/session removal, pool drain and positive cleanup evidence, a separately
   declared cohort completed 1200/1200. This does not prove race freedom.
3. The first external baseline had 99/100 passes: one immediate native-task
   snapshot after release saw one new task. Capture closures, identity/EOF and
   process exit passed. The final cohort used a predeclared fixed task baseline
   and one-second bounded disappearance predicate, recording immediate remainders.
   All 800 passed; there were no immediate remainders in that cohort. Initial cause
   and sustained-leak behavior are unproven. The original failed record/hash remains.

Final RTSP cohort: all 1600 clients NULL and 1600 servers exited 0 with positive
native cleanup; no forced fallback, remaining owned Python worker/child or listener.
Milestone 1.9: 1120 clients, 720 servers and 720 relay workers cleaned up. External final:
1000 captures closed, no extra Python/native tasks after bounded observation,
no socket descriptors at completion, temporary media removed and child reaped.
A timeout/fallback would be a failed trial. Counts remain scoped to their cohorts.

## Independent audit and native-versus-custom value

Target: Groundlight FrameGrab, commit `17f550890b33925cbd92cf997776e64600954f87`,
metadata 0.15.1, MIT. Latest pinned commit dated 2026-03-17, repository not archived;
maintenance observed within a year, current response commitment unknown. Reviewed
outside our repo before execution, including build/import/dependency/license paths.
No third-party source, dependency tree, binary or generated video is committed.

Real supported file replay, max_fps decimation, EOF, seek and crop match the
implementation. A fresh returned buffer can contain repeated old evidence;
explicit seek legitimately repeats identity; crop removes observability. An
already held array remains old across application transition, which the final
application check detects. None is alleged to violate an upstream promise.

The README GStreamer availability predicate returns True for a NO build. The
runtime guard rejects that build, so this is a documentation issue. A private
proposal is prepared, not posted. External RTSP execution is BLOCKED because the
audited OpenCV build lacks GStreamer. No maintainer acknowledgment or two unrelated
developers' adoption intent exists.

The 15-line observe wrapper and 24-line RTSP receipt helper are small. Full semantic
instrumentation includes marker decoding/schema/source generation, lifecycle and
publication wiring; the independent audit is 368 lines including test/supervision.
The complete approximately 30-line reference-integration gate is PARTIAL. Existing
native buffering plus a short final epoch policy suffices for the tested contract.
A standalone package's value over a pytest/FFmpeg recipe is not established.

## Final verification and reproduction

Mandatory commands: editable `pip install -e '.[dev]'`, Ruff check, format check,
verbose pytest, pip check, working/staged diff whitespace and staged/history
security review. Final execution has 305 pure tests passing; all original 275 remain.
Optional image six methods, native 3 methods/30 cases, RTSP 3/26 and transport 2/37
passed locally. Quick CLI path: 24 native, 24 RTSP and 4 stall cases passed.
The external 800-trial cohort is local
optional evidence, never represented as ordinary GitHub CI coverage.

Exact tested commands, setup boundaries and cleanup:
[demo runbook](../guides/DEMO_RUNBOOK.md). Full reliability reproduction:
[image report](stamped-images-results.md), [native report](milestone-1.7-results.md),
[RTSP report](milestone-1.8-results.md), [fault report](milestone-1.9-results.md),
[mature contract report](rtsp-contract-reliability.md),
[independent audit](../audits/THIRD_PARTY_CONSUMER_AUDIT.md).
Private commit/push/two-version CI evidence is in the compliance audit and final
delivery response. CI remains Ubuntu Python-only; it does not run media tests.

Final precommit verification on 2026-10-23:

| Check actually run | Result |
| --- | --- |
| .venv/bin/python -m ruff check . | Passed |
| .venv/bin/python -m ruff format --check . | Passed, 40 Python files |
| .venv/bin/python -m pytest -v | 305 passed in 1.71 s |
| Project, optional image and disposable audit pip check | Passed, no broken requirements |
| git diff --check and git diff --cached --check | Passed; repeated after explicit staging |
| Standard editable dev installation | Passed |
| Local wheel build and member review | Passed; 25 package/metadata files, no media/PRDs/native binaries; wheel kept in /tmp |
| Optional image final rerun | Six methods passed in 0.132 s |
| Optional native final rerun | Three methods /30 cases passed in 3.589 s |
| Optional RTSP final rerun | Three methods /26 cases passed in 15.146 s |
| Optional transport final rerun | Two methods /37 cases passed in 25.050 s |
| Local links and external summary accounting | Passed |
| Working/staged/history/container secret and artifact review | No pattern matches; originals unchanged/untracked; heuristic review only |

The final execution adds the independent optional audit runner, its report and
summary, an unposted upstream documentation proposal, final decision/compliance,
five owner guides and this report. README, AGENTS, the initial requirement matrix
and library capability matrix are updated. Existing core behavior, dependencies,
ordinary tests, workflow and license remain intact. Exact finalization SHA and
post-push CI are in the delivery response because a commit cannot contain its own
SHA or the subsequent CI result without creating another commit.

## Limitations and research conclusion

Windows, real cameras, physical capture clocks, source restart identity, H.264/GOP
recovery, broad codecs/backends, UDP impairment and physical/public networks are
not validated. A local success cohort does not imply a universal failure rate.
No clinical/safety/production validation, community adoption, accepted upstream
contribution, package approval or public license is claimed.

The project demonstrated the distinction it set out to investigate, found native
mechanisms sufficient for waiting buffers, tested a narrow application output
contract and performed an actual independent audit with an honest negative
freshness result. The supported outcome is the reference recipe/toolkit, with
active work stopped and product gates deferred. See [final decision](../audits/FINAL_GO_NO_GO_DECISION.md)
for reopening conditions. **RESEARCH COMPLETE WITH EXPLICIT UNMET EXTERNAL GATES**.
