# Technical PRD completion report — Execution 1 of 2

Experiments: 2026-10-21; report finalized 2026-10-22 (Asia/Kolkata).
This report covers the original PRD Stages 0–5 and the explicitly
authorized Milestone 1.9 work carried into this execution. Original stages and
implementation milestone numbers are not interchangeable. Stage 6 behavioral
audit and Stage 7 product/release decision have not begun.

Current report status: **Declared technical Stage 0–5 work completed and
validated within the scopes below; broader PRD product gates remain incomplete**.
Results are actual observations; unsupported evidence is not labeled PASS.
The initial gap matrix was written before further
implementation under the technical-stage master task and preserves its initial
statuses: [PRD implementation matrix](PRD_IMPLEMENTATION_MATRIX.md).

## Original Stage 0–5 status

| Original stage | Status | Evidence / scope |
| --- | --- | --- |
| 0: requirements and policy review | PASS | Both local originals fully read; foundation differences/conflicts retained; private CI-only delivery and stop conditions explicit |
| 1: producer/consumer learning lab | PASS on tested Fedora/Python core | Existing numbered simulation, FIFO/latest metrics and thread-safe clean-shutdown demo reused; no duplicate implementation |
| 2: evidence/session contract | PASS for controlled logical epochs | Frozen FrameEvidence, injected-clock diagnostics and locked final-output ledger; physical session/capture identity remains UNKNOWN |
| 3: stamped synthetic OpenCV frames | PASS for declared color/PNG path | Actual source-stamped arrays, original source/epoch/sequence checked after transform and at completion; 1000/1000 trace matches |
| 4: deterministic faults | PASS for declared synthetic scenarios | Existing slowdown/disconnect/restart/recovery/cleanup plus actual repeated decoded content and static-scene control; no real-camera freeze claim |
| 5: equivalent RTSP contract/repeatability | PASS for local application-generation contract | Actual decoded receipt reaches epoch ledger; corrected lifecycle 1200/1200, 100/configuration; initial 399/400 normal cohort and one server SIGSEGV retained separately |

Windows portability remains **NOT VERIFIED** across otherwise completed core
work. Native experiments are validated only on Fedora 44. Ordinary Ubuntu CI
passes on Python 3.11/3.12; it does not install or execute multimedia tests.
Physical capture freshness, trusted source clocks and camera epochs remain
**NOT VERIFIED/UNKNOWN**, never replaced with receipt age or decoder PTS.

## Gaps found and changes actually made

1. No actual image arrays or codec/transform marker validation existed. Added
   optional stamped_images using source-created NumPy arrays, visible label,
   binary source/epoch/sequence marker and checksum, OpenCV color conversion and
   lossless in-memory PNG roundtrip. Immutable evidence/pixels are retained.
2. A producer pause was the only freeze model; symbolic pixels were insufficient.
   Added three new decoded buffers containing the same old image marker, plus
   no-data and static-scene/new-marker controls. Existing fault models remain.
3. Mature original RTSP cases had only five repeats/configuration. Added a small
   supervisor calling existing isolated cases for 100/configuration. The first
   cohort exposed one server-process teardown crash and stopped at its baseline
   gate. The new fixture cleanup explicitly closes clients/removes sessions,
   unprepares media, checks source NULL, drains library tasks and reports evidence.
4. Previously authorized 1.9 impairment work was uncommitted on arrival of this
   master task. Completed its independent declared 720-trial assessment and delivery.
   Its result is not used to substitute for missing image or mature RTSP evidence.
5. Stale README scope language was corrected; initial and final audit findings,
   dependency purpose/pins/licenses, reproduction and limits are documented.

Working simulator, buffers, mailbox drain-on-close and epoch publication policy
are preserved. No new client SDK, queue framework, custom RTSP protocol server,
production package API, dashboard or infrastructure was developed.

## Files and tests

Milestone 1.9: transport_framing.py, transport_relay.py, transport_experiment.py,
test_transport_framing.py, integration/test_transport_faults.py; architecture,
results/summary, capability matrix, README/AGENTS and initial audit matrix.

