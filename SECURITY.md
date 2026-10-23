# Security policy

Video Freshness Lab is a research recipe and validation toolkit. Optional local
experiments contain RTSP clients, a synthetic server and a bounded loopback fault
injector. There are no supported production releases, camera authentication
features, image-integrity guarantees or safety certifications. A freshness verdict
cannot establish source authenticity or certify a clinical or industrial decision.

## Report privately

Use this repository's **Security → Report a vulnerability** facility when enabled:
[private report](https://github.com/devAIsh88/video-freshness-lab/security/advisories/new).
GitHub provides this facility for public repositories; it is currently unavailable
while this repository is private. Enabling and verifying it is part of the
conditional publication follow-up in the [release report](docs/release/PUBLIC_RELEASE_READINESS.md).

If the facility is unavailable, ask the owner to arrange a private channel without
including sensitive details. For a public repository, a minimal issue requesting
private contact is the [GitHub-documented fallback](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/report-privately).
Do not post exploit details, credentials or recordings in an issue. No personal
security email address or response SLA is promised.

Provide the affected revision, impact and a sanitized synthetic reproduction.
Arrange disclosure timing with the owner. Ordinary bugs can use normal issue
reports without private connection information.

## Sensitive data and dependency review

Validation uses synthetic media and owned IPv4 loopback sockets only. Never add
credentials, private camera URLs, personal footage, confidential documents,
environments or generated binaries to Git. Original PRDs stay local and untracked.

Review staged contents, complete reachable history, document containers and
available Actions logs before public publication. A clean automated scan supports
review but cannot prove the absence of secrets. If a credential is exposed, rotate
or revoke it; deleting its working copy does not remove historical exposure.
Coordinate remediation with the owner and do not rewrite history unaided.

Keep development installers patched and review dependency advisories. Optional
native libraries retain their own licenses and security maintenance requirements;
the repository does not redistribute their binaries. See the
[third-party review](docs/release/THIRD_PARTY_LICENSE_REVIEW.md).

## CI boundary

CI uses read-only permissions, ordinary pull-request events, pinned action commits
and checkout without persisted credentials. It requires no secrets and performs
no publishing, artifact upload or deployment. Do not use `pull_request_target`,
privileged workflows for untrusted PR code, write tokens, cloud credentials or
self-hosted runners for untrusted contributions. Dependency installation executes
third-party tooling; review updates and keep this boundary narrow. No paid service
is required.
