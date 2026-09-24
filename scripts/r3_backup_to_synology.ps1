param(
  [string]$NasRoot = $env:R3_NAS_ROOT,
  [string]$Config = "r3_backup/config.json",
  [ValidateSet("synology_drive_sync","direct_nas")]
  [string]$DestinationKind = $(if ($env:R3_BACKUP_DESTINATION_KIND) { $env:R3_BACKUP_DESTINATION_KIND } else { "synology_drive_sync" }),
  [int]$WaitForNasReceiptSeconds = 0
)

$ErrorActionPreference = "Stop"

function Find-SynologyDriveRoot {
  $candidates = @(
    "$env:USERPROFILE\SynologyDrive\R3_BACKUP",
    "$env:USERPROFILE\Synology Drive\R3_BACKUP",
    "$env:USERPROFILE\SynologyDrive",
    "$env:USERPROFILE\Synology Drive"
  )
  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) { return $candidate }
  }
  return $null
}

if ([string]::IsNullOrWhiteSpace($NasRoot)) {
  $NasRoot = Find-SynologyDriveRoot
}

if ([string]::IsNullOrWhiteSpace($NasRoot)) {
  Write-Error "R3_NAS_ROOT non configurato. Configura Synology Drive Client con QuickConnect e scegli una cartella locale sincronizzata, oppure monta una share NAS diretta."
}

if (-not (Test-Path $NasRoot)) {
  New-Item -ItemType Directory -Path $NasRoot -Force | Out-Null
}

$probe = Join-Path $NasRoot ".r3-write-probe"
"R3 write probe $(Get-Date -Format o)" | Set-Content -Path $probe -Encoding UTF8
if (-not (Test-Path $probe)) {
  Write-Error "La destinazione NAS/sincronizzata non è scrivibile: $NasRoot"
}
Remove-Item $probe -Force

if (Get-Command gh -ErrorAction SilentlyContinue) {
  gh auth status *> $null
  if ($LASTEXITCODE -eq 0) {
    gh auth setup-git *> $null
  }
}

python -m r3_backup.universal --config $Config --nas-root $NasRoot --destination-kind $DestinationKind
$backupExit = $LASTEXITCODE
if ($backupExit -ne 0) {
  exit $backupExit
}

$root = Join-Path $NasRoot "R3_UNIVERSAL_BACKUP"
$latest = Join-Path $root "LATEST.json"
if (-not (Test-Path $latest)) {
  Write-Error "Backup terminato senza LATEST.json: non considero il backup verificato."
}

$receipt = Get-Content $latest -Raw | ConvertFrom-Json
$receipt | ConvertTo-Json -Depth 8

if ($receipt.status -eq "NAS_VERIFIED") {
  exit 0
}
if ($receipt.status -eq "PARTIAL") {
  exit 3
}
if ($receipt.status -ne "LOCAL_VERIFIED_PENDING_NAS") {
  exit 5
}

$snapshot = Join-Path $root ("snapshots\" + $receipt.snapshot)
$nasReceipt = Join-Path $snapshot "NAS_RECEIPT.json"

if ($WaitForNasReceiptSeconds -gt 0) {
  $deadline = (Get-Date).AddSeconds($WaitForNasReceiptSeconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-Path $nasReceipt) { break }
    Start-Sleep -Seconds 5
  }
}

if (Test-Path $nasReceipt) {
  $nas = Get-Content $nasReceipt -Raw | ConvertFrom-Json
  $nas | ConvertTo-Json -Depth 8
  if ($nas.status -eq "NAS_VERIFIED" -and $nas.snapshot -eq $receipt.snapshot) {
    exit 0
  }
  exit 6
}

Write-Host "LOCAL_VERIFIED_PENDING_NAS: il backup locale è integro, ma manca ancora la ricevuta generata sul Synology."
Write-Host "Configura scripts/r3_nas_verify.sh nel Task Scheduler DSM per chiudere la verifica NAS."
exit 4
