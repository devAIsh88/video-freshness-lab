# Milestone 1.8: local RTSP transport and recovery

**Completed finite localhost validation, 2026-10-21. Decision: retain the recipe /
PIVOT; capture freshness remains UNKNOWN.** This experiment validates owned
synthetic JPEG/RTSP transport, explicit application recovery, shutdown, native
buffering and application output-epoch controls. It establishes no external
consumer defect or need for a standalone reliability package. Stop after 1.8.

## Implementation and prerequisite verification

The [testbed architecture](../architecture/local-rtsp-testbed.md) records exact
pipelines, dependencies, event boundaries and predeclared guards. New optional
`rtsp_experiment` code wraps the existing GstRTSPServer, GStreamer client,
finite source, controller and isolated report collection. Pure `rtsp_contract`
helpers provide validated configuration and frozen receipt sidecars. The existing
PublicationLedger supplies final-output epoch validation under one lock.
No new queue framework or RTSP protocol implementation was built.

Fresh checks from this executor:

| Check | Result |
| --- | --- |
| `rpm -q gstreamer1-rtsp-server` | `gstreamer1-rtsp-server-1.28.8-1.fc44.x86_64` |
| Native library | `ctypes.util.find_library` resolves `libgstrtspserver-1.0.so.0`; `ctypes.CDLL` loads it |
| Typelib | RPM lists and filesystem confirms `/usr/lib64/girepository-1.0/GstRtspServer-1.0.typelib` |
| `/usr/bin/python3` | 3.14.7; imports GstRtspServer 1.0 and exposes RTSPServer |
| Operating system | Fedora Linux 44 Workstation; this executor sees the reported Fedora installation |
| Loopback | Restricted socket creation fails with PermissionError; approved outside-sandbox execution succeeds |

Core/base/source/valve/appsink are **1.28.8**; JPEG/RTP/rtspsrc plugins are
**1.28.6**; PyGObject is **3.56.3**. The project venv is **Python 3.12.15**.
No native packages, venv GI bindings, system configuration or dependencies were
added. The owner had already installed the server RPM.

The previous untracked drafts' 2026-10-20 missing-package/library/typelib and
failed-import findings are historical. They recorded zero RTSP trials, no
success commit and 265 passing regressions. The new observations clear that
specific environment gate; no substitute installation was attempted.

## Executed evidence and attempt accounting

Final declared batch: **120 trials = six scenarios × FIFO/leaky × filter off/on
× five repetitions**. **120 passed, zero failed**, no hidden per-trial retries,
no watchdog expirations. Five repetitions per configuration do not meet the
PRDs' mature 100-repetition gate. Zero observed unexplained failures is a sample
result, not a general reliability guarantee.

The [sanitized machine-readable summary](milestone-1.8-summary.json) retains
per-configuration receipt/drop/rejection counts, timing distributions, cleanup
and the raw batch SHA-256. Local raw reports remain in `/tmp/vfl18-results.json`;
no media, raw diagnostics or sender identifiers enter Git. Summary fields were
computed from actual reports; no missing measurement was replaced with zero.

Development and earlier attempts are separate:

- Six initial controls (one normal, five faults) passed.
- First integration suite: 24 configurations plus one intentional processing
  failure/cleanup control passed (two unittest methods).
- First measurement launcher failed **20 normal controls before RTSP startup**:
  CLI execution used `__main__` as the child module name. That batch was retained
  locally, the importable module name corrected, and a pure regression test added.
  These are harness failures, excluded from transport-success/flake denominators.
- The corrected pre-review batch passed **120/120**. Review then limited recorded
  SDP caps to four media fields and made NULL cleanup unconditional if snapshot
  collection raises. Earlier timings were not pooled with final results.
- Final integration suite: **24 configurations plus two intentional failure
  controls**, all passed (three unittest methods). The second failure control
  proves snapshot collection cannot prevent the NULL transition.
- The final 120-trial batch below used the reviewed implementation. No failed
  runtime trial was silently retried or removed.

## Transport observations

All final trials negotiated synthetic **320×240 I420, 10 fps**, RTP JPEG payload
26 / 90000-Hz RTP clock, with rtspsrc restricted to interleaved TCP. The depayloader
probe collected **2394 RTP packet observations** over 140 connections. These are
packet headers, not source-frame identities. Observed jitterbuffer loss counters
were zero at sampled boundaries; decoder loss and source loss remain unknown.

| Scenario | Trials | Actual observation |
| --- | ---: | --- |
| Normal | 20 | Four receipts/decisions each; PTS advanced within each connection; appsink drops zero |
| Interruption | 20 | Server stop/exit and exact-port refusal confirmed; EOS observed; zero additional receipts in the declared post-exit observation window |
| Explicit reconnect | 20 | Old client closed; new owned server and generation-1 client opened exactly once; new receipt accepted; held epoch-0 result completed after activation |
| Slow consumer | 20 | FIFO retained local decoder ordinals 0,1,2 and dropped zero; leaky delivered 0,7,8 and counted six native waiting drops per trial |
| Blocked read | 20 | Valve stall acknowledged, native pending samples drained, a five-second acquisition remained pending during the observation window; NULL woke it empty and worker joined |
| Output epoch | 20 | Held epoch-0 receipt completed after controller activation of epoch 1; a subsequent receipt was tagged with the new application epoch |

