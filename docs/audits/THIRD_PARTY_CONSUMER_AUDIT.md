# Independent consumer audit: FrameGrab

Design recorded 2026-10-22 before target execution; report completed 2026-10-23.
Stage 6: PASS for a bounded independent file-consumer audit and honest results.
External RTSP/camera validation and adoption gates remain unmet.

Target: [Groundlight FrameGrab](https://github.com/groundlight/framegrab), exact
commit `17f550890b33925cbd92cf997776e64600954f87`, package metadata 0.15.1.
Source is inspected in `/tmp/vfl-third-party-framegrab`; no third-party source,
media or binaries enter this repository. The MIT license was read. The latest
commit is a 2026-03-17 merged file-frame-rate correction (#95); the repository is
not archived. This is evidence of maintenance within the past year, not a claim
of a response-time commitment or verified ongoing maintainer availability.

## Selection and source review

The PRDs name FrameGrab. It is a genuine camera/file consumer with a documented
public factory and existing native frame-decimation controls. Its supported
local video-file path permits an actual decoder experiment without discovery,
credentials, external endpoints, hardware, new listeners or Docker. The target
is unchanged; no mocked capture or deliberately broken consumer is used.

Reviewed: pinned README, MIT license, pyproject/build backend, package imports,
configuration validation, public factory/grab/transform/release path, complete
FileStreamFrameGrabber, RTSP capture/drain/cleanup code, and upstream file tests.
The target exposes decoded arrays and file cursor helpers. It does not promise
source capture timestamps, an application epoch, or rejection of a result already
held by application processing. GStreamer/FFmpeg RTSP claims remain separate from
file-reader behavior.

## Dependency decision before installation

Use a disposable Python 3.12 environment `/tmp/vfl-framegrab-env`. Install the
unchanged reviewed source with its normal public package imports. No fake modules,
patched target methods or hidden import wrappers. No project dependency changes.

| Dependency | Pin | Purpose | License / official source |
| --- | --- | --- | --- |
| FrameGrab | commit above, metadata 0.15.1 | Actual external consumer | MIT; pinned GitHub source |
| NumPy | 2.2.6 | Synthetic arrays | BSD-3-Clause plus bundled notices; PyPI |
| opencv-python | 4.12.0.88 | Upstream-declared decoder dependency | Apache-2.0/MIT wrapper plus bundled notices; PyPI |
| PyYAML | 6.0.3 | Upstream configuration import | MIT; PyPI |
| Pydantic | 2.12.3 | Upstream validated configuration | MIT; PyPI |
| Click | 8.1.8 | Upstream CLI import | BSD-3-Clause; PyPI |
| imgcat | 0.5.0 | Upstream eager preview import, unused preview | MIT; PyPI |
| ascii-magic | 2.3.0 | Upstream eager preview import, unused preview | MIT; PyPI |
| WSDiscovery | 2.1.2 | Upstream eager discovery import, no discovery invoked | LGPL-3.0-or-later; PyPI |
| onvif-zeep | 0.2.12 | Upstream eager discovery import, no ONVIF invoked | MIT; PyPI |
| poetry-core | 2.2.1 | Reviewed standard upstream build backend | MIT; PyPI |

The three source-only dependency archives were downloaded directly from official
PyPI file URLs and checked against published SHA-256 before build-file review.
imgcat defines a deploy command; it is never invoked. Its ordinary build reads
metadata and registers commands. WSDiscovery and onvif-zeep builds declare
packages/data/dependencies; no camera discovery is run during the audit.
Build tools and resolved transitive dependency versions are recorded in
[the machine-readable summary](framegrab-audit-summary.json). Any installation failure remains visible. Dependencies stay outside
project runtime/CI and are not adopted as a reusable product surface.

## Predeclared experiments and criteria

Generate finite 96x160 BGR video containing source-created markers with existing
stamp helpers. Use FFV1 in AVI if supported; verify decoded marker identity rather
than assuming codec survival. No arbitrary sleeps or capture timestamps.

Run supported default replay, max_fps decimation, same-scene advancing markers,
new frames repeating a previous marker, seek/replay, postprocessing marker removal,
and held-output application-epoch transition. Compare original arrays/markers,
file cursor positions and the existing evidence diagnostics. Keep physical capture
age UNKNOWN. A file cursor is not automatically source image identity.

Pilot once, then 100 fresh trials per declared scenario. Required invariants:
readable markers match source truth when the selected path preserves them;
configured decimation follows source/target ratio; repeated content is diagnosed
without calling a static scene frozen; cropped-away identity becomes UNKNOWN;
old held evidence is rejected only by the explicit application policy; EOF is a
bounded documented exception; every owned capture closes. Report all failures and
timeouts without retries. A 120-second outer child-process watchdog bounds native
execution. No listener is created. This is an external file-consumer audit, not
external RTSP/physical-camera validation or a universal failure-rate estimate.

The final results below are separate from the initial cleanup observation.

## Initial cleanup observation and revised observation boundary

The first 100 normal trials stopped the cohort gate: 99 passed and repetition 55
reported one native task immediately after `capture.release()`. All 1200 frame
markers, 100 EOF observations and 100 capture closures passed; no Python worker,
socket or temporary media remained, and the owned process exited. The failed
trial is retained at `/tmp/vfl-framegrab-initial-normal.json`, SHA-256
`551b590347b79e00e057a500fed59073a90b2d2053a2f583a00af9d9fb5a5d52`.
This snapshot is not sufficient evidence of a sustained upstream thread leak.

Before a new full cohort, replace the instantaneous task-count inference with
an explicit bounded observation: compare actual Linux task IDs against one
worker baseline (not a moving per-trial count), record immediate remainders, and
require all new tasks to disappear within one second. Poll the observed predicate
at 1-ms intervals; a sleep alone never establishes correctness. Record cleanup
observation duration and every timeout. Upstream code and media settings remain
unchanged. The original failed observation is separate from the new cohort and
is not retried silently or attributed to an external defect.

## Actual results

Final cohort: **800 completed / 800 trials, 0 failed, 0 timeouts**, 100 fresh trials
for each row. No per-trial retries. The earlier 99/100 cohort is not pooled into
this result. The final cohort has 0% observed unexplained failures; the initial
instantaneous cleanup check had 1/100. Neither estimates a universal failure rate.
The summary preserves both cohorts, raw SHA-256 hashes, exact installed versions,
per-scenario distributions and the failed initial observation.

| Scenario | Observed result in each of 100 trials | Trial duration median / p95 / maximum (ms) |
| --- | --- | --- |
| Default replay | 12 ordered markers 0–11; EOF raises the supported RuntimeWarning | 39.025 / 43.236 / 56.525 |
| Native max_fps=5, source=20 | 3 returned frames at file positions/markers 3, 7, 11; EOF | 13.929 / 15.251 / 16.311 |
| Static scene, advancing markers | Bottom scene region identical; 12 independent arrays with advancing identity; no nonadvancing diagnostic | 39.054 / 42.212 / 43.865 |
| Repeated marked content | 12 independent decoded arrays with marker 0; 11 nonadvancing diagnostics | 39.160 / 41.892 / 44.434 |
| Supported seek | Markers 0, 1, 0; explicit seek event explains nonadvancing identity | 13.714 / 15.044 / 17.802 |
| Configured crop | Top 40 pixels removed; missing marker becomes UNKNOWN, not a consumer-assigned source ID | 7.203 / 8.309 / 8.446 |
| Held result, native control | New epoch output then old held array: 1 obsolete publication | 14.672 / 16.344 / 16.610 |
| Held result, explicit final epoch policy | New output published; 1 obsolete result rejected | 14.561 / 16.156 / 16.749 |

Timing uses `time.monotonic_ns()` in one worker process. Duration starts before
consumer construction and ends after release and cleanup observation. p95 is
nearest-rank, n=100 per row. These are experiment execution durations, not capture
age, recovery latency, throughput benchmarks or real-time file pacing. There is
no connection recovery experiment in this file audit. Native max_fps decimates
file positions; it does not promise that file reads sleep at the configured rate.

Accounting: 4,800 successful public `grab()` arrays observed, 4,700 readable source
markers and 100 deliberately cropped-away markers; 400 expected EOF observations;
1,000 owned captures closed. Constructor probe reads and internally discarded
frames are not counted as public acquisitions. Exact total native decoded-buffer
and drop counters are unavailable; the observed cursor skips substantiate selected
output positions only. Epoch controls have 400 completion decisions: 300 published
(including 100 intentionally obsolete native-control results) and 100 rejected.
No obsolete result was published with the explicit final check. These publications
are the local ledger's experiment records, not an upstream application's UI.

All 800 final cleanup predicates passed: zero extra Python threads, zero extra
native tasks relative to the fixed worker baseline after bounded observation,
zero open socket descriptors at worker completion, temporary media removed, owned
child reaped normally. No immediate native remainder occurred in this final cohort.
Native cleanup observation medians span 0.091–0.107 ms, maxima 0.183–0.977 ms by
scenario; the 1-second guard was never reached. This is measured Linux task
observation, not a proof about all OpenCV/FFmpeg lifecycles or race freedom.
The audit hook rejects Python socket creation before target import. It is an
additional guard, not a native-code network sandbox. The selected capture path
uses generated local files only and invokes no discovery/ONVIF/network methods.

## Classification and upstream value

| Finding | Required classification | Meaning |
| --- | --- | --- |
| File replay, decimation, EOF, seek and crop | Confirmed existing native guarantee | Supported behavior matches inspected implementation and this cohort |
| Markers survive actual FFV1 encoding, FFmpeg decoding and public consumer path | Confirmed reproducible external behavior | Exact identity validated only for these synthetic markers, codec and configuration |
| Repeated marker / held array remains old despite successful grabs | Confirmed reproducible external behavior | Shows what application evidence adds; no unsupported upstream freeze/session promise is alleged |
| File-consumer freshness defect | No defect observed under tested conditions | Explicit replay and crop are supported behavior, not bugs |
| Capture age, live source-head lag and physical session identity | Inconclusive due to evidence limitations | All remain UNKNOWN; file cursor is not capture truth |
| External GStreamer RTSP behavior | Blocked | Installed audit OpenCV build reports GStreamer: NO; no reviewed compatible build in this disposable environment |
| README GStreamer support check | Confirmed reproducible external behavior | Substring check prints YES even when the build line is NO; private documentation proposal prepared |

The [pinned README](https://github.com/groundlight/framegrab/blob/17f550890b33925cbd92cf997776e64600954f87/README.md)
contains a GStreamer support check using membership of the word `GStreamer` in
OpenCV's build information. The executed predicate returns True with the actual
line `GStreamer: NO`. The target's runtime support check is stronger and rejects
this build; this is a misleading documentation check, not a demonstrated RTSP
runtime defect. See [the unposted proposal](FRAMEGRAB_UPSTREAM_PROPOSAL.md).
No upstream issue, comment, patch, disclosure or acknowledgment was sent or received.

## Instrumentation burden and diagnostic usefulness

`observe()` is 15 physical lines, including signature/docstring. That wrapper
requires the existing `read_marker` (19 lines), `Marker` schema/CRC checks (24),
source marker generation (34) and its wire constants, plus fixture setup. The
existing `PublicationLedger` spans 35 lines; final-check wiring, transition and
held-work controls add code in `trial()`. The complete optional audit file is
about 370 lines, including supervision, measurement, assertions and cleanup.
These counts describe distinct responsibilities; adding a thin wrapper does not
make the complete integration a 15-line adaptation. Source and consumer changes
for a camera without a trustworthy marker could be much more invasive.

Source/epoch/sequence are actionable when the marker survives. Acquisition and
activation events carry monotonic times; an old held result reports
`obsolete_session` and `session_mismatch`. Repeated identity reports
`frame_identity_not_advancing`; a seek event supplies context so it is not called
a freeze. Capture age and live sequence lag are explicitly unavailable. Crop
correctly removes the ability to identify the frame. This prevents invented
precision but limits generic plug-in value.

The approximately 30-line target is met by a receipt-to-evidence wrapper only;
it is **not established for complete independent semantic instrumentation**.
A simple pytest/FFmpeg script can cover this supported file behavior. The useful
contribution is the explicit evidence vocabulary, negative controls, immutable
lineage and final publication recipe; a reusable package advantage remains
unproven. Native buffering plus the application's short epoch check remains the
proportionate recommendation.

## Reproduction and installation record

From the project root, the reviewed existing disposable environment reproduces:

```sh
/tmp/vfl-framegrab-env/bin/python -m pip check
PYTHONPATH=src /tmp/vfl-framegrab-env/bin/python integration/audit_framegrab.py --repeat 1 > /tmp/vfl-framegrab-demo.json
PYTHONPATH=src /tmp/vfl-framegrab-env/bin/python integration/audit_framegrab.py --repeat 100 > /tmp/vfl-framegrab-repeat.json
```

For a fresh audit, first clone and inspect outside this repository. Review the
pinned README, LICENSE.txt, pyproject.toml, package imports, grabber.py, config.py
and the source-only dependency build files before installation. Do not substitute
a moving branch or execute third-party installation scripts without review.

```sh
git clone https://github.com/groundlight/framegrab.git /tmp/vfl-third-party-framegrab
git -C /tmp/vfl-third-party-framegrab checkout --detach 17f550890b33925cbd92cf997776e64600954f87
.venv/bin/python -m venv /tmp/vfl-framegrab-env
/tmp/vfl-framegrab-env/bin/python -m pip install --only-binary=:all: numpy==2.2.6 opencv-python==4.12.0.88 PyYAML==6.0.3 pydantic==2.12.3 click==8.1.8 ascii-magic==2.3.0 poetry-core==2.2.1 setuptools==80.9.0 wheel==0.45.1 pytest-runner==4.5.1 zeep==4.3.2 ifaddr==0.2.0
```

After official PyPI metadata/hash verification and build review, the exact local
archive installation command executed was:

```sh
/tmp/vfl-framegrab-env/bin/python -m pip install --no-index --no-deps --no-build-isolation /tmp/vfl-framegrab-dependency-review/imgcat-0.5.0.tar.gz /tmp/vfl-framegrab-dependency-review/WSDiscovery-2.1.2.tar.gz /tmp/vfl-framegrab-dependency-review/onvif_zeep-0.2.12.tar.gz /tmp/vfl-third-party-framegrab
```

Archive SHA-256 values from official PyPI metadata:

- imgcat 0.5.0: `a6261bd3c766b1761a146d6e7209fb54620691b31057d0c050b96a761293cfe0`
- WSDiscovery 2.1.2: `ab816deff2db101be59830317e19b78a95e9146b2b0a747953345ae68d1d8b58`
- onvif_zeep 0.2.12: `aa8bbc02a73eaa50894b0c18e39fa8d318a583a664c65bf35b3c8029d1c40b49`

The first build-tool command mistakenly requested nonexistent pytest-runner 4.5;
pip refused it. Corrected to published 4.5.1 before target installation. This is
an operator dependency setup failure, not an audit trial or hidden retry.
Resolved transitive versions are in the summary; a fresh dependency resolution
is not guaranteed identical. All audit packages remain in `/tmp`; project runtime
and Python-only CI dependencies are unchanged. The optional runner checks the two
critical target module hashes before any trial and fails on drift/missing tools.

## Acceptance and delivery

The research exit criterion is satisfied by an actual maintained external
consumer audit with positive supported guarantees, an honest negative freshness
result, evidence limits and a concrete private documentation improvement. It
establishes neither maintainer interest nor demand from two unrelated developers.
Full project conclusions belong in the final decision and compliance audit.

Validation and private Git delivery are recorded after the required checks. The
commit containing this document is identifiable by the Stage 6 delivery message;
its exact SHA and CI results will be recorded in the final compliance report.

Required Stage 6 precommit checks on 2026-10-23: Ruff check and format check passed
(40 Python files); verbose pytest **305 passed in 1.70 s**; pip check and both
whitespace checks passed. Standard editable `.[dev]` installation succeeded.
The existing optional suites were rerun during this final execution: image six
methods, native three methods/30 cases, RTSP three methods/26 cases and transport
two methods/37 cases all passed. These Fedora integration results are separate
from ordinary Python-only GitHub CI. Dependency setup and private-repository
network access required authorized sandbox exceptions, not privileged host changes.

The reviewed source/build files, staged file inventory, full first-party diff,
original document containers, ignored-file inventory and all Git history were
scanned for secrets/sensitive artifacts. No pattern matches were found; this is
heuristic review, not certification. Original PRD hashes match the previous
technical report and neither original is tracked. No environment, video, binary,
third-party source or licensing change is staged. Repository remains private;
workflow remains read-only, SHA-pinned and CI-only. No maintainer was contacted.
