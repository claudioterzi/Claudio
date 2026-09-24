#!/bin/sh
# R3 UNIVERSAL BACKUP/1 — NAS-side byte verification.
# Run this on the Synology with the R3_UNIVERSAL_BACKUP directory as argument.
set -eu

ROOT="${1:-}"
if [ -z "$ROOT" ] || [ ! -d "$ROOT/snapshots" ]; then
  echo "usage: r3_nas_verify.sh /path/to/R3_UNIVERSAL_BACKUP" >&2
  exit 2
fi

sha_cmd() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$@"
  elif command -v busybox >/dev/null 2>&1; then
    busybox sha256sum "$@"
  else
    echo "sha256sum unavailable" >&2
    exit 3
  fi
}

SNAPSHOT="$(ls -1dt "$ROOT"/snapshots/* 2>/dev/null | head -n 1 || true)"
if [ -z "$SNAPSHOT" ] || [ ! -d "$SNAPSHOT" ]; then
  echo "no snapshot found" >&2
  exit 4
fi

if [ ! -f "$SNAPSHOT/SHA256SUMS" ]; then
  echo "SHA256SUMS missing" >&2
  exit 5
fi

cd "$SNAPSHOT"
if ! sha_cmd -c SHA256SUMS >/tmp/r3_nas_verify.log 2>&1; then
  STATUS="FAILED"
  VERIFIED="false"
else
  STATUS="NAS_VERIFIED"
  VERIFIED="true"
fi

STAMP="$(basename "$SNAPSHOT")"
CHECKSUM="$(sha_cmd SHA256SUMS | awk '{print $1}')"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat > NAS_RECEIPT.json.tmp <<EOF
{
  "protocol": "R3-UNIVERSAL-BACKUP/1",
  "snapshot": "$STAMP",
  "status": "$STATUS",
  "verified_on_nas": $VERIFIED,
  "verification_scope": "physical_NAS_byte_presence_and_SHA256",
  "sha256sums_sha256": "$CHECKSUM",
  "verified_at": "$NOW"
}
EOF
mv NAS_RECEIPT.json.tmp NAS_RECEIPT.json

cp NAS_RECEIPT.json "$ROOT/NAS_LATEST.json.tmp"
mv "$ROOT/NAS_LATEST.json.tmp" "$ROOT/NAS_LATEST.json"

cat NAS_RECEIPT.json
[ "$STATUS" = "NAS_VERIFIED" ]
