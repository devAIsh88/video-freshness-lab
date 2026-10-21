# Original PRD implementation audit

Initial audit: 2026-10-21, actual committed baseline
`f7952a42e7d59e4b83d1fe6c7f9bb5c6c9b7ba7c`. This matrix was created before
additional implementation under the technical-stage master task. Previously
authorized Milestone 1.9 transport work was already uncommitted: its pilot had
36/36 passes and optional integration 37/37 case passes, but no final reliability
cohort or delivery. It is not treated as an accepted stage merely because it exists.

Both original PRDs were read completely and retain their recorded hashes. Stage
numbers below are the PRDs' original 0–7, not implementation milestones 1.1–1.9.
Statuses describe inspected evidence with its scope; historical reports are not
substitutes for tests. Initial baseline rerun: 275/275 Python-only tests passed.
Follow-up status belongs in the completion report; initial gaps are preserved here.

## Requirement and exit-criterion matrix

| Stage / requirement | Original exit criterion | Existing implementation | Existing tests | Evidence | Initial status | Missing requirement / action |
| --- | --- | --- | --- | --- | --- | --- |
| 0: PRD review, scope, uncertainty, privacy, CI/Git policy | Reviewed requirements and explicit stop conditions | AGENTS.md, README.md, docs/prd/README.md, docs/architecture/foundation.md, .github/workflows/ci.yml | tests/test_package_import.py; policy/diff inspection | 1.1 review; intact foundation history | PASS | Correct stale current-scope wording without rewriting historical reports; originals stay local |
| 1: immutable sequence and production time | Explain producer, consumer, backlog, throughput, latency, freshness and sequence lag | model.py, clock.py, simulation.py, architecture/simulation.md | test_clock_and_model.py, test_simulation.py | 1.2 measured virtual ages/lag | PASS | Synthetic timestamps only; no physical capture claim |
| 1: FIFO versus thread-safe latest mailbox and metrics | Alive FIFO freshness failure; latest controls; pure metrics without sleeps | buffers.py, threaded_mailbox.py, experiments.py, threaded_demo.py | test_buffers.py, test_threaded_mailbox.py, test_threaded_demo.py | 1.2 FIFO age 310 ms/latest 70 ms; 1.4 coordinated handoff and 100 lifecycle repeats | PASS | README's statement that full Stage 1 remains unfinished is stale after 1.4 |
| 1: runnable learning demo, clean termination | Threads stop; README describes experiment; no private artifacts | __main__.py, threaded_demo.py, .gitignore | installed CLI tests; conftest.py leak guard | 1.4 reports bounded cleanup and failure controls | PASS | Preserve drain-on-close; do not rewrite functioning mailbox |
| 2: epochs, immutable evidence, ordering and age oracle | Reject previous-session results deterministically with actionable context | evidence.py, threaded_sessions.py, gstreamer_contract.PublicationLedger | test_evidence.py, test_threaded_sessions.py, test_gstreamer_contract.py, test_rtsp_contract.py | 1.5 100 held-work lifecycle repeats; 1.6 unknown-clock fixtures | PASS | This is a logical application epoch, not physical camera-session discovery |
| 3: actual NumPy/OpenCV synthetic images and source-generated marker | Identity survives selected image path; expose backlog without GPU/camera | None: numbered objects and unstamped videotestsrc do not meet this | No cv2/NumPy tests; 1.6 symbolic pixel label is not an array | 1.7 tokens are raw bytes; 1.8 JPEG path has no source marker | NOT IMPLEMENTED | Implement optional tiny synthetic array/stamp path, verify transformations and immutable lineage; compare FIFO/latest with controlled processing delay |
| 3: dependency and provenance validation | Minimal CPU-only optional dependencies, preserved identity, honest unknowns | pyproject has only dev extra; cv2/NumPy absent from venv and system Python | No image integration suite | Fresh find_spec inspection | NOT IMPLEMENTED | Use isolated optional environment and documented trusted pins/licenses; leave ordinary CI media-free |
| 4: slow consumer/FIFO backlog | Reproducible stale behavior under identical source schedule | simulation.py; native experiments | test_simulation.py; integration/test_gstreamer_native.py | 1.2/1.7/1.8 | PASS | Already complete; reuse controls for image evidence |
| 4: no new data / producer freeze | No-progress distinguished from backlog and restart | simulation controls freeze/unfreeze; RTSP valve pause in 1.8 | test_recovery.py | 1.3 explicitly models producer pause | PASS | Do not relabel a pause as repeated decoded content |
| 4: new buffers repeating image identity/content | Distinguish successful delivery from unique evidence progress | None: symbolic pixels are not decoded arrays | No actual repeated-image regression | 1.3 explicitly lists duplicate pixels as untested | NOT IMPLEMENTED | Add image fixture with new buffers copying an old source marker, plus a static-scene/new-marker control |
| 4: disconnect, restart, obsolete output, recovery | Deterministic event ordering and strict old-output suppression | recovery_experiments.py, simulation.py, threaded_sessions.py | test_recovery.py, test_threaded_sessions.py | 1.3 3,600 virtual repeats; 1.5 held work; 1.8 actual client generations | PASS | Synthetic epoch boundary remains explicit; image variant must retain original marker |
| 4: shutdown/failure cleanup | Bounded cooperative worker exit with pending/active work and errors | threaded_demo.py, threaded_sessions.py; RTSP owned processes/NULL | thread/session tests; integration/test_rtsp_transport.py | 1.4/1.5; 1.8 140 clients/servers clean | PASS | No claim of race freedom or forced cancellation of arbitrary callbacks |
| 4: missing trustworthy capture evidence | Missing capture is UNKNOWN independent of receipt and PTS | evidence.py, rtsp_contract.py | test_evidence.py, test_rtsp_contract.py | 1.6/1.8 | PASS | Keep unknown over images/transport unless explicit synthetic ground truth is established |
| 5: existing source, real codec and RTSP media | Same contract exercised on actual RTSP path | rtsp_experiment.py: installed GstRTSPServer, JPEG/RTP/TCP, decoder/appsink | integration/test_rtsp_transport.py | 1.8 120/120; negotiated caps and RTP observations | PASS | No replacement SDK/server needed |
| 5: output contract integrated with RTSP receipt | Retired acquired work rejected at final output under equivalent native settings | Client.pull → frozen receipt_evidence → PublicationLedger.complete | 1.8 epoch/reconnect controls for FIFO/leaky with/without final check | Same 1.8 trials, not merely separate pure-session tests | PASS | Guarantee is application-generation held-work rejection; source identity/capture freshness remain UNKNOWN |
| 5: mature repeatability and declared limitations | At least 100 repetitions of mature event-order cases; ≤1% unexplained failures | Existing isolated runner supports repeat 100 | Optional integration has one trial/config; 1.8 only five/config | 1.8 final summary | PARTIAL | Run 100/config for mature normal/epoch/reconnect controls; report actual denominator/failures, cleanup and timing variability |
| 5: transport impairments | Controlled faults with safe ownership; optional additional reliability evidence | Uncommitted transport_framing.py, transport_relay.py, transport_experiment.py | Uncommitted test_transport_framing.py and integration/test_transport_faults.py | 1.9 pilot/integration only, final cohort not run | PARTIAL | Finish prior authorized 1.9 cohort/report and delivery; do not substitute it for missing stamped images or physical source truth |
| 6: maintained independent consumer audit and upstream evidence | External behavior reproduced or explicit honest negative result | No independent consumer selected/tested | None | Capability matrix is documentation/local fixture research only | NOT IMPLEMENTED | Deferred to next prompt; do not begin external behavioral audit now |
| 7: product decision and all gates | Evidence-based package/upstream/recipe/stop decision | Provisional PIVOT recommendations only | No adoption tests possible | 1.7/1.8 retain recipe; no demand claim | NOT IMPLEMENTED | Next prompt; no default package, public release or license selection |

