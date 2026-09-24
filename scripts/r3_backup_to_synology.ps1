param(
  [string]$NasRoot = $env:R3_NAS_ROOT,
  [string]$Config = "r3_backup/config.json"
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
  Write-Error "R3_NAS_ROOT non configurato. Configura Synology Drive Client con QuickConnect e scegli una cartella locale sincronizzata, poi imposta R3_NAS_ROOT su quella cartella."
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

python -m r3_backup.universal --config $Config --nas-root $NasRoot
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$latest = Join-Path $NasRoot "R3_UNIVERSAL_BACKUP\LATEST.json"
if (-not (Test-Path $latest)) {
  Write-Error "Backup terminato senza LATEST.json: non considero il backup verificato."
}
Get-Content $latest
