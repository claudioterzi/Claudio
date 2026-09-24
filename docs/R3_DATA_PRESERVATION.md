# R3 Data Preservation Decision

**Decision:** no encryption layer for R³ history/backups.

R³ historical and project artifacts must remain directly readable after disaster recovery. No R³-specific master key is required to restore them.

Protection model:

- Synology account permissions and DSM security control access.
- SHA-256 manifests detect corruption or tampering.
- Git bundles preserve repository history.
- Multiple independent copies protect against device loss.
- Passwords, API keys and recovery codes are not stored in the history archive.

This avoids a catastrophic failure mode where losing one encryption key would make the entire R³ history unreadable.

**Falsification:** reconsider this policy only if a concrete threat model shows that plaintext NAS storage creates unacceptable exposure that cannot be mitigated through access control and physical/network security without harming recoverability.