## Cross-stage technical and adoption gates

| Gate | Initial status | Evidence / missing work |
| --- | --- | --- |
| Smoke passes while stale evidence is detected | PASS | Alive virtual FIFO emits old work; independent external value not implied |
| Session, sequence, lag and ordered failures | PASS | Simulator events/Processing include epoch/sequence/age/lag; native path exposes local delivery ordinals and explicit UNKNOWN source lag |
| Reference adapter approximately ≤30 lines | PARTIAL | rtsp_contract.receipt_evidence is a small wrapper, but no independent application or codec-surviving source marker adapter is validated; do not count the whole harness as a small adapter |
| ≥100 repetitions, ≤1% unexplained failures | PARTIAL | Virtual and threaded controlled runs meet counts; mature RTSP configurations have only five repetitions each |
| Value over basic pytest/FFmpeg script | NOT VERIFIED | No independent comparative benefit established; current evidence favors a recipe |
| Real external application behavior tested | NOT IMPLEMENTED | Using native libraries in a constructed fixture does not satisfy independent-consumer validation |
| Maintainer acknowledgment and two unrelated developers intending adoption | NOT VERIFIED | No evidence recorded; never fabricate contacts or send messages |
| Minimal instrumentation and proportionate maintenance | PARTIAL | Native buffering plus tiny output check; test harness complexity is not evidence of product value |
| Fedora/Windows portability | PARTIAL | Fedora pure tests and Ubuntu 3.11/3.12 CI verified; Windows execution unverified; native experiments Linux-only |
| CI only, privacy, license approval before public release | PASS | Read-only SHA-pinned CI; private remote; PRDs untracked; no publication or licensing approval |

