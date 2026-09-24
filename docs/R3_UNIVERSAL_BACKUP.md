# R3 UNIVERSAL BACKUP/1 — Synology primary vault

Origin: **Claudio Terzi [CT-LGAI-001]**

## Goal

GitHub is a replaceable source, not the survival point. The Synology NAS holds a recoverable archive that can recreate Git repositories even if GitHub is unavailable.

Per repository, the archive can include:

- complete Git object history and all refs through a mirror clone;
- a standalone .bundle verified by git bundle verify;
- Git LFS object store when Git LFS is available;
- wiki bundle when a wiki exists;
- GitHub metadata export when gh is authenticated: repository metadata, issues, comments, pull requests, releases, labels, milestones, workflows and workflow runs;
- only the names of GitHub secrets/variables, never their values;
- SHA-256 manifest and SHA256SUMS;
- immutable receipts.

A repository is never counted as complete unless git fsck and bundle verification pass.

## Two verification levels

R3 deliberately separates local integrity from physical NAS persistence.

**direct_nas**: R3 writes to a mounted Synology share. Because hashing is performed against the mounted NAS files themselves, a complete run may become NAS_VERIFIED immediately.

**synology_drive_sync**: R3 writes into a local Synology Drive synchronized folder. A successful PC run is only LOCAL_VERIFIED_PENDING_NAS. It becomes NAS_VERIFIED only after a verifier running on the Synology recomputes SHA-256 from the files physically present on the NAS and writes NAS_RECEIPT.json.

This prevents a sync client from being treated as proof that synchronization has already completed.

## QuickConnect setup

Keep QuickConnect/DSM credentials out of source code and out of the Git repository.

On the Dell:

1. Open Synology Drive Client.
2. Create a sync task using your QuickConnect ID and authenticate interactively.
3. Choose/create a dedicated NAS folder such as R3_BACKUP.
4. Choose the corresponding local synchronized folder.
5. Set R3_NAS_ROOT to that local folder.

Example only:

~~~powershell
$env:R3_NAS_ROOT="$env:USERPROFILE\SynologyDrive\R3_BACKUP"
$env:R3_BACKUP_DESTINATION_KIND="synology_drive_sync"
~~~

Run:

~~~powershell
powershell -ExecutionPolicy Bypass -File scripts/r3_backup_to_synology.ps1
~~~

If the folder is an actual mounted Synology SMB share instead:

~~~powershell
$env:R3_NAS_ROOT="Z:\R3_BACKUP"
$env:R3_BACKUP_DESTINATION_KIND="direct_nas"
powershell -ExecutionPolicy Bypass -File scripts/r3_backup_to_synology.ps1
~~~

## NAS-side verifier

Copy scripts/r3_nas_verify.sh to the NAS or make it available inside the R3 backup share. In DSM Task Scheduler, run it on the directory that contains R3_UNIVERSAL_BACKUP.

Example command shape:

~~~sh
/bin/sh /volume1/R3_BACKUP/scripts/r3_nas_verify.sh /volume1/R3_BACKUP/R3_UNIVERSAL_BACKUP
~~~

The exact /volumeN/share path depends on the NAS configuration and must be verified in DSM rather than guessed.

The verifier:

1. finds the newest snapshot;
2. runs SHA-256 verification against SHA256SUMS on the NAS itself;
3. writes NAS_RECEIPT.json inside that snapshot;
4. writes NAS_LATEST.json at the backup root;
5. returns failure if any byte differs.

The Windows wrapper can optionally wait for the receipt to sync back:

~~~powershell
powershell -ExecutionPolicy Bypass -File scripts/r3_backup_to_synology.ps1 -WaitForNasReceiptSeconds 300
~~~

Without a NAS receipt, R3 reports LOCAL_VERIFIED_PENDING_NAS and does not call the backup NAS_VERIFIED.

## Required local tools

- Git
- Python 3.11+
- GitHub CLI gh authenticated for private repositories and metadata export
- Git LFS if any project uses LFS
- Synology Drive Client when using QuickConnect sync

Verify:

~~~powershell
git --version
gh auth status
git lfs version
python --version
~~~

The wrapper runs gh auth setup-git when gh is already authenticated, so private Git clones can use the GitHub CLI credential helper without embedding credentials.

## Restore without GitHub

Verify a snapshot:

~~~powershell
python -m r3_backup.restore "X:\R3_UNIVERSAL_BACKUP\snapshots\20260924T..." --verify-only
~~~

Restore a repository entirely from its NAS bundle:

~~~powershell
python -m r3_backup.restore "X:\R3_UNIVERSAL_BACKUP\snapshots\20260924T..." --repository "claudioterzi/Claudio" --destination "C:\R3-RESTORE\Claudio"
~~~

The restore command verifies snapshot hashes, verifies the Git bundle, clones it and runs git fsck --full.

## Repository discovery

r3_backup/config.json contains the known R3 repositories and owner names. When gh is authenticated, the backup also enumerates accessible repositories for the configured owners so new repositories are not silently omitted.

## Scheduling

The primary backup must run from the Dell/NAS path, not from a GitHub Action. A GitHub Action would keep disaster recovery dependent on the platform being backed up.

Recommended operational policy:

- daily mirror snapshot;
- NAS-side verification after each synchronized snapshot;
- monthly restore drill into a disposable directory;
- Synology Hyper Backup to a second independent/off-site destination for the third 3-2-1 copy.

## Limits in v1

GitHub does not reveal secret values, so secret values cannot be reconstructed from GitHub exports. Keep API credentials/recovery keys in a separate encrypted secret vault. External package/container registries and arbitrary externally hosted issue attachments need dedicated exporters in a later version.
