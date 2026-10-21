# Original Stages 3/4: actual stamped images and repeated content

The initial audit found the original Stage 3 absent: numbered objects, symbolic
pixel labels and unstamped JPEG transport were not source-stamped image arrays.
This change adds only that experiment and the missing repeated-content distinction.
Existing virtual clock, simulator, buffer/session contracts and RTSP code remain
unchanged. The Stage 4 gaps fit this same coherent change; no separate artificial
fault-coverage commit is needed. **PIVOT remains supported.**

## Actual path and source lineage

The [architecture](../architecture/stamped-images.md) describes reviewed optional
pins/licenses and exact pixel format. Source generation creates actual 96×160×3
uint8 BGR arrays, a readable label and a binary cell marker containing source 7,
epoch and sequence plus CRC32. Generation occurs at frame_produced before queue
admission. Consumer IDs are never assigned retrospectively. Source evidence and
pixels are immutable; transformations allocate separate arrays.

The chosen processing path actually runs OpenCV BGR→gray→BGR and in-memory PNG
encode/decode. A decoder reads the source marker at processing start and again
at completion, checking it against the original frozen sidecar. Grayscale changes
scene pixels, so this is stronger than a mere whole-array copy or attached
metadata. Ambiguous/corrupted/cropped markers return UNKNOWN; a valid marker that
mismatches the original source evidence fails. No hidden fallback assigns an ID.

Tested dependencies: Python 3.12.15, NumPy 2.2.6, opencv-python-headless
4.12.0.88 (cv2 4.12.0), isolated ignored venv-media. Both packages were absent
before inspection. Restricted package access first failed; installation of the
documented official PyPI binary wheels succeeded with approved network access.
No system package or Fedora interpreter changed. Optional images pins are declared
in pyproject.toml; ordinary dependencies and Python-only CI remain media-free.

## Measurements and repeatability

Ten named configurations, **100 fresh repetitions each = 1000/1000 matching
complete traces**, zero failed repetitions. Ten additional reference runs define
the expected trace and are excluded from that denominator. A prior one-repetition
pilot and optional regression tests are separate. The
[sanitized summary](stamped-images-summary.json) records versions, raw evidence
SHA-256, exact metrics and markers; raw reports stay in `/tmp/vfl-images-results.json`.
No image/binary artifact is committed.

All age/duration values below are **injected simulator milliseconds**, not CPU
or camera latency. Production timestamps describe controlled source schedule;
physical capture timestamp and capture freshness remain UNKNOWN.

| Workload | Policy / filter | Produced | Processed | Published | Total drops incl. rejected | Session rejects (subset of drops) | Max published result age ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Balanced | FIFO/latest | 10 | 10 | 10 | 0 | 0 | 10 |
| Slow | FIFO | 10 | 10 | 10 | 0 | 0 | 310 |
| Slow | Latest | 10 | 4 | 4 | 6 | 0 | 70 |
| Producer pause | FIFO | 6 | 6 | 6 | 0 | 0 | 150 |
| Producer pause | Latest | 6 | 4 | 4 | 2 | 0 | 70 |
| Disconnect/restart | FIFO, off | 7 | 7 | 7 | 0 | 0 | 190 |
| Disconnect/restart | FIFO, on | 7 | 5 | 4 | 3 | 3 | 130 |
| Disconnect/restart | Latest, off | 7 | 4 | 4 | 3 | 0 | 70 |
| Disconnect/restart | Latest, on | 7 | 3 | 2 | 5 | 2 | 50 |

Slow FIFO processes source sequences 0–9; latest processes 0,4,8,9 and replaces
six waiting frames. Both use the same source image identities and schedule.
FIFO delivery remains alive while eight outputs exceed the explicit 80-ms
synthetic result-age budget; latest has zero under that budget. A stricter budget
would change the verdict without changing image identity. The selected values
are example contracts, not universal camera thresholds.

