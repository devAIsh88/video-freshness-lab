# Finite localhost RTSP testbed

Milestone 1.8 reuses the installed GstRTSPServer library; it does not implement
an RTSP protocol server. The owner authorized this finite loopback experiment
on 2026-10-21. Stop after 1.8. No external endpoint, camera, production reader,
reliability package or Milestone 1.9 work is authorized.

The original PRDs remain unchanged and untracked. Their broader stage gates and
[foundation differences](foundation.md) remain in force. The earlier untracked
1.8 drafts recorded an unavailable server on 2026-10-20; fresh checks now resolve
that prerequisite. Historical negative results remain in the results report.

## Existing dependencies and execution environment

Before adoption, RPM metadata and live introspection established:

| Component | Installed version | Purpose | License / source |
| --- | --- | --- | --- |
| gstreamer1-rtsp-server | 1.28.8-1.fc44 | Existing RTSP server and typelib | LGPL-2.0-or-later AND LGPL-2.1-only; official installed Fedora RPM |
| gstreamer1 / plugins-base | 1.28.8-1.fc44 | Pipeline, source, valve, appsink | LGPL-2.1-or-later; official installed Fedora RPMs |
| gstreamer1-plugins-good | 1.28.6-1.fc44 | JPEG, RTP, rtspsrc | Fedora expression: CC0-1.0 AND GPL-2.0-only AND LGPL-2.0-only AND LGPL-2.0-or-later AND LGPL-2.1-only AND LGPL-2.1-or-later AND xlock AND MIT AND BSD-3-Clause AND CC-BY-3.0 |
| python3-gobject-base | 3.56.3-1.fc44 | System GI bindings | LGPL-2.1-or-later; official installed Fedora RPM |