Stage 3/4: stamped_images.py, test_image_marker.py,
integration/test_stamped_images.py; optional images extra in pyproject.toml;
stamped-images architecture/results/summary; README and audit/capability updates.

Stage 5: existing rtsp_experiment.py server ownership/lifecycle hardening,
positive native-cleanup assertions in integration/test_rtsp_transport.py,
pure missing/failed/confirmed cleanup evidence cases in test_rtsp_contract.py,
integration/repeat_rtsp_contract.py and the repeatability report/summary.

Tests added: 20 pure transport framing/config/watchdog cases, seven pure
source-marker cases, three pure native-cleanup evidence cases; optional actual
image/fault/cleanup controls remain outside normal pytest discovery. All original
275 Python-only tests are retained. No necessary assertion or test was removed,
weakened, skipped or retried silently.

## Actual image and deterministic-fault findings

Python 3.12.15 / NumPy 2.2.6 / headless OpenCV 4.12.0.88, isolated ignored media
venv. Default project venv remains free of NumPy, cv2 and GI. Only the optional
images extra adopts the reviewed official PyPI binary wheels; no Fedora package
or interpreter changes.

Source marker is drawn before queue admission. Marker survives BGR→gray→BGR
and PNG encode/decode; scene pixels change but source identity does not. Corrupt,
ambiguous, cropped or mismatched identity fails closed. This does not demonstrate
JPEG/video-codec survival, arbitrary transformations or camera identity.

Ten configurations ×100 repetitions = **1000/1000 full-trace matches**, plus ten
separate reference runs. Slow FIFO processes ten images and reaches 310 injected
ms maximum result age; latest processes source sequences 0,4,8,9, replaces six
waiting items and reaches 70 injected ms. These are virtual source-schedule ages,
not physical capture or CPU/network latency.

Three independently decoded arrays can have fresh local receipt observations
while carrying the identical old source stamp; the diagnostic detects two
nonadvancing identities. A static generated scene ROI with markers 0,1,2 advances
source identity; a producer pause generates no new arrays. Old queued images and
held obsolete completions retain their original markers. Filtered restart admits
no obsolete output under the declared model. Capture age stays UNKNOWN.

Full metrics, accounting distinctions and commands:
[image results](../experiments/stamped-images-results.md),
[image summary](../experiments/stamped-images-summary.json).

## Actual RTSP transport and contract findings

Fedora 44; system Python 3.14.7 / PyGObject 3.56.3; core/base/server 1.28.8,
JPEG/RTP/rtspsrc plugins 1.28.6. Installed GstRTSPServer supplies finite SMPTE
JPEG/RTP over IPv4 loopback TCP, decoded to appsink. FIFO/leaky configurations
and optional final-output filtering use the same media settings. No UDP loss,
physical-network fidelity or automatic reconnect guarantee is claimed.

The acquired decoded GstSample is the observation boundary. Client.pull creates
its frozen receipt sidecar, which trial.complete passes to PublicationLedger.
Held old evidence completes after explicit epoch activation and is suppressed
only in filtered modes. This directly connects the epoch contract to RTSP;
separate successful session and transport tests are not being combined by assertion.
Application epoch, connection generation and physical source epoch are distinct.
Unstamped RTSP source frame identity/capture age/source sequence lag remain UNKNOWN.

Milestone 1.9: **720/720 trials**, zero timeout, **400/400 explicit recoveries**.
2,200 acquired/processed = 1,960 published +240 epoch-rejected; 240 obsolete
publications occur only in deliberately permissive controls. Native waiting drops
240 are separate from application rejections. Recovery min/median/p95/max:
44.614/46.028/47.546/49.204 ms. Pending-read wake after NULL is roughly 100 ms
under held interleaved media. All 1,120 clients, 720 servers and 720 relay workers
cleaned up; no fallback/listener leak. These finite faults are TCP delivery holds
or socket cuts, not packet loss or physical source restart. Full distributions:
[1.9 report](../experiments/milestone-1.9-results.md).

