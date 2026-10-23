# Public release readiness

Audit performed 23 October 2026; final private checkpoint reviewed 24 October 2026.
Scope: `devAIsh88/video-freshness-lab`, default
branch `main`. Inspected starting revision:
`58f2dd2661cecae27dc4b502aab8d8b03a8659a5`.

**Decision: PRIVATE — PUBLICATION BLOCKED.** Release preparation does not establish
copyright ownership. The explicit ownership confirmation and acceptance of
existing historical personal metadata remain pending. No visibility change or
MIT grant has been made. The PIVOT research conclusion and unmet external gates
are unchanged; this review concerns publishing the source recipe/toolkit, not
publishing a package or claiming production readiness.

This is the pre-commit review record. Post-commit SHA, remote synchronization and
new CI results must be verified after delivery and reported with that delivery;
this document cannot contain its own commit SHA or subsequent CI result.

## Release checklist

| Gate | Status | Evidence / remaining action |
| --- | --- | --- |
| Exact repository/account/default branch | PASS | Authenticated `devAIsh88`; HTTPS origin is the intended repository; API says private, main, administrator access |
| Initial Git synchronization | PASS | Local HEAD and origin/main match the starting SHA; only main advertised, no tags; original foundation retained |
| Copyright authority | BLOCKED | Sole Git identity and no conflicting notices found, but owner has not explicitly confirmed authority over all original code, tests, documentation and assets, including contributor/employer/institution rights |
| MIT license and packaging declaration | BLOCKED | Owner selected MIT and `Copyright (c) 2026 devAIsh88`; root LICENSE still grants no open-source license pending ownership confirmation; no MIT SPDX claim added |
| Third-party redistribution review | PASS | No vendored source, binaries, external fixtures or media found; dependency imports/references reviewed separately in [license review](THIRD_PARTY_LICENSE_REVIEW.md); this does not resolve original ownership |
| Current source security review | PASS | Established scanner plus targeted review; hash/pin candidates explained; no credentials or private camera connections identified |
| Complete reachable history review | PASS | 14 commits, 132 unique blobs, all UTF-8 text, all refs and reflog commits covered; no hidden branch/tag history advertised |
| Historical personal-data disclosure | BLOCKED | Existing author/committer contact metadata and a personal absolute checkout path would become public; owner acceptance is pending; values omitted here; no history rewriting authorized |
| Available Actions logs/artifacts review | PASS | All 14 run attempts downloaded, 52 log files reviewed; zero retained artifacts; no unexplained credentials/personal paths found |
| Original PRD exclusion | PASS | Both originals unchanged and untracked, absent from all historical paths and review wheel; DOCX container inspected locally without redistributing it |
| Source/documentation review | PASS | No research-result changes; corrected private-original links, stale contribution/security guidance and current demo path; linked release status separately from historical research conclusions |
| Dependency advisory review | PASS | Patched pytest/build tooling and optional-environment pip; final core/build and image inventories have no known advisories in this scan; scope/limits below |
| GitHub Actions configuration | PASS | Python 3.11/3.12, read-only permissions, full action SHAs, 10-minute job timeout, no secrets/publishing/deployment; repository now allows only the two reviewed action SHAs |
| Local mandatory checks | PASS | Ruff lint/format, 305 Python tests, pip check and diff checks passed; staged checks must also pass before commit |
| Optional media regression checks | PASS | Images 6 methods; native 3 methods/30 cases; RTSP 3 methods/26 cases; TCP faults 2 methods/37 cases; separate from CI |
| Editable install and local wheel | PASS | Pinned build backend succeeds; Metadata 2.4; 25 wheel members, no runtime requirements, private originals or native/media binaries; license expression deliberately absent |
| New private push and CI | NOT VERIFIED | Pending at this pre-commit snapshot; verify exact new SHA and completed successful jobs on 3.11 and 3.12 after push |
| Post-publication security settings and rendered pages (follow-up, not a pre-publication gate) | NOT VERIFIED | Repository remains private; private vulnerability reporting and applicable free public secret protections must be enabled/verified during any later authorized transition |
| Public publication | BLOCKED | Ownership and historical-data decisions unresolved; do not execute the visibility command |

