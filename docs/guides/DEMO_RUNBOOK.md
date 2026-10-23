# Fedora demonstration runbook

Commands below were executed successfully during the final handover on the
existing Fedora 44 checkout. Use the project root. The quick path takes about
10–15 minutes including explanation; the experiments themselves are shorter.
All data is synthetic. Files written below are JSON/text under /tmp.

## Prerequisites

The current checkout has Python 3.12.15 in .venv, an optional venv-media with
NumPy 2.2.6/headless OpenCV 4.12.0.88, and Fedora system GI/GStreamer bindings.
The system interpreter is /usr/bin/python3 (3.14.7 in the recorded environment).
The ordinary venv intentionally does not import GI or OpenCV.

```sh
cd /home/missy/projects/rtsp_camera
.venv/bin/python --version
.venv/bin/python -m pip check
rpm -q gstreamer1-rtsp-server
/usr/bin/python3 - <<'PY'
import gi
gi.require_version('GstRtspServer', '1.0')
from gi.repository import GstRtspServer
print('GstRtspServer import:', bool(GstRtspServer.RTSPServer))
PY
venv-media/bin/python -m pip check
```

Observed server package: gstreamer1-rtsp-server-1.28.8-1.fc44.x86_64. The import
succeeds in this execution environment, which now sees the Fedora installation.
If optional prerequisites are absent, run the pure path and report that native
portion unavailable. Do not repeat host installations to fix a different sandbox.
Loopback integration needs permission to bind owned IPv4 localhost sockets.

For a fresh checkout, owner-provided original PRDs are required before changing
requirements-dependent implementation. Standard Python-only installation is:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

Optional image setup, when needed, is the existing documented isolated extra:

```sh
.venv/bin/python -m venv venv-media
venv-media/bin/python -m pip install -e '.[images]'
```

These setup commands use trusted pinned direct dependencies and require package
index access. Do not run them to overwrite an already working demonstration env.
The independent audit has a separate reviewed setup in its report; it is not a
last-minute prerequisite for the core demonstration.

## Quick path: 10–15 minutes

### 1. FIFO versus latest, approximately two minutes

```sh
.venv/bin/python -m video_freshness_lab
.venv/bin/python -m video_freshness_lab --suite all --json > /tmp/vfl-final-simulation.json
```

Point to slowdown-fifo: ten consumed frames, 310 virtual ms maximum result age,
eight result violations at the scenario's 80 ms budget. slowdown-latest processes
four frames, replaces six waiting frames and reaches 70 virtual ms with no budget
violation. These injected times are deterministic model values, not camera latency.
A passing latest case depends on its workload and chosen budget.

### 2. Real threads, approximately two minutes

```sh
.venv/bin/python -m video_freshness_lab.threaded_demo --mode normal
.venv/bin/python -m video_freshness_lab.threaded_demo --mode slow
.venv/bin/python -m video_freshness_lab.threaded_demo --mode idle
```

Normal delivers ten. Slow delivers epoch-0/frame-0 and epoch-0/frame-9, replaces
eight, and reports both workers terminated. Idle wakes an empty blocked consumer
through close. Explicit coordination establishes counts; no arbitrary sleep is
used as the correctness oracle.

### 3. Session filtering and faults, approximately two minutes

```sh
.venv/bin/python -m video_freshness_lab --scenario reconnect --policy latest
.venv/bin/python -m video_freshness_lab --scenario reconnect --policy latest --session-filter
.venv/bin/python -m pytest tests/test_threaded_sessions.py tests/test_recovery.py tests/test_evidence.py -v
```

Without the filter the model emits two obsolete outputs even though its age
budget passes. Filtering rejects two and publishes zero obsolete outputs. The
focused 158-test suite covers held work, legal lock order, no-data freeze,
restart/recovery, unknown clocks and shutdown. This is a logical application epoch.

### 4. Actual stamped images, approximately two minutes

```sh
venv-media/bin/python -m video_freshness_lab.stamped_images --repeat 1 > /tmp/vfl-final-images-demo.json
venv-media/bin/python -m unittest discover -s integration -p test_stamped_images.py -v
```