The corrected Stage 5 cohort passed **1200/1200 trials**, 100/configuration,
with **400/400 explicit reconnect recoveries**, zero failed/unexplained trials and
zero timeout. It acquired/processed 3200 receipts, published 2800 and rejected
400 obsolete completions. All 400 obsolete publications occurred in unfiltered
negative controls; filtered modes published zero. Native snapshot drops were
zero in these short cases, not a claim about all native buffering.

All 1600 clients reached NULL and 1600 servers exited 0 with positive native
media-NULL/pool-drain evidence. No forced fallback, child/Python-worker remainder,
listening-port leak or native stderr trial occurred. Recovery from application
epoch activation through new owned-server startup to first new receipt:
min/median/p95/max **110.427/119.911/124.211/166.264 ms**, population standard
deviation 4.697 ms (n=400). New-client-open to receipt: 11.226/12.832/13.977/39.585
ms, excluding server readiness/construction. Exit-observed to bus-observed:
1.445/1.603/2.009/3.607 ms, an observation latency rather than physical fault-onset
latency. Client NULL min/median/p95/max 0.492/0.760/1.656/4.153 ms (n=1600).
Decoder PTS advanced within each connection, with separate domains across opens;
physical source continuity remains unknown. Full distributions, accounting and
raw hashes are in the Stage 5 report and sanitized summary.

The initial mature cohort's server -11 exit remains a real failed trial despite
successful media flow, client NULL and listener release. Exact native cause is
unestablished; explicit media/library cleanup improves the fixture ownership
contract. Subsequent successful repeats cannot prove race freedom or attribute
an upstream defect. See [Stage 5 evidence](../experiments/rtsp-contract-reliability.md).

## Verification record and unavailable evidence

Before each accepted implementation commit: editable installation, Ruff
check/format check, verbose pytest, pip check, working/staged whitespace and
staged security/full-diff review. After push: exact remote/CI verification. Current
lifecycle regression tests and all 305 pure tests pass; the corrected full cohort
completed 1200/1200 without timeout or cleanup failure.

| Verification | Actual completed result |
| --- | --- |
| Initial baseline pure suite | 275 passed |
| Milestone 1.9 pure suite | 295 passed |
| Stage 3/4 pure suite | 302 passed |
| Stage 5 full Python-only suite | 305 passed; all original 275 retained |
| Stage 5 native-cleanup focused pure tests | 13 passed, including three added cases |
| Ruff check / format check | Passed; 39 Python files formatted |
| pip check | Passed in project and optional image environments |
| Working and staged whitespace checks | Passed before each commit |
| Editable packaging / wheel | Editable install passed; wheel built in /tmp, 25 package/metadata files only |
| Existing CLIs | All-scenarios simulator JSON and slow threaded JSON passed; CLI regression tests retained |
| 1.7 optional native controls | 3 unittest methods /30 cases passed |
| 1.8 optional RTSP controls, corrected lifecycle | 3 methods /26 cases passed |
| 1.9 optional transport controls, corrected lifecycle | 2 methods /37 cases passed |
| Optional OpenCV image tests | Six methods passed |
| Image repeatability | 1000/1000 matches; reference runs excluded |
| Transport impairment repeatability | 720/720; 20/configuration; separate denominator |
| Initial mature RTSP cohort | 399/400 normal controls; one -11 exit; later scenarios stopped |
| Corrected mature RTSP cohort | 1200/1200; 100/configuration; zero failures/timeouts |

Commands actually used for final mandatory checks and optional suites:

```sh
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
git diff --check
git diff --cached --check
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_gstreamer_native.py -v
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_rtsp_transport.py -v
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_transport_faults.py -v
venv-media/bin/python -m unittest discover -s integration -p test_stamped_images.py -v
```

Finite reliability commands and exact settings are in the linked image, 1.9 and
Stage 5 experiment reports. The separate cohorts are never pooled into one
claimed failure rate. The final successful RTSP cohort followed a declared code
correction and fresh cohort, not a hidden retry of a failed trial.