## Security and history method

Fetched all remote heads and tags without pruning or rewriting. Inspected branches,
tags, commits, reflogs, reachable tree/blob objects, contributor metadata, current
files, ignored-file categories, workflow, document containers and dependency
boundaries. The original PRD hashes match their foundation record. No original
PRD, environment, credential file, recording, archive or binary appears in the
reachable Git blobs. The review wheel contains only first-party Python and
package metadata, including the current no-license-grant notice. `git fsck` also
identified four local dangling blobs: all were UTF-8 drafts/configuration text,
not either original PRD. Targeted inspection and an additional established scan
found no credential candidates. These unreachable blobs are not included in a
normal branch push; none was deleted or rewritten.

Used [Yelp detect-secrets](https://github.com/Yelp/detect-secrets) 1.5.0 in an
isolated temporary environment, with `--no-verify` so candidates were not sent
for live credential validation. Current scan: 13 potential matches, all artifact
hashes or pinned commits/source-integrity checks. History export: 133 files
(132 blobs plus commit metadata), the same 13 explained candidates. Actions: all
52 files selected, zero candidates. Targeted checks supplemented entropy scanning
for credentials, private keys, private addresses, non-loopback RTSP endpoints,
embedded URL authentication, personal data and prohibited file types.

An initial absolute-path scanner invocation silently selected zero exported
files. It was invalid evidence and was replaced by runs **from inside each export
directory**, with `scan --no-verify --all-files .`; file coverage was checked.
Manual Actions review found hosted-runner paths, masked tokens and expected
credential setup/cleanup only. No credential rotation was identified as necessary.
Automated scans and manual screening cannot prove that undiscovered secrets or
ownership issues do not exist.

Historical contact/path metadata is a disclosure decision, not an exposed access
credential. Removing the current demo path does not remove the older value from
history. The existing history has not been rewritten, and nothing has been
removed from GitHub Actions to conceal evidence.

## Dependencies and changes

The core still has no runtime dependencies. Exact reviewed dependency versions
were inventoried from the environments, with the isolated build requirement
added explicitly. [PyPA pip-audit](https://github.com/pypa/pip-audit) 2.9.0 queried
the advisory database using those exact pins (`--no-deps --disable-pip`). This
checks the enumerated installed/build packages; it is not a transitive lockfile
or a native-code vulnerability analysis.

| Finding | Change | Evidence |
| --- | --- | --- |
| pytest 8.4.2: CVE-2025-71176 / PYSEC-2026-1845 | Development pin and local tool changed to 9.0.3 | [Reviewed advisory](https://github.com/advisories/GHSA-6w46-j5rx-g56g); full suite remains 305 passing |
| setuptools 80.9.0: CVE-2026-59890 / PYSEC-2026-3447 | Isolated build pin changed to 83.0.0 | [PyPA advisory](https://github.com/pypa/advisory-database/blob/main/vulns/setuptools/PYSEC-2026-3447.yaml); editable and wheel builds passed |
| Optional image environment pip 26.0.1: four advisories | Upgraded only that environment to 26.2.1 | PYSEC-2026-196, -2875, -2876, -3721; image inventory rescanned clean |

Final advisory inventories: eight core/build/tool packages and three image/tool
packages, zero known vulnerabilities reported. Versions used in historical
experiment reports remain unchanged as historical evidence. Fedora native RPMs
and the disposable historical FrameGrab environment were license-reviewed, not
certified free of vulnerabilities by this Python advisory scan. Audit tooling
lives outside Git; no new runtime dependency was introduced.

## Verification performed

Fedora 44, project Python 3.12.15, pytest 9.0.3 and Ruff 0.14.0:

```sh
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pip wheel --no-deps --wheel-dir /tmp/vfl-release-wheel .
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -v
.venv/bin/python -m pip check
git diff --check
git diff --cached --check
```

Ruff: all checks passed, 40 Python files formatted. Pytest: 305 passed in 2.44 s; final pre-commit repeat: 305 passed in 1.65 s.
No test was removed or weakened. Packaging inventory and metadata were inspected;
MIT metadata validation remains blocked on legal confirmation. Across the tracked
and proposed documentation, 144 relative links/heading anchors resolved inside
the publication tree; all 100 external source/documentation URLs returned successful
HTTP responses. The nine repository URLs require private access, and the security
reporting route is explicitly unavailable until enabled on a public repository.
Rendered public pages cannot be verified before publication. The supported
modern form, once authorized, is `license = "MIT"` with `license-files = ["LICENSE"]`.
It is [supported by the selected backend](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/).

Executed the default simulation, all-suite JSON, filtered reconnect, threaded
normal/slow/idle, stamped-image single repetition and six image integration
methods. Also ran all existing native/RTSP/fault integration suites:

```sh
venv-media/bin/python -m unittest discover -s integration -p test_stamped_images.py -v
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_gstreamer_native.py -v
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_rtsp_transport.py -v
PYTHONPATH=src /usr/bin/python3 -m unittest discover -s integration -p test_transport_faults.py -v
```

Native suite: 3 methods, 30 cases, 4.659 s. RTSP: 3 methods, 26 cases, 17.337 s.
Fault suite: 2 methods, 37 cases, 28.076 s. Tests positively check expected worker
termination, owned child exit, pipeline NULL and owned listening-port release.
A subsequent host process check found no remaining matching experiment workers.
GstRtspServer imports through `/usr/bin/python3`; RPM is
`gstreamer1-rtsp-server-1.28.8-1.fc44.x86_64`. This environment sees the Fedora host
installation. No large research cohort was repeated, and these regression counts
are not added to historical reliability denominators or claimed as physical
camera freshness evidence.

## GitHub settings and visibility consequences

Verified description: “Reproducible Python experiments for video freshness, RTSP
buffering, recovery and session reliability.” Topics: python, rtsp, gstreamer,
computer-vision, video-streaming, pytest, fault-injection, reliability-engineering.
No homepage was invented.

Applied and read back:

- Actions limited to the existing checkout/setup-python full SHAs; SHA pinning
  required. Other GitHub-owned/verified actions are not implicitly allowed.
  Updating either action requires reviewing and updating this allowlist too.
  The CI install step explicitly selects reviewed pip 26.2.1 and now also runs
  `pip check`; ordinary CI still excludes native integration tests.
- Dependabot alerts and dependency graph enabled; SBOM endpoint works and open
  alerts were empty at review. An empty alert list is not a substitute for the
  explicit local advisory scan or a guarantee that graph ingestion is complete.
- Existing read-only workflow defaults and inability to approve PRs preserved.

Only the owner has collaborator access; no invitations, PRs, issues, webhooks,
deployments, environments, releases, tags or retained artifacts were found.
Branch protection/rulesets require a paid plan or public visibility in the current
configuration. Secret scanning/private vulnerability reporting were unavailable
in this private configuration. No plan was upgraded. Public-only features and
fork-workflow approval policy remain follow-up work if publication later passes.

[GitHub's visibility documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility)
was evaluated: changing private to public exposes code/history and Actions logs,
permits public forks, publishes activity, can detach private forks, erases existing
stars/watchers, and disables push rulesets. There are currently no forks. Those
consequences make the historical personal-data decision necessary; current-tree
cleanup alone is insufficient. No visibility command has been executed.

## Remaining release actions

1. Obtain explicit authority to apply MIT to all original material and explicit
   acceptance of the already-identified historical contact/path disclosure.
2. If both confirmations arrive, install the unmodified standard MIT text with
   the selected attribution, add SPDX packaging metadata, update current status
   documents and rebuild/review the artifact. Do not relicense dependency code.
3. Commit only reviewed changes, push privately, verify exact remote SHA and
   completed Python 3.11/3.12 CI, then review that new run's logs as well.
4. Re-evaluate every mandatory pre-publication gate against the exact repository and reviewed
   revision. If any remains FAIL, BLOCKED or NOT VERIFIED, stay private.
5. Only when all mandatory gates pass, execute the owner's exact visibility
   command, verify public identity/README/LICENSE/default branch and links, and
   enable/verify supported free public security features. No package, release,
   deployment, paid service or unrelated repository change is authorized.
