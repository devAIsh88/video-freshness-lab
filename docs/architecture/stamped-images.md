# Stamped synthetic image lineage: dependency decision

The initial PRD audit found no actual NumPy/OpenCV image lineage experiment.
Numbered objects, symbolic pixel labels and unstamped videotestsrc do not satisfy
original Stage 3. The owner now authorizes the smallest optional CPU-only path.

Before adoption, inspect the official version pages:
[NumPy 2.2.6](https://pypi.org/project/numpy/2.2.6/) supplies uint8 image arrays
(BSD-3-Clause; bundled binary components have their own notices), and
[opencv-python-headless 4.12.0.88](https://pypi.org/project/opencv-python-headless/4.12.0.88/)
supplies cv2 drawing, color conversion and in-memory PNG encode/decode (OpenCV
Apache-2.0; wheel wrapper MIT, with bundled third-party license notices). These
are fixed reproducibility choices, not a latest-version/security recommendation.
Both have compatible Python 3.12 wheels. Install only official PyPI binary wheels
in an ignored, isolated `venv-media/` created from project Python 3.12. Do not
modify Fedora system Python, expose GI to a venv, or install GUI/contrib modules.
Normal Python-only CI and runtime dependencies remain unchanged; an optional
images extra will record the two direct pins. No real or external image is used.

Planned path: generate a small uint8 BGR array at the source; encode source,
epoch and sequence plus checksum as high-contrast cells; include readable text;
convert BGR→gray→BGR and PNG encode/decode in memory; decode the source marker
and compare it to the original immutable sidecar. Corrupt/cropped/ambiguous
markers fail closed (identity UNKNOWN), never replaced with a consumer ordinal.
No JPEG or video-codec survival follows from a lossless PNG experiment.

Reuse the existing Simulator/VirtualClock/FIFO/LatestFrame schedule for processing
delay and age/lag accounting. An image registry keyed by source-generated IDs
adapts the existing frame path; do not build another queue or concurrency system.
A repeated-content fixture must create new decoded arrays carrying an old marker,
with new local receipt times, alongside a static-scene control with advancing
source stamps. Capture time remains unavailable; simulator production times are
synthetic age references and never physical camera capture evidence.

## Implemented ownership and event boundaries

The optional `stamped_images` module imports NumPy/cv2 only when image functions
are called. `Marker` remains usable in the ordinary media-free suite. Each image
is a 96×160×3 uint8 BGR array. The first 64×40 pixels encode 160 bits in a 16×10
cell grid (4×4 pixels/cell): magic VFL3, uint32 source, epoch, sequence, then CRC32.
A readable source/epoch/sequence label appears below it. Scene pixels are generated
locally. This fixed-coordinate marker has no orientation/scale recovery, error
correction, authentication or collision-proof guarantee. Ambiguous cell levels,
wrong dimensions/type, magic or checksum return UNKNOWN; wrong original sidecar
raises a mismatch. Never replace an unreadable marker with a delivery ordinal.

Images are backed by immutable bytes and exposed as read-only ndarray views;
the view cannot re-enable writes. Transformations allocate independent arrays.
The evidence sidecar is the existing frozen FrameEvidence with source_order IDs
and capture=None. No physical capture or inferred presentation time is attached.

ImageSimulator adds image observation hooks to the existing finite Simulator:
source's frame_produced hook creates/stamps the image before queue admission;
processing_started converts BGR→gray→BGR, PNG encodes/decodes and independently
checks the decoded marker against original source evidence. Completion decodes
again, retaining the original epoch across active processing. The existing virtual
clock, FIFO/latest buffers, source head, controls, metrics, final session policy
and event order are reused unchanged. There is no new queue, scheduler or worker.

Processing delays are injected virtual durations (10/40 ms), not measured CPU or
wall latency. Source age/lag have synthetic ground truth from the source schedule;
capture age stays UNKNOWN. Every processing completion has checked image lineage,
including old active work rejected at output; queued drops/rejections have no
invented processing attempt. Produced, processed, replaced, rejected and emitted
retain the simulator's documented accounting rather than being summed twice.

The repeated-content control creates three independently decoded buffers from
one old stamped image. Arrival observations advance but the marker remains at
source 7/epoch 0/sequence 0. A static-scene control preserves the same scene ROI
with source stamps 0,1,2. A no-data interval produces no image at all. Distinct
identity observations do not solve real-camera freeze detection where such a
source stamp may be unavailable. The selected path validates color conversion
and lossless PNG only, without JPEG/video codec, resizing, streaming or cameras.

## Reproduction

```sh
.venv/bin/python -m venv venv-media
venv-media/bin/python -m pip install -e '.[images]'
venv-media/bin/python -m unittest discover -s integration -p test_stamped_images.py -v
venv-media/bin/python -m video_freshness_lab.stamped_images --repeat 100 > /tmp/vfl-images-results.json
.venv/bin/python -m pytest -v
```

The media venv uses Python 3.12.15, NumPy 2.2.6 and OpenCV 4.12.0.88 wheel
(cv2 reports 4.12.0). The ordinary venv still has neither numpy nor cv2. Native
libraries' bundled notices remain in installed wheel metadata; no vendored binary
or third-party asset enters Git. No GUI, GPU or system package is needed.

There are ten named image configurations (balanced/slow/pause for two policies,
and restart with both policies/filter settings). The CLI makes one reference
run per configuration, then compares 100 fresh repetitions against its complete
trace. Those ten reference runs are separate from the 1000-repetition denominator.
All native image work stays in this explicit optional process; no application
worker/thread/network listener is created. Finite arrays and clock agenda drain
before return. Missing dependencies fail explicitly instead of integration skips.