Optional integration and native repetitions are local Fedora evidence, not GitHub
CI results. Sandbox socket/network/PyPI failures were resolved with authorized
outside-sandbox user execution; no privileged host changes. Missing tools were
not installed with administrator access. Package-cache warnings were nonfatal.
A no-build-isolation packaging attempt failed because the runtime venv does not
include the setuptools build backend; the standard pinned isolated build succeeded.
A manual threaded CLI probe used --scenario (unsupported); correction to the
documented --mode slow succeeded. These invocation failures were not test flakes.

Cross-stage external product gates remain PARTIAL/NOT VERIFIED: source identity
and capture clocks; approximately 30-line independent reference adapter; value
over basic pytest/FFmpeg; independent consumer reproduction; maintainer/adoption
interest. The small receipt helper is not an independently validated external
adapter. A successful constructed fixture does not prove a standalone-package gap.

## Security and delivery already verified

Original SHA-256 values unchanged and files untracked/absent from Git history:
PRD.md `d3cf3fdc9092905f97dac8999e7b5588f34b144eae4c2da38b52f4c5b432994e`;
DOCX `1daf713215f07ccc37dcaf1e5556e559ead2221d07369a0e4e7c0f71f9779997`.
Scan includes document members, first-party/staged content, all history to push
and ignored environment/cache inventory. No matched private keys/tokens,
credential URLs, private connection data, external RTSP endpoints, recordings,
environments or binaries are committed. Heuristic scanning is not certification.
The exact private owner/account and remote main are verified; foundation history
is intact. No deployment, paid services, license change or public disclosure.

| Completed implementation delivery | Commit | Synchronization / CI |
| --- | --- | --- |
| Milestone 1.9 transport assessment | `71dab03031346a374c36fb73fe8aa84af7c7c8b3` | Pushed; exact remote SHA verified; [CI](https://github.com/devAIsh88/video-freshness-lab/actions/runs/39643361131) Python 3.11 and 3.12 success |
| Original Stage 3/4 image lineage / repeated content | `e1080be434efc07b26bde96b7b81f0ae22af9c14` | Pushed; exact remote SHA verified; [CI](https://github.com/devAIsh88/video-freshness-lab/actions/runs/39645565947) Python 3.11 and 3.12 success |
| Original Stage 5 RTSP contract / native cleanup | `db8e94fe58af418eadd5e6c7eedf7944c7e660ce` | Pushed; exact remote SHA verified; [CI](https://github.com/devAIsh88/video-freshness-lab/actions/runs/39657982732) Python 3.11 and 3.12 success |

Stage 5 implementation commit: `db8e94fe58af418eadd5e6c7eedf7944c7e660ce`,
pushed to private origin/main; the exact remote SHA was verified. The completed
[CI run](https://github.com/devAIsh88/video-freshness-lab/actions/runs/39657982732)
and both individual jobs, checks (3.11) and checks (3.12), completed successfully
at that exact SHA. These jobs perform ordinary Python checks, not media integration.
This report
and demonstration guide form a separate meaningful audit deliverable; no empty
Stage 4 commit was manufactured.

## Remaining limits, recommendation and next execution

**PIVOT** to native configuration guidance and small final-output checks remains
supported. Do not build a new buffering/reliability framework. Technical completion
is scoped to the selected synthetic/Linux experiments; capture-clock/source truth,
Windows execution, UDP/public-network behavior and independent application value
are not silently declared complete.

The local technical evidence is ready for a separately authorized Stage 6 audit.
Selecting an independent consumer and an honest observable contract remains
necessary; this readiness is not proof of adoption, product value or source freshness.
The next prompt, not this execution, authorizes that behavioral audit and Stage 7.
Independent real-camera work additionally requires separate approval, private
endpoint handling, source identity surviving its actual codec, bounded clock/error
provenance, physical session definitions, meaningful fault scope and external
output lineage. No production camera connection has been attempted.

For the owner's demonstration use [the short guide](DEMONSTRATION_GUIDE.md).
It separates successful delivery, advancing source identity, logical session
validity and unknown physical freshness without a camera or cloud service.
