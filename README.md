# Video Freshness Lab

A CPU-only research lab for testing whether successful video processing
can still publish results from old or obsolete evidence. It compares FIFO/latest
buffering, tracks immutable frame evidence, validates application epochs at final
publication, and exercises existing GStreamer through local synthetic RTSP.

**Status: research complete with explicit unmet external gates.** The final
choice is a documented reference recipe and validation toolkit. Native buffering
plus a small application output check was sufficient for the tested contract.
A production RTSP framework and package publication remain out of scope.
The source and documentation are MIT licensed; see the
[release-readiness report](docs/release/PUBLIC_RELEASE_READINESS.md).

Start with [the 75-minute learning plan](docs/guides/START_HERE.md) or
[the 10–15-minute demonstration](docs/guides/DEMO_RUNBOOK.md).

## What the experiments found

| Evidence environment | Measured finding | Limit |
| --- | --- | --- |
| Deterministic simulation | Slow FIFO: 10 results, max age 310 virtual ms, 8 violations at 80 ms budget. Latest: 4 results, 6 replacements, max 70 ms, 0 violations | Virtual source/workload timing, not camera latency |
| Real Python threads | Controlled slow handoff delivers first/last of 10 items, replaces 8 and terminates both workers | Event-coordinated behavior, not throughput measurement |
| Source-stamped OpenCV images | 1000/1000 trace matches over ten configurations; source marker survives selected color/PNG path | Arbitrary transforms and JPEG RTSP pixel lineage unverified |
| Mature local RTSP contract | Corrected 1200/1200, 100/configuration; 400 explicit recoveries; filtered modes reject all 400 obsolete completions | Actual JPEG/RTP/TCP/decode; application epochs, not physical source freshness |
| Controlled TCP delivery faults | 720/720, 20/configuration; delay/stall/cuts and bounded recovery/shutdown | Owned localhost fixture; no UDP packet loss or real-network rate |
| Independent FrameGrab file audit | Final 800/800, 100/scenario; native supported behavior confirmed, no freshness defect observed | FFV1/FFmpeg path; external RTSP blocked by audit OpenCV build; no adoption claim |

Each row has its own denominator. Initial failures remain in the reports: one
server teardown failure in the first 400 mature RTSP controls, and one immediate
native-task remainder in the first 100 external controls. Corrections/new
observation boundaries precede separately declared successful cohorts.

## Install and run the Python core

