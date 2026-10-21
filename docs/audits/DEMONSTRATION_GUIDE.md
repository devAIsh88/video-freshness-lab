# Demonstrating the technical lab

Use the project root and existing environments. No camera, credentials, public
listener, GPU or service account is needed. These are local experiments, not a
production video reader. The original PRDs remain local and untracked.

## 1. Explain a healthy read versus current information

```sh
.venv/bin/python -m video_freshness_lab
```

Point to slowdown-fifo versus slowdown-latest. Both consume valid numbered items.
FIFO's maximum result age is 310 virtual ms; latest's is 70 virtual ms, replacing
six waiting items. The source horizon is identical. Availability and throughput
alone do not prove the age of the evidence behind a result. These are injected
model ages, not measured camera/network latency.

## 2. Show why queue policy cannot retract acquired work

```sh
.venv/bin/python -m video_freshness_lab --scenario reconnect --policy latest --json > /tmp/vfl-reconnect-naive.json
.venv/bin/python -m video_freshness_lab --scenario reconnect --policy latest --session-filter --json > /tmp/vfl-reconnect-filtered.json
```

The latest-only model can emit two obsolete outputs while its example age budget
passes. Adding final session validation suppresses them. Closing the real-thread
mailbox still drains accepted work; it does not secretly activate another epoch.
The separate application output boundary decides whether a completed result may
publish. The simulator's disconnect epoch convention is deliberately explicit.

## 3. Demonstrate actual images and repeated content

The ignored venv-media has the optional pinned NumPy/headless OpenCV packages.
Fresh reproduction setup is in the stamped-images architecture document.

```sh
venv-media/bin/python -m unittest discover -s integration -p test_stamped_images.py -v
venv-media/bin/python -m video_freshness_lab.stamped_images --repeat 1 > /tmp/vfl-image-demo.json
```

Explain that the source draws a source/epoch/sequence marker before queueing.
The consumer reads it after BGR→gray→BGR and PNG encode/decode, then checks it
again at completion against the original immutable sidecar. A corrupted marker
is UNKNOWN, never relabeled as the next arrival. PNG survival does not establish
JPEG/video-codec survival.

The repeated-content control has three independent decoded arrays with identical
pixels and the same old source stamp. A no-data interval has no buffers at all.
A static scene can have advancing source stamps. Local receipt timestamps can
advance in all these delivery cases without proving new physical exposures.

## 4. Optional real RTSP demonstration

This explicit command needs permission to create IPv4 loopback sockets and uses
Fedora system Python's already installed GStreamer bindings:

```sh
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_rtsp_transport.py -v
```

The existing library server generates finite SMPTE/JPEG media. RTP-over-TCP
travels over loopback, is depayloaded/decoded, then acquired through appsink.
The actual acquired sample's sidecar reaches the final epoch check. We compare
FIFO/leaky queues with/without that check. An already acquired old result is
suppressed by the final check, not by native waiting-buffer replacement.

Application epoch, connection generation and physical source epoch are distinct.
Decoder PTS is presentation time in its own domain. Capture age stays UNKNOWN.
Native source media now explicitly unprepare and reach NULL; internal library
tasks drain before the owned server process exits. A prior native teardown crash
was retained in the evidence, not hidden by rerunning until green.

## 5. Explain transport faults and the conclusion

```sh
PYTHONPATH=src /usr/bin/python3 -m video_freshness_lab.transport_experiment --scenario stall --repeat 1 > /tmp/vfl-stall-demo.json
```

This is four queue/filter configurations, not a long reliability cohort. The
bounded fixture relay retains a complete interleaved record until acknowledged
release. It affects only the owned loopback connection. TCP head-of-line blocking
also delays later control replies. No UDP loss or physical-network fidelity is
claimed. Recovery after a cut is explicit application reopen, not an automatic
native-library recovery claim.

The supported recommendation is PIVOT to configuration guidance and small output
checks. Independent consumer value, trustworthy physical lineage/capture clocks,
adoption and public licensing are not established. The next authorized execution
must decide the bounded Stage 6 audit; this demonstration does not begin it.
