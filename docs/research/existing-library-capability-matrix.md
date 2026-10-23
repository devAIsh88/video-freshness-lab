# Existing-library capability and gap investigation

Milestone 1.6 research accessed **2026-10-20**. Official project documentation and
local read-only version/property inspection support the historical matrix below.
No pipeline or transport experiment had run at that milestone. Milestone 1.7's
separately classified runtime findings follow the matrix. Rolling URLs
are access-date snapshots, not promises about every installed release. Missing
documentation is not evidence that a feature is absent.

Classification throughout: **D** = documented capability; **V** = verified locally
(only the stated inspection); **H** = hypothesis/proposed test; **U** = unknown,
requires experiment. Mixed cells distinguish what is documented from what still
needs measurement. Documentation and recommendations do not count as external
behavior reproduction or satisfy the PRDs' adoption gates.

## Documentation versions and evidence

| Library | Official documentation reviewed | Local inspection |
| --- | --- | --- |
| GStreamer | D: [1.28 release notes](https://gstreamer.freedesktop.org/releases/1.28/) identify 1.28.8, released October 8, 2026. Rolling [appsink](https://gstreamer.freedesktop.org/documentation/app/appsink.html) explicitly marks new properties since 1.28 | V: core/tools and appsink report **1.28.6**; appsrc/appsink/videotestsrc are inspectable |
| FFmpeg | D: [8.0 AVFrame](https://ffmpeg.org/doxygen/8.0/structAVFrame.html), [8.1 demuxing](https://ffmpeg.org/doxygen/8.1/group__lavf__decoding.html), rolling [formats](https://ffmpeg.org/ffmpeg-formats.html) and [protocols](https://ffmpeg.org/ffmpeg-protocols.html) | V: ffmpeg/ffprobe report **8.1.2**; option behavior untested |
| PyAV | D: current official [project repository](https://github.com/PyAV-Org/PyAV) links to the new documentation host; pages identify **19.0.0**. The old pyav.org stable time page still identifies **9.0.2**, so it is not used as a current API guarantee | V: `av` is absent from the project venv |
| OpenCV | D: 4.x URL resolves to [**4.13.0** property reference](https://docs.opencv.org/4.13.0/d4/d15/group__videoio__flags__base.html) and [VideoCapture API](https://docs.opencv.org/4.13.0/d8/dfe/classcv_1_1VideoCapture.html) | V: `cv2` is absent from the project venv |

U: an 8.1 AVFrame documentation request timed out; the reviewed 8.0 page is
explicitly a baseline, not verification of all 8.1 differences. One guessed
GStreamer language-binding tutorial URL also failed to fetch; Python signatures
on the app element API pages support binding availability, not local usability.
V: Python `gi` is absent from the project venv. No dependencies were adopted.

## Capability comparison

| Dimension | GStreamer | FFmpeg | PyAV | OpenCV VideoCapture |
| --- | --- | --- | --- | --- |
| Buffer control | D: appsink `max-buffers`; `max-bytes`/`max-time` since 1.24; `leaky-type` since 1.28; older `drop` now deprecated. rtspsrc jitterbuffer `latency`/`drop-on-latency` | D: RTSP `reorder_queue_size`, socket `buffer_size`, `max_delay`; `fflags=nobuffer` reduces initial analysis buffering. U: total decoder/application backlog | D: FFmpeg options exposed through container/open APIs. U: effective queue bounds for the linked build | D: `CAP_PROP_BUFFERSIZE` exists; effectiveness depends on backend. U: usable bound in a particular build |
| Timestamp availability | D: GstBuffer PTS/DTS/duration can be absent; nanosecond units. D: segment mapping matters | D: packet PTS/DTS may be unset, in stream time base; AVFrame best-effort stamp may be heuristic | D: frame and packet PTS/DTS with time bases; presentation seconds and side data available | D: FFmpeg-only `CAP_PROP_PTS` uses FPS time base; `POS_MSEC` is position, not guaranteed capture time |
| Source timestamp trust | D: rtspsrc can attach reconstructed reference-clock metadata under stated conditions. U: source capture semantics and clock error | D: generated/missing/heuristic timestamp paths exist. U: source capture meaning | D: metadata exposure. U: provenance of any particular decoded stamp | D: stream-open UTC property describes opening. U: capture meaning of returned position/PTS |
| Reconnect | D: rtspsrc `udp-reconnect` for RTSP control closure during UDP; timeout messages have documented scope. U: arbitrary restart recovery | D: protocol-specific options; HTTP reconnect switches must not be assumed to apply to RTSP. U: RTSP restart recovery policy | D: open/read timeouts and explicit close. U: automatic recovery/session policy for RTSP | D: explicit open/release. U: automatic recovery behavior of a chosen backend |
| Session observability | D: stream-start/segment events and RTSP messages. U: correspondence to physical restart or application epoch | D: explicit input lifetime under application control. U: durable physical-session identity | D: container lifetime exposed. U: camera epoch inference | D: backend and stream-open information. U: reliable source-generation identity |
| Drop instrumentation | D: appsink `in`, `out`, `dropped`, queue-level counters since 1.28. V: inspected locally | U: end-to-end drop accounting across demux, decode, application boundaries | U: complete accounting through the Python decode path | U: portable per-frame drop accounting across backends |
| Shutdown | D: appsink pull unblocks at READY/NULL or EOS; `wait-on-eos` governs waiting. U: full application teardown | D: `avformat_close_input` frees input resources. U: blocked-read cancellation and decoder drain in chosen application | D: explicit container close; documented timeout contract. U: native worker cleanup under fault | D: `release()` closes capture. U: thread interruption and blocked-read cleanup for chosen backend |
| Python use | D: appsrc/appsink APIs show Python signatures. U: local GI setup and ownership details | D: C API/CLI. H: Python subprocess or a binding, with metadata preserved separately from raw pixels | D: native Python bindings with direct timestamp objects | D: Python read/get/set/release API; D: unsupported property reads can return zero |
| Thin configuration sufficient? | H: native bounded/leaky appsink may satisfy waiting-queue freshness; U: final in-flight epoch rule | H: targeted options plus a short application recipe may suffice; U: same final-output contract | H: small timestamp/epoch sidecar may suffice; U: real lineage burden | H: explicit backend plus supported properties may suffice; U: metadata ambiguity and source identity |

GStreamer references: [appsink queue, counters, EOS](https://gstreamer.freedesktop.org/documentation/app/appsink.html),
[GstBuffer time/offset/meta](https://gstreamer.freedesktop.org/documentation/gstreamer/gstbuffer.html),
[clock/segment synchronization](https://gstreamer.freedesktop.org/documentation/additional/design/synchronisation.html),
[rtspsrc policies](https://gstreamer.freedesktop.org/documentation/rtsp/rtspsrc.html),
[stream and segment events](https://gstreamer.freedesktop.org/documentation/gstreamer/gstevent.html).
U: none establishes an external sink's transaction semantics. A stream-start
identifier or SSRC is not assumed to prove a new physical camera exposure epoch.

FFmpeg references: [RTSP transport/timeout/reordering and HTTP reconnect scope](https://ffmpeg.org/ffmpeg-protocols.html),
[analysis buffering and timestamp generation options](https://ffmpeg.org/ffmpeg-formats.html),
[8.1 packet timestamp units and input cleanup](https://ffmpeg.org/doxygen/8.1/group__lavf__decoding.html),
[8.0 AVFrame presentation and best-effort fields](https://ffmpeg.org/doxygen/8.0/structAVFrame.html).
H: reduced buffering may improve observed lag; it cannot by itself substantiate
physical capture time. U: behavior with B-frames, losses, resets, and option
combinations on local 8.1.2 remains unmeasured.

PyAV references: [19.0.0 frames](https://pyav.basswood.io/docs/stable/api/frame.html),
[packets](https://pyav.basswood.io/docs/stable/api/packet.html),
[containers and decoder flushing](https://pyav.basswood.io/docs/stable/api/container.html),
[open/options/timeout](https://pyav.basswood.io/docs/stable/api/_globals.html).
D: frame/packet timestamps can be `None`; packet and frame are different objects.
D: final dummy demux packets flush decoder buffers. U: draining versus aborting
after source replacement needs an application policy and experiment. Packet
trust flags are not interpreted as capture-clock verification.

OpenCV references: [4.13.0 property meanings](https://docs.opencv.org/4.13.0/d4/d15/group__videoio__flags__base.html),
[4.13.0 API caveats](https://docs.opencv.org/4.13.0/d8/dfe/classcv_1_1VideoCapture.html).
D: open/read timeouts are open-only and documented for FFmpeg/GStreamer backends.
D: `getBackendName()` and property support checks matter; even a successful
`set()` does not guarantee device acceptance. U: a returned zero PTS may be
valid zero or unsupported. An adapter must retain ambiguity until independently
validated, rather than converting it to zero latency.

## First evaluation recommendation (proposal, not executed)

H: choose **GStreamer 1.28.6**, matching inspected core/appsink, for the first
local real-library evaluation. D: 1.28.8 is documented; using 1.28.6 is a fixed
existing-environment baseline, not a latest-version or security recommendation.
Record and match plugin, GI, and linked library versions before execution; any
version change requires an explicit new experiment record. No system change is
authorized here. Review binding dependencies, purpose, versions, sources, and
licenses before adoption in a later authorized milestone.

The choice follows evidence: queue/drop instrumentation is already inspectable,
the documented native policy closely overlaps our custom mailbox, and explicit
PTS/buffer metadata avoids starting with a backend-dependent zero value.
H: this provides the strongest initial chance to disprove a separate queue
implementation's value. PyAV is a useful subsequent timestamp/decoder comparison;
OpenCV adds backend uncertainty; FFmpeg alone needs a Python metadata bridge.

H: proposed deterministic source is finite in-process **appsrc**, with tiny
generated raw buffers, explicit ordinal offsets and PTS (0, 10, 20 ms), and a
recorded source/epoch sidecar. Use no camera, file recording, codec, or server.
D: [appsrc](https://gstreamer.freedesktop.org/documentation/app/appsrc.html) supports
application-supplied buffers and EOS. U: preservation through the chosen path
must be checked. A later stamped-image/codec step is a separate PRD gate; this
proposal tests buffer metadata only, not robust pixel lineage.

H: compare these identical workloads, with test-owner events/pad observations
confirming each push has reached appsink before advancing (no timing sleeps):

1. A finite native nonleaky queue control with capacity covering the workload.
2. Native `max-buffers=1 leaky-type=downstream sync=false`, with no extra mailbox.
3. The same native policy plus only an application final-output epoch check.

Acquire frame A and hold its processing outside streaming callbacks. Push B/C
while no next sample is pulled; record queue levels, in/out/drop counts, source
ordinals, and ordered test events. Then release processing and pull the survivor.
In a separate run declare a controller boundary, activate epoch B, reset PTS, and
release the old active result. Compare native queue behavior and final output
with the explicit application check. U: a native flush/state-reset strategy may
also suffice; evaluate it before adding a custom mechanism. Already acquired
results are an application boundary, not automatically a library defect.

Declare expected identities and count conservation before running. Use bounded
waits as hang guards, explicit EOS, `wait-on-eos` chosen for the draining policy,
and READY/NULL teardown with worker joins on failure. U: the exact EOS/state
behavior must be measured, not inferred from the project mailbox. Record
unexplained failures separately. Do not silently retry or call a metadata-only
source physical capture ground truth.

## Build, pivot, or stop

- H: build only a small adapter/regression test if independent-library behavior
  shows a meaningful observable contract failure after documented native controls
  are applied, and roughly 30 lines can preserve precise lineage. No package yet.
- H: pivot to a native configuration recipe or upstream test if native policy
  plus a short final-output check meets the same contract; this is useful negative
  gap evidence. Prefer existing GStreamer validation tooling if it covers the path.
- H: stop freshness claims when capture meaning, clock mapping, session boundary,
  or lineage is unavailable; report `unknown`. Stop or simplify if only contrived
  consumers fail, instrumentation is invasive, or event ordering remains flaky.

The PRDs still require independent external reproduction, actionable evidence,
100 mature integration repeats with at most 1% unexplained failures, value over
a recipe, maintainer acknowledgment, two unrelated developers' adoption intent,
and proportionate maintenance before a package decision. V: 1.6 meets none of
these external/adoption gates. H: the next milestone should authorize only the
finite local native-configuration comparison, not RTSP or a product framework.

## Milestone 1.7 runtime supplement

**V (local runtime):** Fedora system Python 3.14.7 has PyGObject 3.56.3 and
Gst/GstApp 1.0 bindings for installed GStreamer/app plugin 1.28.6. The Python
3.12.15 project venv still lacks GI. No dependency was installed or changed.

**V:** finite direct appsrc/appsink workloads verify native FIFO backpressure,
downstream leaky oldest-waiting replacement, input/output/drop counter accounting,
explicit payload-token/epoch association, EOS handling with pending samples,
and NULL cleanup in the tested paths. Native appsrc buffering is independently
observed; intermediate property snapshots are not atomic. See the
[1.7 design](../architecture/gstreamer-experiment.md) and
[measurements](../experiments/milestone-1.7-results.md) for exact conditions.

**V:** native leaky buffering did not retract an already acquired old-epoch
result. A small application final-output epoch check suppressed it. This is an
application-level policy added by our harness, not a GStreamer defect or evidence
of a missing general feature. **H / recommendation:** PIVOT toward native
configuration, validation tests, and minimal application integration; no additional
custom buffering layer is justified by this experiment.

**U:** RTSP reconnect/session discovery, RTP/RTCP reference-clock trust, codecs,
physical capture age, approximate clock mapping, blocked network reads, and
third-party application behavior remain untested. Other libraries' entries remain
documentation/inspection findings. The historical 1.6 proposal above is preserved
as a pre-experiment recommendation, not a current claim of missing bindings.

## Milestones 1.8/1.9 runtime supplement (2026-10-21)

Historical cells above retain their original versions and untested scope.
Current optional Fedora runtime is core/base/server 1.28.8, JPEG/RTP/rtspsrc
1.28.6, system Python 3.14.7 / PyGObject 3.56.3. No new native package was adopted.

| Boundary | Classification / executed evidence | Remaining limit |
| --- | --- | --- |
| JPEG RTP/RTSP TCP decoding | V: 1.8 120/120 finite loopback trials | No source pixel marker or capture-clock trust |
| Native FIFO/leaky plus final output check | V: same decoded receipt sidecar reaches locked ledger; obsolete held work suppressed only with application check | Application epoch, not physical source session |
| Controlled TCP delivery faults | V: 1.9 720/720 trials, acknowledged delay/stall/cuts; 400/400 explicit recoveries | No UDP, network partition, RST guarantee or automatic reconnect |
| Shutdown under held media | V: 80 pending-read controls wake empty at NULL; relay/server ports released | Finite local configuration; no general race-freedom claim |
| Mature original RTSP reliability | PARTIAL at 1.9 snapshot: 20/config impairment trials; original 1.8 five/config | Separate 100/config original Stage 5 cohort required; do not pool denominators |
| Source image identity | U at baseline: unstamped videotestsrc and local ordinals cannot prove it | Initial PRD audit requires actual optional stamped arrays |
| Physical freshness and independent value | U: no capture truth, independent consumer or adoption evidence | PIVOT to recipe remains; no separate buffering framework justified |

See [1.9 measured results](../experiments/milestone-1.9-results.md) and the
[original PRD matrix](../audits/PRD_IMPLEMENTATION_MATRIX.md). Toxiproxy's documented
TCP toxics are an assessed alternative, not an installed/executed dependency.

## Original Stage 3/4 image supplement

V: optional Python 3.12.15 / NumPy 2.2.6 / headless OpenCV 4.12.0.88 process
generates and independently decodes source/epoch/sequence pixel markers through
BGR→gray→BGR and lossless PNG. Ten configurations match across 100 repetitions
each. Actual new decoded buffers carrying repeated old markers are distinguished
from no-data intervals and a static scene with advancing stamps. Source sidecars
retain their original epochs through active work and final simulator rejection.
See [image evidence](../experiments/stamped-images-results.md).

U: JPEG/video-codec stamp survival, physical capture clocks/source epochs,
independent consumer value and adoption remain unverified. This image experiment
does not retroactively add source lineage to the unstamped RTSP source.

## Original Stage 5 mature contract supplement

V: the corrected native lifecycle completed **1200/1200 actual RTSP trials**,
100 per normal/epoch/reconnect ×FIFO/leaky ×filter configuration, with 400/400
explicit recoveries and 1600 positively verified media-NULL/server-pool cleanups.
The same decoded receipt sidecar reaches final output; 400 obsolete completions
are rejected in filtered modes, while permissive controls publish 400 obsolete
outputs. Native waiting replacement alone does not retract acquired evidence.

V: the initial baseline failed once in 400 trials with a server -11 exit. It is
retained separately; root cause is unproven. Explicit media/session/client/pool
teardown strengthens the fixture rather than asserting an external-library defect.
See [counts, distributions and limitations](../experiments/rtsp-contract-reliability.md).

U: the short receipt helper is 24 physical lines, but independent adapter burden,
consumer behavior, physical source lineage/capture clocks, Windows and adoption
are still unverified. The selected local application-epoch contract passes;
no claim of complete physical freshness follows. PIVOT remains supported; original
Stages 6–7 await separate authorization.

## Independent consumer and final decision supplement (2026-10-23)

Historical unverified cells remain historical. **V:** unchanged Groundlight
FrameGrab commit `17f550890b33925cbd92cf997776e64600954f87` (metadata 0.15.1,
MIT) was reviewed and executed through its supported file consumer. Actual
source-stamped FFV1/AVI → OpenCV FFmpeg decode → public grab/options/seek/release
path completed 800/800 final trials, 100 per eight scenarios. Native decimation,
replay, EOF and crop behavior matched inspection. No reusable freshness defect
was observed. The initial 99/100 immediate cleanup cohort remains separately
reported; bounded native-task observation preceded the final cohort.

**V:** source markers survive this selected video codec path. A removed marker
becomes UNKNOWN. Old held arrays require an explicit application final policy;
no upstream promise to retract them is alleged. **V:** README support predicate
has a false positive when GStreamer build value is NO; a private unposted proposal
exists. **BLOCKED:** external GStreamer RTSP execution in the audit OpenCV wheel,
which reports NO. Do not extend file results to that backend or physical cameras.

**U:** physical capture clocks, live source-head lag, Windows, external adoption,
full approximately 30-line semantic adaptation and package advantage remain unmet.
**Decision:** retain PIVOT to native configuration plus final epoch recipe and
validation toolkit. No new buffering framework, public package or deployment.
See [independent audit](../audits/THIRD_PARTY_CONSUMER_AUDIT.md),
[final decision](../audits/FINAL_GO_NO_GO_DECISION.md) and
[compliance](../audits/FINAL_PRD_COMPLIANCE.md).