Sources: installed RPM metadata, [Fedora server package](https://packages.fedoraproject.org/pkgs/gstreamer1-rtsp-server/gstreamer1-rtsp-server/)
and [GStreamer project](https://gstreamer.freedesktop.org/). License expressions
identify external components; repository licensing remains pending. Nothing was
installed or downloaded for the native experiment. No dependency was added to
pyproject.toml. The existing editable project installation was verified separately.

The executor sees Fedora 44, `/usr/bin/python3` 3.14.7, the server RPM, a loadable
`libgstrtspserver-1.0.so.0`, and
`/usr/lib64/girepository-1.0/GstRtspServer-1.0.typelib`. The system interpreter
imports GstRtspServer 1.0 and exposes RTSPServer. Project tests use the existing
Python 3.12.15 venv; its GI availability is not assumed. Socket creation is denied
inside the restricted sandbox; approved outside-sandbox loopback execution works.

## Source, transport and application boundaries

The runner has no host/URL argument. The library server binds **127.0.0.1** with
service **0** and reports its actual bound port over an owned multiprocessing
pipe after attachment. The library's configured address is checked; accepted
client addresses must be IPv4 loopback. Each server's exact port must return
connection refused after its process has exited. Temporary ports are not stored
in committed reports.

Server factory, shared for its one owned client:

```text
videotestsrc is-live=true num-buffers=100 pattern=smpte
→ video/x-raw,format=I420,width=320,height=240,framerate=10/1
→ valve drop=false → jpegenc → rtpjpegpay name=pay0 pt=26
```

The valve implements the acknowledged source stall and introduces no queue.
A source pad counts production for the controlled slowdown phase; this is not
encoded frame lineage or a capture timestamp. Every trial stops its owned source
before or at the finite limit; success does not require all 100 buffers or EOS.

Client:

```text
rtspsrc protocols=tcp latency=50 drop-on-latency=false tcp-timeout=2000000
→ application/x-rtp,media=video,encoding-name=JPEG
→ rtpjpegdepay → jpegdec → appsink
```

UDP is disabled. Negotiated RTP caps record JPEG and the 90000-Hz clock; decoded
caps record the raw frame format. Runtime plugin versions and rtspsrc's actual
buffer-mode/retransmission properties are saved per client. JPEG is intra-frame;
no H.264/GOP conclusions follow. Server shutdown is an owned process exit, not
packet loss, a physical source restart, or a network partition.

A/B use native FIFO/downstream-leaky appsink respectively. C/D use identical
settings with the existing small PublicationLedger final-output epoch check.
Appsink: max-buffers=2, max-bytes=max-time=0, leaky-type=none/downstream,
sync=false, async=false, emit-signals=true, enable-last-sample=false,
wait-on-eos=false. No application queue or appsrc is inserted. Native internal
RTSP/jitterbuffer/decoder buffering still exists and is not attributed to appsink.
Mailbox code and its drain-on-close contract are unchanged.

## Evidence, clocks and epochs

The server, client and report boundaries remain separate. `rtsp_contract.py`
provides pure receipt sidecars and validated experiment configuration;
`rtsp_experiment.py` owns optional native execution. Integration lives outside
pytest's configured `tests` directory. Ordinary tests import no GI.

The decoder-output/appsink-ingress pad records buffer PTS, a local observation
ordinal, and local monotonic time before appsink queue insertion. A receipt is
associated only when that PTS has exactly one pad observation in the current
connection. This is a local buffer association; ambiguous PTS fails the trial.
It is not a source-frame or RTP-to-frame identity claim. Acquired receipt ordinals
are explicitly local deliveries. PTS must advance within each observed connection;
a new connection creates a separate PTS domain. No cross-connection PTS comparison.

The depayloader sink probe maps RTP headers and records sequence, timestamp,
SSRC and marker with local observation time. Frames can span multiple packets;
no packet-to-frame correspondence is asserted. Native jitterbuffer stats are
sampled where available; decoder loss and source sequence lag remain unknown.

Receipt, processing start, final decision, controller action, pad observation,
NULL request/completion and read entry/return use the client process monotonic
clock. Server acknowledgments retain their own labeled monotonic domain; no
server/client timestamp subtraction is used. Arrival age is decision minus
receipt; processing delay is decision minus start; pad-to-receipt includes
native waiting. None is capture age. Capture timestamp, physical source epoch,
codec-surviving source identity and capture freshness remain UNKNOWN/null.

Each explicit client open has a connection generation (0, then 1 only during
reconnect). The controller independently activates a logical application output
epoch. Acquisition tags a frozen sidecar with that declared epoch; it never
retags held work. Logical epoch checks are meaningful only for that application
policy. They do not authenticate a new physical camera session. Ledger validation
and output recording occur under one lock; there is no external output sink.
Closing a source or client alone does not activate an epoch.

## Declared trial schedule and budgets

Five repetitions of each of six scenarios × two native policies × filter on/off
= **120 trials**. Normal controls precede faults. No per-trial retry. Budgets were
selected in the approved draft: 30-second outer process-group watchdog; five
seconds for startup/next sample/source phase; three seconds for observed fault
symptoms, NULL state and joins. A reconnect has exactly two client opens total,
with no repeated connection attempt. Budgets prevent hangs, not freshness SLAs.

| Scenario | Controlled event order and acceptance |
| --- | --- |
| normal | Receive and complete four samples, advancing decoder PTS, then owner stop |
| interruption | Acquire old sample; request/wait server exit and port refusal; observe later delivery and ERROR/EOS for up to three seconds; close client; finish held work without inventing a new epoch |
| reconnect | Same interruption; close old client; activate epoch 1; start new owned server on a new ephemeral port; explicitly open generation 1; receive/complete current work, then complete held epoch 0 |
| slow | Hold first acquired result; withhold further pulls until acknowledged source count ≥10; require FIFO insertion ≥3/ingress ≥4, or leaky insertion ≥8/ingress ≥4; snapshot, finish held result, acquire two more |
| blocked-read | Acknowledge valve stall; drain until a bounded 200-ms pull returns empty (five-second drain guard); register a five-second acquisition; observe no completion during a 100-ms window; request NULL; require empty wakeup and joined worker |
| epoch | Hold acquired work; activate application epoch 1 without reconnecting; finish old work; acquire/complete work tagged epoch 1 |

In slowdown, the source production boundary and client acquisition schedule are
shared, but reachable native insertion boundaries differ: FIFO blocks admission
when full while leaky keeps accepting. Source count ≥10 does not prove delivery
of ten frames. Scheduling differences are measured, never erased by retries.
The pending-read observation proves a call pending at the shutdown boundary;
it does not prove native code was blocked for an indefinite duration. The
100-ms window is an explicit observation window, not a unit-test sleep.

## Reporting and cleanup

Every raw trial reports receipts, RTP headers, decoder-pad observations, bus
ERROR/EOS domain/code and detection time, decisions, runtime settings, non-atomic
counter snapshots, cleanup and errors. Separate native drops from application
rejections. Undrained native work at owner stop is not classified as a drop or
rejection. Streaming snapshots are not global conservation or maximum-occupancy
proofs. Bus debug strings are omitted; native stderr stays in local raw artifacts.

A trial `finally` transitions clients to NULL, joins its application reader,
commands/waits every owned server, verifies exact-port refusal, and reports
remaining owned children/Python threads. Server stop fallback is terminate/join,
then kill/join; any fallback makes the trial fail. The outer supervisor starts a
new POSIX process group for each trial and kills/waits the group on timeout,
covering native calls and descendants. Linux/Fedora execution only is validated.

Reproduce from the repository root with the already installed system bindings:

```sh
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p 'test_rtsp_transport.py' -v
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.rtsp_experiment --repeat 5 > /tmp/vfl18-results.json
.venv/bin/python -m pytest -v
```

Missing bindings fail the explicit integration command. `PYTHONPATH=src` supplies
system-Python source access only; editable packaging is independently checked in
the project venv. The unchanged GitHub workflow runs Python-only tests on 3.11
and 3.12, with read-only permissions and no secrets, deployment or publishing.
See [observations and limitations](../experiments/milestone-1.8-results.md).
