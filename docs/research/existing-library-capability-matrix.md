# Existing-library capability and gap investigation

Research accessed **2026-10-20**. Only official project documentation and local
read-only version/property inspection support the findings below. No media,
decoder, RTSP endpoint, reconnect, or shutdown experiment was run. Rolling URLs
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
