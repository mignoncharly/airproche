#!/usr/bin/env bash
set -euo pipefail
umask 0077

: "${DATABASE_URL:?DATABASE_URL is required.}"
: "${BACKUP_ENCRYPTION_KEY:?BACKUP_ENCRYPTION_KEY is required.}"
BACKUP_DIR=${BACKUP_DIR:-/home/mignon/airproche/backups}
BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-14}
if [[ ! "$BACKUP_RETENTION_DAYS" =~ ^[0-9]+$ ]] || (( BACKUP_RETENTION_DAYS < 1 )); then
  printf 'BACKUP_RETENTION_DAYS must be a positive integer.\n' >&2
  exit 1
fi
for command in pg_dump sha256sum flock openssl; do
  command -v "$command" >/dev/null || { printf 'Missing required command: %s\n' "$command" >&2; exit 1; }
done

mapfile -t database < <(DATABASE_URL_TO_PARSE="$DATABASE_URL" python3 - <<'PY'
import os
from urllib.parse import unquote, urlsplit

parsed = urlsplit(os.environ["DATABASE_URL_TO_PARSE"])
if parsed.scheme not in {"postgres", "postgresql"}:
    raise SystemExit("DATABASE_URL must use PostgreSQL.")
if parsed.hostname not in {"127.0.0.1", "localhost"}:
    raise SystemExit("Production backup is restricted to local PostgreSQL.")
if unquote(parsed.path.lstrip("/")) != "airproche":
    raise SystemExit("Production backup is restricted to the airproche database.")
print(parsed.hostname)
print(parsed.port or 5432)
print(unquote(parsed.username or ""))
print(unquote(parsed.password or ""))
PY
)
if [[ "${database[2]}" != airproche ]] || [[ -z "${database[3]}" ]]; then
  printf 'DATABASE_URL must use the dedicated airproche role.\n' >&2
  exit 1
fi

install -d -m 0700 "$BACKUP_DIR"
exec 9>"$BACKUP_DIR/.backup.lock"
if ! flock -n 9; then
  printf 'Another Airproche backup is already running.\n' >&2
  exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
final="$BACKUP_DIR/airproche-$timestamp.dump.enc"
plain="$BACKUP_DIR/.airproche-$timestamp.dump.tmp"
encrypted="$BACKUP_DIR/.airproche-$timestamp.dump.enc.tmp"
cleanup() { rm -f "$plain" "$encrypted"; }
trap cleanup EXIT INT TERM

PGPASSWORD="${database[3]}" pg_dump \
  --host="${database[0]}" --port="${database[1]}" --username="${database[2]}" \
  --dbname=airproche --format=custom --no-owner --no-privileges --file="$plain"
chmod 0600 "$plain"
BACKUP_ENCRYPTION_KEY="$BACKUP_ENCRYPTION_KEY" openssl enc -aes-256-cbc -pbkdf2 -salt \
  -in "$plain" -out "$encrypted" -pass env:BACKUP_ENCRYPTION_KEY
rm -f "$plain"
chmod 0600 "$encrypted"
mv "$encrypted" "$final"
sha256sum "$final" >"$final.sha256"
chmod 0600 "$final.sha256"
trap - EXIT INT TERM

find "$BACKUP_DIR" -maxdepth 1 -type f -name 'airproche-*.dump.enc' -mtime "+$BACKUP_RETENTION_DAYS" -delete
find "$BACKUP_DIR" -maxdepth 1 -type f -name 'airproche-*.dump.enc.sha256' -mtime "+$BACKUP_RETENTION_DAYS" -delete
printf 'Encrypted Airproche backup created: %s\n' "$(basename "$final")"