In both reconnect and output-epoch scenarios, native-only FIFO **and** leaky
published one held obsolete result per trial. With final epoch filtering, each
rejected exactly that one old result and published the current application-epoch
result. Thus all 20 filtered epoch/reconnect trials rejected old held work;
all 20 native-only counterparts admitted it. The source alias is a fixture alias,
and the epoch is a declared **application output policy**, not authenticated
physical-source identity. Same-connection epoch tagging cannot identify old
source frames already buffered before receipt.

Interruption does not activate an epoch. Its held work can complete under either
filter setting, consistent with preserving closure separately from invalidation.
No additional receipts after the prompt stop is a scoped negative result: this
schedule does not prove native queues always empty after disconnect. Reconnection
here is explicit client recreation to a newly bound fixture port; it is not a
measurement of automatic native reconnect, same-URL recovery, camera restart,
UDP recovery, packet loss, or network partition behavior.

Local elapsed observations from the final batch (min / median / max, milliseconds):

| Boundary | n | Observed ms |
| --- | ---: | --- |
| Slow FIFO, waiting decoder-pad → receipt | 20 | 601.600 / 656.499 / 710.774 |
| Slow leaky, waiting decoder-pad → receipt | 20 | 0.942 / 56.349 / 111.162 |
| Slow FIFO, held receipt → decision | 10 | 916.929 / 924.743 / 926.416 |
| Slow leaky, held receipt → decision | 10 | 916.393 / 923.090 / 927.046 |
| Interruption, observed server exit → end of symptom observation | 20 | 1.471 / 1.527 / 1.922 |
| Reconnect interruption, same boundary | 20 | 1.439 / 1.517 / 2.057 |
| NULL request → pending read return | 20 | 0.549 / 0.742 / 1.857 |
| NULL request → observed NULL | 140 | 0.449 / 0.781 / 2.344 |
| Server stop request → observed process exit | 140 | 18.386 / 25.767 / 37.277 |

These are observations under this controller schedule, not freshness budgets or
portable performance guarantees. The symptom endpoint includes parent polling;
it is not physical fault time. FIFO/leaky phases share the source count ≥10
boundary and withheld pulls but reach different native insertion boundaries.
Snapshots are non-atomic and sampling times differ. No global conservation,
source frame loss, maximum queue occupancy or source sequence lag is inferred.
The held result ages similarly with either native policy because appsink can
replace waiting buffers only; it cannot retract acquired application work.

All **140 client pipelines reached NULL**, all **140 server processes exited
with code 0**, and every exact fixture port refused connection afterward.
Remaining owned children/Python workers: **zero**. Termination fallbacks,
watchdog timeouts and nonempty native stderr: **zero** in the final batch.
The child/group watchdog is a hang safeguard; the final batch did not exercise
its forced-kill path. This is no claim about unrelated host processes/listeners.

## Commands and quality results

```sh
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
git diff --check
git diff --cached --check
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_rtsp_transport.py -v
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.rtsp_experiment --repeat 5 > /tmp/vfl18-results.json
```

The editable install initially failed because sandbox DNS could not reach PyPI
for the pinned build backend. The approved outside-sandbox rerun succeeded.
Ruff lint/format pass for **30 Python files**. **275 Python-only pytest tests
pass** (265 preserved plus 10 new pure cases). Pip reports no broken requirements;
its cache-directory warning is nonfatal. Working/staged whitespace checks pass.
The final explicit integration suite and repeated transport batch pass separately;
they do not run in GitHub CI. Windows and other native runtime versions remain
unverified. The existing 1.7 native suite was not rerun in this milestone.

Resolved project tools: pytest 8.4.2, Ruff 0.14.0, pip 26.2.1, iniconfig 2.3.1,
packaging 26.3, pluggy 1.6.0, Pygments 2.21.0; editable video-freshness-lab 0.0.0.
Direct pins and runtime dependency list are unchanged; transitives are not locked.

## Security, delivery and decision

Review includes tracked/proposed content, ignored-file inventory, all existing
history blobs, staged filenames/full diff, original PRD hashes and every member
of the DOCX container. Pattern checks cover private keys, GitHub/AWS token forms,
URL credentials, private IPv4 connection data and non-loopback RTSP endpoints.
No matches were found; this bounded scan is not a certification. Ignored content
consists of local environments, caches, generated bytecode and editable metadata;
none is staged. Temporary raw measurements remain outside the repository.

Original PRDs remain unchanged, untracked and absent from history. Foundation
commit `6ff7cb3f7aec0ee50175b22f85d0ad8642d052d0` remains intact. Existing mailbox,
simulator and publication contracts are preserved. No deployment, publishing,
license choice, external stream, credentials, paid service or CI expansion was
introduced. GitHub identity/ownership/private visibility/main branch were checked
before reuse; the existing read-only Python 3.11/3.12 workflow is unchanged.
Existing owner Actions spending controls remain an owner setting; none was enabled
or changed here.

Delivery follows the authorized single commit message:
`test: validate local RTSP transport and recovery behavior`.
The exact commit/push/remote SHA and completed two-version CI results are reported
after delivery, outside this pre-commit evidence snapshot. Prior 1.7 CI is never
presented as 1.8 evidence.

**PIVOT / recipe remains supported.** Configured native buffering plus the small
application final-output check cover the declared held-work contract. This is a
controlled application demonstration, not an independent consumer audit or a
standalone-package gap. Capture freshness, true source-session detection,
codec-surviving identity, external/adoption evidence and mature per-configuration
repeatability remain open. Milestone 1.9 has not begun.
