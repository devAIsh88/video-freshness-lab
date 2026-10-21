# Fixture-only TCP transport fault injection

## Feasibility decision and existing tools (before implementation)

Actual baseline is `f7952a42e7d59e4b83d1fe6c7f9bb5c6c9b7ba7c`; only the
owner-provided original PRDs were untracked. They were read and remain unchanged.
The owner's current request authorizes 1.9 beyond AGENTS.md's historical 1.8
stop. The PIVOT decision and mailbox drain-on-close semantics remain intact.

Official [Toxiproxy documentation](https://github.com/Shopify/toxiproxy), reviewed
2026-10-21, offers directional TCP latency, timeout and connection interruption.
It is a useful existing option for whole-stream impairment with less application
code. It is not installed here. Its documented stream-level toxics do not by
themselves identify RTSP responses versus interleaved RTP/RTCP; a framing-aware
boundary acknowledgment would still need instrumentation. No binary is downloaded
or dependency adopted. Installed socat is a byte relay, not the required
acknowledged RTSP-media fault controller. Neither tool was executed or audited.

**Feasible, with a narrow fixture relay.** Use standard-library sockets, one
bounded I/O worker and a limited RTSP/1.0 downstream framer. Fixed target is the
owned GstRtspServer at 127.0.0.1; listener is 127.0.0.1 on an ephemeral port. No
host/URL configuration, discovery, forwarding API, privileged operation, firewall,
namespace, external traffic or UDP support. At most four sequential connections
per trial. This is test scaffolding, not a general-purpose networking proxy.

The framing reference is [RFC 2326 section 10.12](https://www.rfc-editor.org/rfc/rfc2326#section-10.12):
interleaved records use a dollar prefix, channel and 16-bit length. This historical
RTSP/1.0 reference matches the tested fixture; no RTSP/2.0 conformance is claimed.
The downstream parser must respect RTSP Content-Length, fragmented/coalesced TCP
reads and binary payload boundaries. Only negotiated channels 0/1 for one JPEG
RTP/RTCP stream are accepted. Control bytes and payloads remain opaque and are
never stored in reports. Upstream client bytes are forwarded unchanged.

Delay/stall retains one complete downstream interleaved record. Later bytes,
including control responses, cannot overtake it on TCP: head-of-line blocking
is part of this experiment. Stalling upstream socket reads also creates native
socket backpressure. No bytes are randomly dropped, reordered or corrupted.
A cut shuts both owned connected sockets, without waiting for RTSP TEARDOWN.
It is abrupt transport closure, not a claim of TCP RST or UDP packet loss.

## Predeclared experiment and acceptance

Nine scenarios, FIFO/leaky appsink, filter off/on, **20 repetitions per
configuration: 720 final trials**. A separate one-repetition pilot and opt-in
integration controls precede the cohort and are not pooled. Every attempt is
retained; no hidden retries. Baseline configurations must pass before faults.
Twenty repeats characterize this finite sample; the PRD's mature 100-repeat
per-configuration gate and independent application/adoption gates remain open.

Reuse the 1.8 server (finite 100-buffer SMPTE/I420/JPEG, 320×240 at 10 fps) and
client (TCP only, latency=50 ms, two-slot FIFO/leaky appsink). No producer valve
pause is used for 1.9 transport faults. Source production and decoder receipt
are separate observations. The source stays owned and alive across reconnects;
new client connections use the same relay address/port within each trial.

Budgets before trials: 30-second process-group watchdog; five-second startup,
next acquisition, acknowledgment, relay boundary and drain guards; three-second
bus symptom, NULL/worker join and server join guards. Delay is **200 ms on one
complete interleaved record** after a baseline acquisition; stall lasts until
controller release after observed native drain, without a guessed sleep. A
pending read is observed unfinished for 100 ms before NULL. Three cuts/reopens
in the cycle scenario; exactly one explicit reopen per cut, never retry-to-pass.

| Scenario | Layer / ordered stimulus | Required evidence |
| --- | --- | --- |
| baseline | transport pass-through, four balanced receipts | framed control and RTP, negotiated channels, advancing decoder PTS |
| delay | transport: arm 200-ms hold on next interleaved unit | held/released timestamps, hold ≥200 ms, subsequent receipt |
| close | transport: cut connected pair; application: detect and reopen once | terminal bus symptom, new connection and receipt after explicit reopen |
| stall | transport: hold next unit; drain buffered receipts; release | observed empty acquisition, no parser bypass, resumed same-connection receipt |
| cycles | transport/application: repeat cut, detect, epoch transition and explicit reopen three times | four successful connections, three recovery durations; held results retain old epochs |
| slow-interruption | application holds work while source reaches count ≥10, then transport cut, drain and explicit reopen | native queue/drop snapshots, held old completion after epoch transition |
| shutdown | transport stall/drain, register pending read; application NULL | bounded empty read wakeup, worker joined despite held media |
| epoch | transport stall plus application epoch transition with held result | native-only old publication versus filtered rejection; no physical-epoch inference |
| recovery | transport stall/drain/release, then three receipts | same connection resumes with advancing decoder PTS |

A trial passes when its declared fault is observed and its specific recovery or
shutdown behavior completes within guards, with trustworthy local lineage and
complete cleanup. Intentional transport closure/EOS is an expected stimulus,
not a failed trial. Missing negotiation, unobserved fault, malformed/truncated
framing, parser overflow, unexpected callback/bus errors, failed recovery,
timeout or cleanup leak fails the trial. A behavioral failure is retained rather
than dismissed as flakiness. Forced watchdog controls are reported separately.

## Clock and measurement contract

Relay I/O, controller, client pad/receipt/decision, bus polling and NULL observations
share the trial process monotonic clock. Hold duration is release minus retained
record time; detection latency is first observed bus symptom minus applied cut;
connection recovery is first new-generation receipt minus explicit reopen request.
Fault end to resumed receipt is a separate duration. Server acknowledgments retain
their labeled server domain; no cross-process timestamp subtraction.

Decoder PTS uses nanoseconds within each connection domain, not local wall time.
Report within-connection deltas and gaps; never compare resets across connections
as a regression. Application epoch, connection generation, RTSP Session header
presence and physical-source epoch are distinct. Retain original frozen receipt
sidecars through final publication, using the existing locked PublicationLedger.
RTSP session identifiers and sender CNAMEs are not persisted. Capture timestamp,
capture freshness, source-frame identity, source sequence lag, physical-session
identity and UDP loss are UNKNOWN/unavailable. Receipt age is local residence,
not physical freshness. Native drop snapshots are non-atomic; application epoch
rejection applies only after acquisition. No global loss conservation is inferred.

Each report must include attempts/completions/failures/timeouts, recovery attempts
and success, descriptive timing distributions, acquired counts, native drops,
rejections, obsolete publications, continuity diagnostics and cleanup. Timings
are descriptive; no universal real-world error rate or race-freedom claim.

## Isolation and cleanup requirements

One owned server process, one relay worker, and optional one bounded reader per
trial. Worker owns connected sockets and accepts only IPv4 loopback. Controller
commands have acknowledgments and cannot supply destinations. Read/write sizes,
framer memory, source duration, connections and execution time are bounded.
Closing/canceling the relay releases a retained record without forwarding it;
client NULL and server stop follow in finally. Every owned listener's exact port
must refuse connection, all pipelines reach NULL, workers join and child exits
are waited. Parent watchdog owns and kills/waits the full trial process group.
Normal cleanup must not use forced termination. No unrelated network state can
be selected or modified.

## Implemented bounds and reproduction

The relay uses one worker and 10-ms select polls, with 500-ms socket I/O guards.
The downstream framer permits 16-KiB headers, 64-KiB bodies, a 128-KiB retained
input buffer, and at most one 65535-byte interleaved payload plus framing held
for impairment. TCP chunks are at most 64 KiB. It rejects unsupported protocol,
channels, duplicate/invalid lengths, oversize input and truncated upstream EOF.
Control bodies may contain dollar bytes; they are never parsed as media.
A commanded cut/stop or client teardown intentionally abandons pending bytes;
it does not misreport that abandonment as successful delivery or random loss.

New modules are transport_framing (pure bounded parsing), transport_relay (fixed
fixture sockets/worker) and transport_experiment (owner phases/report/supervisor).
No 1.8 source, buffer, ledger, client or native dependency was replaced.

```sh
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_transport_faults.py -v
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.transport_experiment --repeat 1 > /tmp/vfl19-pilot.json
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.transport_experiment --repeat 20 > /tmp/vfl19-results.json
.venv/bin/python -m pytest -v
```

A CLI `--scenario` selects only declared fixtures; it never accepts endpoints.
Intentional retained-media abort is a separate integration cleanup control.
The supervisor's forced timeout path has a pure regression verifying exactly one
attempt, process-group kill, wait and explicit UNKNOWN cleanup, not a fabricated
cleanup pass. Ordinary Python CI requires neither sockets nor native bindings.
The [PRD audit](../audits/PRD_IMPLEMENTATION_MATRIX.md) preserves gaps beyond this
local impairment assessment; stamped images and mature original-RTSP repeats
must be evaluated separately under the newer technical-stage master task.