## Interpretation and conflicts

- Both PRDs are draft v0.1. DOCX adds Fedora/Windows, explicit adapter/adoption and
  100-repeat gates omitted by the shorter Markdown; retain the stricter gates.
- PRDs describe an established problem; this repository's external reproduction
  remains unverified. Demonstration failures do not establish a package gap.
- The PRD source-tracking table suggests tracking a PRD, while the owner's explicit
  current privacy rule keeps both originals unchanged and untracked. Owner rule
  wins. The old 1.1 review's proposed staging commands are historical, not current
  authorization to publish originals.
- Existing-source reuse is mandatory. A narrow wrapper of the installed server
  is compatible; a new RTSP implementation is not. A bounded fixture-only relay
  is impairment scaffolding, not a production server or buffering framework.
- “Same contract over RTSP” can substantiate application-generation/output ordering
  here. It cannot honestly substantiate unknown physical capture/session identity.
  Report that narrower contract separately from source-freshness requirements.
- Current owner authorization supersedes historical milestone stop language, but
  this execution stops at technical Stage 0–5 completion or a documented blocker.
  Stage 6 behavioral audit, Stage 7 decision, public release and cameras are excluded.

## Authorized actions after this initial matrix

Complete meaningful pending 1.9 validation; implement only missing image lineage
and repeated-content coverage; extend mature RTSP repetitions and contract evidence
as needed. Preserve working buffers, epoch ledger and ordinary media-free CI.
Every coherent delivery requires all quality checks, security review, a meaningful
commit, private push and actual two-version CI verification. Update the technical
completion report with final statuses and delivery evidence; do not silently
replace the initial gaps with retrospective PASS labels.

## Stage 3/4 closure evidence

Actual NumPy/OpenCV arrays, source marker generation, color/PNG decoding, immutable
sidecars, queued/active identity checks and repeated decoded buffers now pass
the selected-path criteria. See [the image report](../experiments/stamped-images-results.md)
for 1000/1000 matching repetitions, six optional media tests and seven new pure
marker cases. The initial Stage 3 and repeated-content rows become PASS within
that explicit synthetic path; physical capture and video-codec lineage remain
NOT VERIFIED. Other already-complete Stage 4 scenarios were reused unchanged.

The first mature RTSP cohort stopped after 399/400 normal successes: one native
server process exited -11 during cleanup. Epoch/reconnect cohorts did not run.
Stage 5 mature repeatability remains PARTIAL pending lifecycle investigation;
do not hide this failure or treat separate image success as RTSP acceptance.
