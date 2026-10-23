# Third-party dependency and license review

Reviewed 2026-10-23 for the proposed publication of the research repository.
This is an inventory of observed licenses and distribution boundaries, not a
legal opinion. On 24 October 2026 the owner explicitly confirmed ownership and
necessary rights for the original project contributions and approved MIT with
`Copyright (c) 2026 devAIsh88`. The prior ownership confirmation gate is resolved.
Dependency licenses do not establish those rights or relicense third-party code.

## Scope and method

Reviewed `pyproject.toml`, installed distribution metadata and shipped notices in
the development, optional image and disposable external-audit environments;
queried Fedora RPM license expressions; inspected the pinned FrameGrab source
license; and consulted the primary sources linked below. Exact versions describe
the reviewed installations or current direct pins, not a claim that they are the
newest or free of vulnerabilities. Security findings are a separate review.

The repository has **no mandatory third-party Python runtime dependencies**:
`project.dependencies` is empty. Ordinary source uses the standard library;
NumPy/OpenCV and GStreamer imports belong to explicitly optional experiments.
FrameGrab is imported only by the isolated external audit. Source/history review
found no vendored third-party source, binary, wheel, media asset or copied license
text in the research repository. This inspection cannot prove authorship or
exclude unknown prior claims to the original work.

Installing/importing a dependency locally, downloading an action on a CI runner,
and redistributing that dependency in this repository are different operations.
This proposal distributes the lab's source, tests and reports, not its virtual
environments, RPMs, audit checkout, third-party wheels or generated media. This
review does not clear a future bundled application, container, installer or
binary distribution. Such a change requires review of the exact bundled files,
notices and applicable source/relinking obligations.

## Core build, development and CI

