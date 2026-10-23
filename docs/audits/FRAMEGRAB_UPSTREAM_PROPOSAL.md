# Private upstream documentation proposal — not posted

Target: https://github.com/groundlight/framegrab at
`17f550890b33925cbd92cf997776e64600954f87`, README GStreamer support check.
No issue, comment or pull request has been sent. Owner approval is required before
any external submission. No maintainer acknowledgment exists.

Proposed title: **Check the enabled OpenCV GStreamer value in the README example**

The README's membership check for `GStreamer` returns True when the OpenCV build
information contains `GStreamer: NO`. In the audited opencv-python 4.12.0.88 wheel,
this prints a positive support message even though the backend is unavailable.
The runtime `_check_gstreamer_support` guard already rejects the unavailable build;
this proposal corrects the installation verification instructions only.

Reproduce in an environment with that wheel:

```sh
python - <<'PY'
import cv2
build = cv2.getBuildInformation()
print('substring predicate:', 'GStreamer' in build)
print(next(line.strip() for line in build.splitlines() if 'GStreamer:' in line))
PY
```

Observed: substring predicate True; actual GStreamer build value NO.
Suggested replacement, preserving uncertainty if the line is absent:

```python
import cv2

line = next(
    (s.strip() for s in cv2.getBuildInformation().splitlines()
     if s.strip().startswith('GStreamer:')),
    None,
)
print(line or 'GStreamer build information unavailable')
```

The replacement displays the actual enabled/disabled value and makes no claim
about whether the necessary runtime plugins are installed. A second runtime
pipeline check may still be necessary. It was checked locally against the actual
NO build line and representative YES/NO/missing input; no external RTSP test or
runtime defect is claimed.
