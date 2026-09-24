# R3 UNIVERSAL BACKUP/1 — Synology primary vault

Origin: **Claudio Terzi [CT-LGAI-001]**

## Goal

GitHub is a replaceable source, not the survival point. The Synology NAS holds a recoverable archive that can recreate Git repositories even if GitHub is unavailable.

The backup contains, per repository:

- complete Git object history and all refs through a mirror clone;
- a standalone .bundle verified by git bundle verify;
- Git LFS object store when Git LFS is available;
- wiki bundle when a wiki exists;
- GitHub metadata export when gh is authenticated: repository metadata, issues, comments, pull requests, releases, labels, milestones, workflows and workflow runs;
- only the names of GitHub secrets/variables, never their values;
- SHA-256 manifest written on the NAS;
- LATEST.json and immutable receipts.

A run is VERIFIED only if every requested repository completes. Partial runs are recorded as PARTIAL, never silently promoted.

## Synology / QuickConnect setup

Do **not** place DSM/QuickConnect passwords in this repository, environment files committed to Git, or GitHub Secrets for this purpose.

Use Synology Drive Client on the Dell:

1. Install/open **Synology Drive Client**.
2. Create a sync task to the Synology NAS using its QuickConnect ID.
3. Authenticate interactively in Synology Drive Client.
4. Choose or create a NAS folder dedicated to R3, for example R3_BACKUP.
5. Choose the corresponding local synchronized folder.
6. Set R3_NAS_ROOT to that **local synchronized folder**.

Example only:

~~~powershell
$env:R3_NAS_ROOT="$env:USERPROFILE\SynologyDrive\R3_BACKUP"
~~~

The supplied PowerShell wrapper also tries common Synology Drive locations automatically:

~~~powershell
powershell -ExecutionPolicy Bypass -File scripts/r3_backup_to_synology.ps1
~~~

QuickConnect credentials stay inside Synology Drive Client / Windows credential storage; R3 only sees the synchronized filesystem path.

## Required local tools

- Git
- Python 3.11+
- GitHub CLI gh authenticated for private repositories and metadata export
- Git LFS if any project uses LFS

Verify:

~~~powershell
git --version
gh auth status
git lfs version
python --version
~~~

## Run

~~~powershell
powershell -ExecutionPolicy Bypass -File scripts/r3_backup_to_synology.ps1
~~~

Or directly:

~~~powershell
python -m r3_backup.universal --nas-root "$env:R3_NAS_ROOT"
~~~

## Restore without GitHub

Verify a snapshot:

~~~powershell
python -m r3_backup.restore "X:\R3_UNIVERSAL_BACKUP\snapshots\20260924T..." --verify-only
~~~

Restore a repository entirely from its NAS bundle:

~~~powershell
python -m r3_backup.restore "X:\R3_UNIVERSAL_BACKUP\snapshots\20260924T..." --repository "claudioterzi/Claudio" --destination "C:\R3-RESTORE\Claudio"
~~~

The restore command verifies the snapshot hashes, verifies the Git bundle, clones it and runs git fsck --full.

## Scheduling

Run the wrapper locally with Windows Task Scheduler. A GitHub Action is **not** the primary backup path because it would keep the backup dependent on GitHub and would require remote access to the home NAS.

Recommended schedule:

- mirror snapshot daily;
- monthly restore drill to a disposable folder;
- Synology Hyper Backup from the NAS to a second independent destination for the third 3-2-1 copy.

## Important limits in v1

GitHub does not reveal secret values, so secret values are not reconstructable from a GitHub backup. Keep recovery keys/API credentials in a separate encrypted secret vault. Package/container registries and arbitrary externally-hosted issue attachments need dedicated exporters in a later version.