| Component | Current version / scope | Observed license and primary source |
| --- | --- | --- |
| Python | Python 3.11+ target; locally 3.12.15 and system 3.14.7; interpreter and standard library supplied separately | [Python license and history](https://docs.python.org/3/license.html); PSF license terms and included historical/component notices |
| setuptools | `83.0.0`, isolated PEP 517/660 build requirement | [MIT license at v83.0.0](https://github.com/pypa/setuptools/blob/v83.0.0/LICENSE) |
| pytest | `9.0.3`, `dev` extra and CI tests | [MIT license at 9.0.3](https://github.com/pytest-dev/pytest/blob/9.0.3/LICENSE) |
| Ruff | `0.14.0`, `dev` extra and CI lint/format checks | [MIT and included third-party notices at 0.14.0](https://github.com/astral-sh/ruff/blob/0.14.0/LICENSE) |
| actions/checkout | `11bd71901bbe5b1630ceea73d27597364c9af683`, CI checkout | [MIT notice at the pinned commit](https://github.com/actions/checkout/blob/11bd71901bbe5b1630ceea73d27597364c9af683/LICENSE) |
| actions/setup-python | `a26af69be951a213d495a4c3e4e4022e16d87065`, CI interpreter setup | [MIT notice at the pinned commit](https://github.com/actions/setup-python/blob/a26af69be951a213d495a4c3e4e4022e16d87065/LICENSE) |

The release review replaces the historical setuptools 80.9.0 and pytest 8.4.2
pins with the versions above following advisory review. Historical experiment
reports retain the versions actually used. Setuptools is a build requirement,
not a runtime dependency; it was not installed in the ordinary `.venv` when
this license inventory queried its distributions. The separately retained audit
environment still contains setuptools 80.9.0 under MIT.

Observed ordinary-environment supporting distributions are packaging 26.3
([Apache-2.0 OR BSD-2-Clause](https://pypi.org/project/packaging/26.3/)), pluggy 1.6.0
([MIT](https://pypi.org/project/pluggy/1.6.0/)), iniconfig 2.3.1
([MIT](https://pypi.org/project/iniconfig/2.3.1/)), Pygments 2.21.0
([BSD-2-Clause](https://pypi.org/project/Pygments/2.21.0/)), and the installation
tool pip 26.2.1 ([MIT, with vendored notices](https://pypi.org/project/pip/26.2.1/)).
Their installed metadata/notices were inspected. These are an environment
snapshot, not new direct pins or a transitive lockfile for every platform.

## Optional synthetic image dependencies

| Component | Version and use | License evidence |
| --- | --- | --- |
| NumPy | `2.2.6`; generated image arrays in `images` extra | [NumPy license](https://numpy.org/doc/2.2/license.html): BSD-3-Clause; installed wheel's `numpy-2.2.6.dist-info/LICENSE.txt` additionally identifies bundled components |
| opencv-python-headless | `4.12.0.88`; drawing, transforms and encoding/decoding in `images` extra | [Version metadata](https://pypi.org/project/opencv-python-headless/4.12.0.88/) and [upstream licensing](https://github.com/opencv/opencv-python#licensing): OpenCV Apache-2.0, packaging scripts MIT, bundled components under their own notices |

The inspected NumPy Linux wheel notice identifies OpenBLAS (BSD-3-Clause),
LAPACK (the notice labels it BSD-3-Clause-Attribution), GCC runtime libraries
(GPL-3.0 with GCC Runtime Library Exception), and libquadmath
(LGPL-2.1-or-later). Its source-component notices also include MIT and Zlib
licenses. Describing the whole wheel simply as BSD would omit these components.

The inspected OpenCV wheel contains `LICENSE.txt` and `LICENSE-3RD-PARTY.txt`.
Its upstream packaging documentation identifies FFmpeg under LGPLv2.1 and
additional bundled libraries. Headless wheels exclude Qt GUI components.
The non-headless `opencv-python` wheel used only in the external audit has
additional Qt 5 LGPLv3 scope on Linux. The notices are retained in the separate
installed wheels; neither type of wheel is committed or redistributed here.
The packaging notice contains conditional entries for multiple platforms, so
it must not be read as proof that every listed binary is present in every wheel.

## Optional Fedora native media integration

The following are installed external Fedora packages, not project requirements
downloaded by Python CI. License expressions below are the literal RPM metadata
observed in this environment. Package-level expressions may cover utilities,
tests and multiple libraries; they are not a per-symbol analysis of this lab's
selected pipeline.

| Fedora component | Installed version | RPM license expression |
| --- | --- | --- |
| gstreamer1 | `1.28.8-1.fc44` | LGPL-2.1-or-later |
| gstreamer1-plugins-base | `1.28.8-1.fc44` | LGPL-2.1-or-later |
| gstreamer1-plugins-good | `1.28.6-1.fc44` | CC0-1.0 AND GPL-2.0-only AND LGPL-2.0-only AND LGPL-2.0-or-later AND LGPL-2.1-only AND LGPL-2.1-or-later AND xlock AND MIT AND BSD-3-Clause AND CC-BY-3.0 |
| gstreamer1-rtsp-server | `1.28.8-1.fc44` | LGPL-2.0-or-later AND LGPL-2.1-only |
| python3-gobject / python3-gobject-base | `3.56.3-1.fc44` | LGPL-2.1-or-later |
| gobject-introspection | `1.86.0-3.fc44` | GPL-2.0-or-later AND LGPL-2.0-or-later AND LGPL-2.1-or-later AND BSD-2-Clause |
| glib2 | `2.88.3-1.fc44` | LGPL-2.1-or-later |

Primary references: [GStreamer licensing](https://gstreamer.freedesktop.org/documentation/frequently-asked-questions/licensing.html),
[Fedora core package](https://packages.fedoraproject.org/pkgs/gstreamer1/gstreamer1/),
[Fedora plugins-good](https://packages.fedoraproject.org/pkgs/gstreamer1-plugins-good/gstreamer1-plugins-good/),
[Fedora RTSP server](https://packages.fedoraproject.org/pkgs/gstreamer1-rtsp-server/gstreamer1-rtsp-server/),
[PyGObject source](https://gitlab.gnome.org/GNOME/pygobject), and the installed
RPMs. Exact historical versions and selected plugins remain recorded in the
native experiment reports. No blanket statement that all GStreamer plugins have
one license, or that importing any native component licenses this repository,
is made.

## Isolated FrameGrab audit environment

The external consumer was [FrameGrab commit
17f550890b33925cbd92cf997776e64600954f87](https://github.com/groundlight/framegrab/tree/17f550890b33925cbd92cf997776e64600954f87),
version 0.15.1. Its [MIT license](https://github.com/groundlight/framegrab/blob/17f550890b33925cbd92cf997776e64600954f87/LICENSE.txt)
was inspected locally in the unchanged checkout. The project distributes its own
audit harness and observations, not FrameGrab source or binaries. The optional
audit uses the real package's public imports; preview and network discovery
dependencies are present because of upstream imports, but those features were
not exercised. Network discovery, camera access and external service calls were
not part of the experiment.

There were 35 unique installed distributions in that disposable environment.
The following inventory records the top-level distribution license from its
metadata and shipped notice where present. Each version link is the publisher's
PyPI record. This is not an exhaustive list of native libraries embedded inside
all wheels or of vendored components inside build tools.

| Distribution | Version / primary record | Observed license |
| --- | --- | --- |
| annotated-types | [0.8.0](https://pypi.org/project/annotated-types/0.8.0/) | MIT |
| ascii-magic | [2.3.0](https://pypi.org/project/ascii-magic/2.3.0/) | MIT declared by classifier/PyPI; notice limitation below |
| attrs | [26.1.0](https://pypi.org/project/attrs/26.1.0/) | MIT |
| certifi | [2026.10.19](https://pypi.org/project/certifi/2026.10.19/) | MPL-2.0 |
| charset-normalizer | [3.5.2](https://pypi.org/project/charset-normalizer/3.5.2/) | MIT |
| click | [8.1.8](https://pypi.org/project/click/8.1.8/) | BSD-3-Clause, confirmed from shipped notice |
| colorama | [0.4.6](https://pypi.org/project/colorama/0.4.6/) | BSD-3-Clause, confirmed from shipped notice |
| framegrab | [0.15.1](https://pypi.org/project/framegrab/0.15.1/) | MIT; pinned source above |
| idna | [3.20](https://pypi.org/project/idna/3.20/) | BSD-3-Clause |
| ifaddr | [0.2.0](https://pypi.org/project/ifaddr/0.2.0/) | MIT |
| imgcat | [0.5.0](https://pypi.org/project/imgcat/0.5.0/) | MIT declared by metadata; notice limitation below |
| isodate | [0.7.2](https://pypi.org/project/isodate/0.7.2/) | BSD-3-Clause, confirmed from shipped notice |
| lxml | [6.1.3](https://pypi.org/project/lxml/6.1.3/) | BSD-3-Clause; wheel includes additional notices |
| numpy | [2.2.6](https://pypi.org/project/numpy/2.2.6/) | BSD-3-Clause plus wheel notices described above |
| onvif_zeep | [0.2.12](https://pypi.org/project/onvif-zeep/0.2.12/) | MIT |
| opencv-python | [4.12.0.88](https://pypi.org/project/opencv-python/4.12.0.88/) | Apache-2.0 OpenCV / MIT packaging / bundled notices, including FFmpeg and Qt scope |
| pillow | [13.0.0](https://pypi.org/project/pillow/13.0.0/) | MIT-CMU; component notices remain applicable |
| pip | [26.0.1](https://pypi.org/project/pip/26.0.1/) | MIT plus vendored notices; installation tool |
| platformdirs | [4.13.5](https://pypi.org/project/platformdirs/4.13.5/) | MIT |
| poetry-core | [2.2.1](https://pypi.org/project/poetry-core/2.2.1/) | MIT plus vendored notices; upstream build backend |
| pydantic | [2.12.3](https://pypi.org/project/pydantic/2.12.3/) | MIT |
| pydantic_core | [2.41.4](https://pypi.org/project/pydantic-core/2.41.4/) | MIT |
| pytest-runner | [4.5.1](https://pypi.org/project/pytest-runner/4.5.1/) | MIT confirmed from shipped notice; legacy build support |
| pytz | [2026.5](https://pypi.org/project/pytz/2026.5/) | MIT |
| PyYAML | [6.0.3](https://pypi.org/project/PyYAML/6.0.3/) | MIT |
| requests | [2.34.2](https://pypi.org/project/requests/2.34.2/) | Apache-2.0 |
| requests-file | [3.0.1](https://pypi.org/project/requests-file/3.0.1/) | Apache-2.0 |
| requests-toolbelt | [1.0.0](https://pypi.org/project/requests-toolbelt/1.0.0/) | Apache-2.0 |
| setuptools | [80.9.0](https://pypi.org/project/setuptools/80.9.0/) | MIT plus vendored notices; historical audit build tool |
| typing-inspection | [0.4.4](https://pypi.org/project/typing-inspection/0.4.4/) | MIT |
| typing_extensions | [4.16.0](https://pypi.org/project/typing-extensions/4.16.0/) | PSF-2.0 |
| urllib3 | [2.8.0](https://pypi.org/project/urllib3/2.8.0/) | MIT |
| wheel | [0.45.1](https://pypi.org/project/wheel/0.45.1/) | MIT plus vendored packaging notices; build tool |
| WSDiscovery | [2.1.2](https://pypi.org/project/WSDiscovery/2.1.2/) | LGPL-3.0-or-later |
| zeep | [4.3.2](https://pypi.org/project/zeep/4.3.2/) | MIT |

Two limitations remain explicit. `imgcat` 0.5.0 declares MIT, but the reviewed
source archive/installed distribution has no standalone license file.
`ascii-magic` 2.3.0 has an installed `License: UNKNOWN` field, an MIT classifier
and a [publisher statement of MIT licensing](https://pypi.org/project/ascii-magic/2.3.0/#description),
but no standalone license file in the installed wheel. These are incomplete
notice packaging observations, not conclusions that the projects are unlicensed
or that redistribution has been cleared. Neither dependency is bundled here;
obtain and verify the applicable notices before any future redistribution.

## Temporary release-audit tools

The review used [detect-secrets 1.5.0](https://github.com/Yelp/detect-secrets/blob/v1.5.0/LICENSE)
and [pip-audit 2.9.0](https://github.com/pypa/pip-audit/blob/v2.9.0/LICENSE), both
Apache-2.0 according to installed metadata and upstream notices. They and their
dependencies remain in a disposable tools environment outside this repository.
They are not added to package dependencies or CI and are not redistributed.
Their transitive environments are not claimed as a fully audited distributable
software bill of materials.

## Publication decision boundary

The inspected repository does not redistribute the third-party distributions
listed above. No third-party code inclusion requiring removal was identified by
this review. However, this finding does not establish copyright ownership of
the lab's original work or permission from an employer, contributor or other
rights holder. The owner has now explicitly supplied the required original-work
rights confirmation and accepted historical contact/path disclosure. The original
repository material is MIT licensed; security and CI remain independent publication
gates. No unresolved redistribution blocker was identified for this source-only
release. The dependency notice limitations above still restrict any future bundling.

If the project later bundles dependencies, ships binaries or containers, copies
upstream code, or changes its supported codecs, repeat this review for that exact
artifact and retain all applicable third-party notices. The present review
supports a source-and-documentation release assessment only.