Ten image configurations have zero trace mismatches. The JSON includes repeated
content and static-scene controls. Markers originate before admission and survive
the selected color/PNG path; separate arrays repeating the same old stamp do not
become new source evidence. Six optional test methods pass. No display/GPU needed.

### 5. Native buffering and local RTSP, approximately three minutes

```sh
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.gstreamer_experiment --repeat 1 > /tmp/vfl-final-native-demo.json
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.rtsp_experiment --repeat 1 > /tmp/vfl-final-rtsp-demo.json
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.transport_experiment --scenario stall --repeat 1 > /tmp/vfl-final-fault-demo.json
```

Observed: 24/24 native cases, 24/24 RTSP cases and 4/4 stall cases pass. Native
queue/drop counters separate replacement from application rejection. RTSP runs
normal/interruption/reconnect/slow/blocked-read/epoch for four queue/filter modes.
It exercises JPEG encoding, RTP/TCP transport, decoding and the receipt-to-output
contract. The stall command holds framed media delivery in the owned loopback
relay; it is not UDP packet loss or physical capture freeze.

Inspect the small output summaries:

```sh
.venv/bin/python - <<'PY'
import json
from pathlib import Path
for name in ('native', 'rtsp', 'fault'):
    data = json.loads(Path(f'/tmp/vfl-final-{name}-demo.json').read_text())
    rows = data.get('cases', data.get('results', []))
    print(name, len(rows), 'cases;', sum(r['status'] != 'ok' for r in rows), 'failed')
PY
```

Finish with the decision and limitations: native buffering plus a final output
check is enough for the tested logical contract; capture freshness is UNKNOWN.

## Full verification and separate optional suites

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

Default pytest: 305 passed. Optional suites: native 3 methods/30 cases; RTSP
3/26; transport 2/37; images six methods. Normal GitHub CI runs only the ordinary
Python suite and Ruff/install steps, not these multimedia experiments.

## Reliability reproduction, beyond the quick demo

```sh
venv-media/bin/python -m video_freshness_lab.stamped_images --repeat 100 > /tmp/vfl-images-repeat.json
PYTHONPATH=src /usr/bin/python3 integration/repeat_rtsp_contract.py --repeat 100 > /tmp/vfl-stage5-repeat.json
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.transport_experiment --repeat 20 > /tmp/vfl-fault-repeat.json
```

These may take several minutes. The declared historical cohorts were respectively
1000/1000 image trace matches, 1200/1200 corrected mature RTSP trials and 720/720
fault trials. Re-running creates new observations; preserve any failure rather
than retrying it until green. See the individual reports for predeclared criteria,
settings, timing definitions and the retained initial failed cohorts.

The reviewed disposable FrameGrab environment can also execute:

```sh
PYTHONPATH=src /tmp/vfl-framegrab-env/bin/python integration/audit_framegrab.py --repeat 1 > /tmp/vfl-framegrab-demo.json
```

It is optional, needs that separately reviewed environment and uses synthetic
local files only. The full external audit is 100 trials per eight scenarios.
See [exact setup and constraints](../audits/THIRD_PARTY_CONSUMER_AUDIT.md).

## Cleanup and failure handling

Each finite native invocation owns its workers, child processes, pipelines and
listener ports. Normal completion asserts pipeline NULL, worker/process exit and
port closure; RTSP also requires positive media/session-pool cleanup evidence.
The independent file audit releases captures, checks task remainders, deletes
TemporaryDirectory media and reaps its worker. Native process watchdogs are hang
guards; a watchdog/fallback is a failed observation, not a successful cleanup.

Let finite commands finish. If a process is externally interrupted, preserve its
output and inspect that invocation's owned PIDs/ports before another run; never
use a broad process-kill command against unrelated applications. No persistent
service, firewall rule, network namespace or privileged network change is created.
The /tmp JSON outputs may be removed when no longer needed. Keep failed raw logs
locally if investigating; generated media and environments do not enter Git.
