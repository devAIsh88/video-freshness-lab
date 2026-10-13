# Security policy

This repository currently contains research scaffolding, not a network client
or a production security boundary. There are no supported production releases,
camera authentication features, encryption guarantees, or safety guarantees.
An eventual freshness verdict cannot establish image integrity, prevent source
spoofing, or certify a clinical or industrial decision.

## Report privately

For a security-sensitive finding, contact the repository owner through a verified
private channel. Once a GitHub repository exists, use its **Security → Report a
vulnerability** facility if the owner has enabled private reporting. No private
contact address or reporting facility has been configured yet; the owner must
establish one before public release. Do not post secrets or exploit details in a
public issue while arranging a channel. Ordinary bugs can be reported publicly
using synthetic reproductions after repository publication is approved.

Provide the affected revision, impact, and a minimal sanitized synthetic
reproduction. Arrange disclosure timing with the owner. No response SLA is
promised at this stage. Do not transmit camera credentials or private recordings.

## Sensitive connection data

Validation uses synthetic data only. This milestone needs no real credentials
and does not read `.env` files. Never include authentication strings, private
RTSP URLs, camera addresses, hostnames, personal footage, or patient data in
code, documentation, logs, issue reports, screenshots, or CI output. Later local
experiments must keep private configuration and media outside tracked files.
Diagnostics should use opaque session labels and sequence/event identifiers.

Review staged paths and contents, including DOCX metadata, links, and embedded
assets, before any push. Run a repository-wide secret scan before first public
push and after configuration changes. Pattern scans and `.gitignore` cannot
prove the absence of secrets. If a credential is exposed, revoke or rotate it
and notify the owner privately; deleting the working file alone is insufficient.
Coordinate any history cleanup with the owner; do not rewrite history unaided.

## CI boundary

CI uses read-only contents permissions, ordinary pull-request events, pinned
action commits, and checkout without persisted credentials. It requires no
secrets and performs no publishing, artifact upload, or deployment. Do not use
`pull_request_target`, privileged workflows for untrusted PR code, write tokens,
cloud credentials, or self-hosted runners for untrusted contributions. Dependency
installation still executes third-party tooling; review version updates and
keep this boundary narrow. No paid third-party security service is required.