Python 3.11+; recorded Fedora development uses Python 3.12.15. From this checkout:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: pip==26.2.1
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m video_freshness_lab
.venv/bin/python -m video_freshness_lab --scenario reconnect --policy latest --session-filter
.venv/bin/python -m video_freshness_lab.threaded_demo --mode slow
```

If .venv already exists, use it. The core has no runtime dependency beyond the
standard library. Initial installation requires an approved package index/cache.
A fresh checkout needs owner-provided local original PRDs before changing
requirements-dependent implementation; they are deliberately absent from Git.

The simulator supports --suite buffering/recovery/all and --json. Its processing
ages are virtual milliseconds. The threaded demo supports --mode normal/slow/idle.
Source closure drains the final waiting item; it does not invalidate an epoch.

## Tests and CI

```sh
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
git diff --check
git diff --cached --check
```

**305 Python-only tests pass**, retaining the original 275. GitHub
[CI](https://github.com/devAIsh88/video-freshness-lab/actions/workflows/ci.yml)
installs the editable dev extra, runs Ruff and pytest on Ubuntu Python 3.11 and
3.12. The verified Stage 6 delivery passed both jobs in
[run 39842507560](https://github.com/devAIsh88/video-freshness-lab/actions/runs/39842507560).
The subsequent research handover also passed both jobs in
[run 39844877466](https://github.com/devAIsh88/video-freshness-lab/actions/runs/39844877466).
Release-preparation checks are recorded separately in the release-readiness report.
Workflow permissions are read-only, actions pinned to full SHAs, with no CD,
publication, releases, secrets or deployment. Optional media tests do not run in CI.

## Optional synthetic images and native media

Existing isolated images environment:

```sh
venv-media/bin/python -m video_freshness_lab.stamped_images --repeat 1 > /tmp/vfl-images-demo.json
venv-media/bin/python -m unittest discover -s integration -p test_stamped_images.py -v
```

If absent, create it with `.venv/bin/python -m venv venv-media` then
`venv-media/bin/python -m pip install --only-binary=:all: pip==26.2.1` and
`venv-media/bin/python -m pip install -e '.[images]'`. This optional extra pins
NumPy 2.2.6 and opencv-python-headless 4.12.0.88; it does not change system Python.
Use a supported, patched pip in each environment (26.2.1 was checked here).
Native dependency licenses and binary notices are summarized in the
[third-party review](docs/release/THIRD_PARTY_LICENSE_REVIEW.md).

The existing Fedora system interpreter supplies GI, GStreamer and GstRtspServer.
Verify these prerequisites; missing bindings are a blocker, not a reason to
repeat host installations from an isolated execution environment.

```sh
rpm -q gstreamer1-rtsp-server
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_gstreamer_native.py -v
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_rtsp_transport.py -v
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_transport_faults.py -v
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.rtsp_experiment --repeat 1 > /tmp/vfl-rtsp-demo.json
```

The optional tests use generated inputs and owned IPv4 loopback listeners only.
They verify finite teardown and listener release. Fedora integration results are
separate from Python CI. The independent consumer audit uses a reviewed disposable
environment outside the repo; see its report rather than adding its dependencies
to the core. Exact tested demonstration and reliability commands are in the runbook.

## Architecture and documentation

Controlled source → waiting buffer → acquired processing with original immutable
evidence → locked final epoch check → in-memory publication ledger. Pure diagnostics
report session, identity progression and supported ages without publishing.
Existing GStreamer owns native buffering; the lab adds finite tests and the
application boundary policy. [Code guide and Mermaid diagram](docs/guides/CODEBASE_GUIDE.md).

| Read for | Document |
| --- | --- |
| Guided learning | [START_HERE](docs/guides/START_HERE.md) |
| Concepts and original stages | [Project walkthrough](docs/guides/PROJECT_WALKTHROUGH.md) |
| Actual modules/classes/tests | [Codebase guide](docs/guides/CODEBASE_GUIDE.md) |
| Tested Fedora demos and cleanup | [Demo runbook](docs/guides/DEMO_RUNBOOK.md) |
| Presentation and 20 technical questions | [Explanation Q&A](docs/guides/PROJECT_EXPLANATION_QA.md) |
| Consolidated measured evidence | [Final research report](docs/experiments/FINAL_RESEARCH_REPORT.md) |
| Original requirement history | [PRD matrix](docs/audits/PRD_IMPLEMENTATION_MATRIX.md), [technical completion](docs/audits/TECHNICAL_STAGE_COMPLETION_REPORT.md) |
| Independent target and honest findings | [Third-party audit](docs/audits/THIRD_PARTY_CONSUMER_AUDIT.md) |
| Every gate and final outcome | [Final compliance](docs/audits/FINAL_PRD_COMPLIANCE.md), [go/no-go decision](docs/audits/FINAL_GO_NO_GO_DECISION.md) |
| Timestamp/identity rules | [Evidence contract](docs/architecture/frame-evidence-contract.md) |
| Documented versus verified library behavior | [Capability matrix](docs/research/existing-library-capability-matrix.md) |

## Supported scope and limitations

The Python core is tested locally on Fedora 44/Python 3.12 and in Ubuntu
Python 3.11/3.12 CI. Windows remains an unverified PRD target. Native harnesses
are Fedora/Linux experiments using explicitly recorded versions. Direct tool/image
dependencies are pinned; transitive dependencies are not globally locked.

Local receipt time, decoder PTS, source capture time, source epoch, connection
generation and application epoch are distinct. Unavailable physical capture age
and source-head lag remain UNKNOWN. No physical cameras, public-network faults,
UDP impairment, H.264/GOP recovery, safety certification, production readiness or
broad community adoption is claimed. Complete low-burden semantic instrumentation
and package advantage over a short pytest/FFmpeg recipe remain unproven.

## License and contribution status

Released under the [MIT License](LICENSE).
Copyright (c) 2026 devAIsh88. Third-party dependencies retain their own licenses;
see the [license review](docs/release/THIRD_PARTY_LICENSE_REVIEW.md).
The original private PRDs are excluded from this release.

[Contribution guidance](CONTRIBUTING.md) covers small, evidence-backed fixes and
[security reporting](SECURITY.md) covers sensitive findings. Source publication
does not establish adoption, physical-camera guarantees or package readiness.
No package publication, paid infrastructure or deployment is authorized.
