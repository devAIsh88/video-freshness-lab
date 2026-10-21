# Milestone 1.9: controlled TCP delivery faults

Completed local validation on 2026-10-21. **PIVOT remains supported**: existing
native buffering plus a small final-output epoch check cover the declared
held-work policy. No independent application defect or package gap is established.
The later technical-stage master task extends authorization through original
Stage 5 only; no Stage 6 behavioral audit or product-release work starts here.

## Design and scope

See [the predeclared design](../architecture/transport-fault-injection.md) for
feasibility, tool assessment, bounds and exact criteria. Toxiproxy was documented
as an existing whole-stream TCP alternative before implementing the narrow relay;
it was not installed. The implemented fixture relay uses only stdlib sockets,
one worker, one retained record, fixed owned loopback destination, and at most
four sequential connections. No general proxy API, new buffering framework,
privileged network changes or UDP impairment exists.

RTSP/1.0 responses are parsed by bounded header/Content-Length framing; interleaved
RTP/RTCP are recognized only after TCP channel 0/1 negotiation. Client bytes pass
unchanged. Delay holds one complete media/control-channel record for 200 ms;
stall waits for an acknowledged release after native acquisition drains empty.
Control responses behind held media cannot overtake it: TCP head-of-line effects
are part of this experiment. A cut closes both connected relay sockets without
RTSP teardown. It is not a claimed TCP RESET, packet corruption or UDP loss.

All source media are finite synthetic SMPTE/JPEG, 320×240 I420 at 10 fps. Reuse the
unchanged 1.8 GstRTSPServer, Client, two-slot native FIFO/leaky appsink, immutable
receipt sidecar and PublicationLedger. Source remains alive across explicit
reopens to the same relay port. No producer pause supplies a 1.9 transport fault.
The server's valve is not operated in these scenarios.

Environment: Fedora 44; project Python 3.12.15; system Python 3.14.7 / PyGObject
3.56.3; GStreamer core/base/source/valve/appsink/server 1.28.8; JPEG/RTP/rtspsrc
plugins 1.28.6. Client TCP-only, latency 50 ms, drop-on-latency false, tcp-timeout
2,000,000 microseconds, native two-buffer FIFO/downstream-leaky queue, sync/async
false, wait-on-eos false. No native packages, system settings or project runtime
dependencies changed. A separately authorized image venv is not used here.

## Attempts, criteria and observed frequency

Final cohort: **720 trials**, nine scenarios × FIFO/leaky × filter off/on ×
20 repetitions/configuration. **720 completed and passed, zero failed,
zero timeout**. No per-trial retries. Before this cohort, the 36-case pilot and
37-case optional integration suite (36 controls plus intentional retained-media
abort cleanup) passed. Their measurements are not pooled into final distributions.

Pass criteria were recorded before execution: verified negotiation/media fault,
required local recovery or pending-read behavior, advancing within-connection
PTS, retained original sidecar at output, and complete cleanup within guards.
The watchdog regression is a separate simulated timeout path, not a natural
transport timeout or successful real cleanup. The final process-group forced-kill
path was not exercised by runtime trials. Baseline was rerun at 275 pure tests;
20 meaningful framing/config/watchdog regressions bring that suite to 295.

Zero failures among twenty trials per configuration characterizes this sample;
it is not a universal reliability claim or the later mature 100-repeat gate.
The [initial PRD audit](../audits/PRD_IMPLEMENTATION_MATRIX.md) explicitly identifies
that original Stage 5 gap and the missing stamped-image/repeated-content work.
A separate mature original-RTSP cohort is not pooled with this impairment cohort.
Its early cases overlapped the tail of this run on the same host; these descriptive
latencies are not isolated performance benchmarks.

## Scenarios actually executed

| Scenario | Layer | Trials | Result |
| --- | --- | ---: | --- |
| Baseline | Unimpaired relay transport | 80 | Four receipts per trial, all controls pass |
| Delay | Downstream transport hold | 80 | One interleaved record retained ≥200 ms, released, subsequent receipt |
| Abrupt close | Transport cut + application reopen | 80 | EOS observed; 80/80 explicit single-attempt recoveries |
| Stall | Downstream transport hold/release | 80 | Empty bounded acquisition before release, same-connection delivery resumes |
| Three disconnect cycles | Three cuts + explicit application epochs/reopens | 80 | 240/240 recoveries; four connections per trial |
| Slow consumer during cut | Application withholding + transport cut/reopen | 80 | Native policy comparison and 80/80 recoveries; held result crosses epoch |
| Shutdown with pending read | Transport stall + application NULL | 80 | Read observed pending, wakes empty during NULL, reader joins |
| Held-result epoch transition | Transport stall + application boundary | 80 | Old held result admitted by native-only control or rejected by final filter |
| Recovery after stall | Transport release, same connection | 80 | Three resumed receipts per trial; PTS advances |

The source/session/application meanings remain distinct. A successful explicit
reopen is not automatic rtspsrc recovery. RTSP Session header presence is observed;
raw session identifiers are not retained and physical-session identity is unknown.
An application epoch activation does not authenticate a physical source restart.

## Counts and continuity

Across final trials: **2,200 acquired = 2,200 processed = 1,960 published + 240
application epoch rejections**. Published includes **240 obsolete results**, all
from deliberately permissive native-only controls. All filtered counterparts
suppress the held obsolete work. These are final in-memory output decisions,
not an external device/network sink transaction.

Native appsink snapshots count **240 waiting drops**, all in slow leaky cases:
six per each of forty slow-leaky trials. FIFO waiting drops are zero. Native
waiting drops and application rejections apply to disjoint boundaries; no global
produced/acquired/lost conservation is asserted. Buffered/unpulled work abandoned
at transport/owner stop is not silently counted as a native drop or rejection.
Source-frame production identity, capture age and end-to-end loss are unavailable.