Restart without filtering publishes three obsolete FIFO results or two latest
results. Filtering suppresses all obsolete outputs. Both filtered modes process
and reject one active old image after the boundary, preserving marker epoch 0;
additional old queued frames are rejected before processing. Thus `processed`
includes the rejected active item, and session rejection is already included
in total drops. Do not double-count those categories. Source close/epoch policy
retain the simulator's documented synthetic semantics, not physical session truth.

## Genuine Stage 4 distinctions

| Case | Actual evidence | Invariant / limit |
| --- | --- | --- |
| No new data / producer pause | Source times 0,10,60,70,80,90; six actual images | No image is emitted in the 20–50-ms interval; source epoch stays unchanged |
| New buffers repeating old content | Three independent decoded arrays, no shared memory, identical full pixels and marker 7/0/0 | Two nonadvancing-identity findings despite local arrivals 0,10,20 ns; capture age UNKNOWN |
| Static scene with new source stamps | Identical generated scene ROI, markers 7/0/0, 7/0/1, 7/0/2 | Static scene content alone is not declared a freeze |
| Old queued images | FIFO retains old marker sequences and increasing synthetic age/lag | Successful processing does not imply current evidence |
| Delayed obsolete result | Actual transformed image from epoch 0 completes after controller boundary | Final session policy suppresses it; original marker never retagged |
| Missing trustworthy capture reference | capture=None for source and every output | No PTS/receipt/virtual-production value becomes physical capture time |
| Corruption/mismatch | Checksum, dimensions/type, ambiguous cells and wrong-sidecar controls fail | UNKNOWN/failed identity, not an invented marker |

Repeated-identity detection is a controlled source-marker observation. It does
not solve real-camera freeze detection where a trustworthy stamp may be absent,
and static-scene equality does not distinguish repeated exposures on its own.

## Tests, cleanup and reproduction

```sh
.venv/bin/python -m pip install -e '.[dev]'
venv-media/bin/python -m pip install -e '.[images]'
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
venv-media/bin/python -m pip check
git diff --check
git diff --cached --check
venv-media/bin/python -m unittest discover -s integration -p test_stamped_images.py -v
venv-media/bin/python -m video_freshness_lab.stamped_images --repeat 100 > /tmp/vfl-images-results.json
```

**302 Python-only tests pass**: all 295 prior cases plus seven pure marker cases.
The six optional OpenCV/NumPy unittest methods pass, including source/epoch/sequence
survival, immutable independent arrays, corruption/mismatch, FIFO/latest behavior,
new repeated buffers/static scene, and pause/restart rejection. They do not run
in ordinary GitHub CI. Editable packaging and both pip environments are verified.
Ruff lint/format and working/staged whitespace checks pass.

The experiment creates no application worker, child, socket or persistent media.
Its finite clock agenda and active-image registry drain after all processing.
OpenCV is limited to one native worker in the explicit test/CLI process; that
process exits after the run. No general race-freedom or native allocator/lifetime
claim follows. Existing threaded cleanup and CLI tests remain active unchanged.

## Security, limitations and delivery

Both PRDs remain unchanged/untracked; synthetic arrays never leave memory during
validation. Temporary technical JSON remains outside Git. Review includes staged
content/full diff, optional dependency purpose/version/license/source, ignored
media venv, all history to push and document-container members. No secrets,
recordings, private endpoints, new listeners, deployment, paid service, license
selection or public publication is introduced. GitHub remains private.

One meaningful Stage 3/4 commit is proposed after acceptance:
`feat: validate stamped synthetic video frame lineage`. Its exact SHA, remote
verification and two-version CI follow delivery and belong in the final technical
completion report. No extra Stage 4 commit is manufactured.

PASS is scoped to the chosen color/PNG path, source-generated marker and controlled
fault models. JPEG/video-codec marker survival, arbitrary resizing/cropping,
clock/capture semantics, independent application value and Windows execution are
not verified. A separate original Stage 5 repetition run exposed a server-process
SIGSEGV during fixture teardown (399/400 normal controls passed); that observation
is retained and investigated separately, not relabeled as an image failure or an
accepted RTSP completion. Stage 6 remains excluded from this execution.