Within each connection, decoder PTS never regressed or repeated in acquired
samples. There are **480 observed gaps over the declared 150-ms diagnostic
threshold**, including **80 in normal baselines**. Thus gaps alone do not prove
transport loss or fault causation; native startup/scheduling/drops contribute.
PTS domains are separate after every explicit open and are never subtracted
across sessions. Source timestamp continuity remains UNKNOWN.

The [sanitized summary](milestone-1.9-summary.json) records every configuration,
raw report hash, counters, descriptive distributions and cleanup. Raw technical
reports stay under `/tmp/vfl19-results.json`; no media or raw RTSP/SDP bodies
are committed. Missing evidence fields are null/UNKNOWN, never fabricated zero.

## Timing distributions

All following differences use the **same trial process monotonic clock**, including
relay/controller/client. Server acknowledgments keep their own labeled clock;
no cross-process subtraction. Detection is cut application → first observed bus
EOS, including controller polling/drain. Recovery is explicit reopen request →
first new-generation receipt, excluding earlier detection/old-client close.
Resumption is release acknowledgment → next application receipt; it does not
establish packet-to-frame lineage or capture age.

| Observation | n | Min ms | Median ms | p95 ms | Max ms | Population SD ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Explicit connection recovery | 400 | 44.614 | 46.028 | 47.546 | 49.204 | 0.778 |
| Applied cut → observed EOS | 400 | 0.089 | 1.536 | 3.675 | 5.476 | 1.105 |
| Released stall → receipt | 240 | 0.634 | 0.776 | 1.150 | 2.024 | 0.185 |
| Configured 200-ms delay hold | 80 | 202.154 | 202.495 | 203.180 | 203.310 | 0.285 |
| Other released media stalls | 240 | 100.920 | 101.277 | 101.737 | 102.328 | 0.218 |
| NULL request → pending read return | 80 | 100.292 | 100.450 | 100.606 | 100.707 | 0.085 |
| NULL request → observed NULL, all scenarios | 1,120 | 0.398 | 0.511 | 100.857 | 101.606 | 25.854 |

Exact per-configuration values and sample sizes are in JSON. The roughly 100-ms
shutdown boundary under held media is observed behavior of this setup; it differs
from the unimpeded 1.8 teardown. It is not a universal shutdown SLA. The configured
200-ms delay's overshoot includes 10-ms select polling and scheduling. Timings are
not physical fault/capture times or a public-network benchmark.

## Cleanup, tests and reproduction

Final cohort: **1,120 client pipelines reached NULL; 720 servers exited code 0;
720 relay workers joined; zero remaining owned children/Python workers; zero
server/relay listener refusal failures; zero termination fallbacks; zero nonempty
native stderr reports**. Every exact owned listening port refused connections
after cleanup. No claim is made about unrelated host listeners or processes.
Cancellation cannot target another destination; it acts on the relay's own pair.

```sh
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
git diff --check
git diff --cached --check
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_transport_faults.py -v
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.transport_experiment --repeat 20 > /tmp/vfl19-results.json
.venv/bin/python -m video_freshness_lab --suite all --json
.venv/bin/python -m video_freshness_lab.threaded_demo --mode slow --items 10 --json
```

Actual local Python-only suite: **295 passing tests**, preserving all 275 baseline
cases. Framing tests cover arbitrary read fragmentation/coalescing, dollar bytes
inside control bodies, exact byte preservation, missing/unsupported channels,
length corruption, truncation, bounds and invalid configuration. The watchdog
regression verifies one launch, group kill and wait with explicit unavailable
cleanup evidence. Existing simulator/thread/CLI/import tests stay active.
Optional transport integration: **2 unittest methods, 37 native cases passed**.
These are separate from GitHub's ordinary Python-only CI. Editable installation,
Ruff lint/format, pip integrity and whitespace checks pass. Socket and GitHub
access initially failed in the sandbox; approved execution succeeded without
system/network-policy changes. Cache warnings are nonfatal.

## Security and decision

Staged files/full diff, tracked and proposed content, ignored inventory, original
PRD hashes, every DOCX member, and all history to push are reviewed. No private
keys, token forms, credential URLs, private connection data, external RTSP
endpoints, real recordings or binary artifacts are selected. The scan is bounded
and cannot certify absence of every possible secret. Both PRDs remain unchanged,
untracked and absent from pushed history. Native bodies/SDP sender identifiers
never enter the sanitized summary. Temporary artifacts and environments stay
ignored/outside Git. Private ownership/account/main baseline were checked.
No licensing, deployment, CI permissions, paid usage or public visibility change.

One coherent milestone commit is authorized after verification:
`test: evaluate RTSP transport fault recovery`. Exact SHA, push and completed
Python 3.11/3.12 CI verification are recorded after delivery, without a status-only
commit or history amendment. Foundation history is preserved.

**Recommendation: PIVOT.** Keep a tested native configuration and small output
check. Local faults do not justify a new reliability package. Remaining independent
camera requirements include trustworthy capture semantics/clock uncertainty,
source identity surviving the actual codec, physical-session boundaries, UDP and
real-network fault scope, independent consumer reproduction, minimal adapter burden,
and maintainer/adoption evidence. Newer authorized technical work addresses only
stamped synthetic images and missing mature RTSP evidence; Stage 6/7 remain out
of this execution's scope.

Previous optional suites were also rerun successfully: 1.7 native buffering/EOS/
failure controls (3 unittest methods, 30 cases) and 1.8 RTSP/cleanup controls
(3 methods, 26 cases). They remain distinct from the 720-trial cohort and CI.
