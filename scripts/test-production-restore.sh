#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  printf 'Run this script with sudo.\n' >&2
  exit 1
fi
APP_ROOT=/home/mignon/airproche
ENV_FILE="$APP_ROOT/shared/.env.production"
RESTORE_DB=airproche_restore_test
[[ -f "$ENV_FILE" ]] || { printf 'Production environment is missing.\n' >&2; exit 1; }
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
: "${DATABASE_URL:?DATABASE_URL is required.}"
: "${BACKUP_ENCRYPTION_KEY:?BACKUP_ENCRYPTION_KEY is required.}"

backup=${1:-}
if [[ -z "$backup" ]]; then
  backup="$(find "${BACKUP_DIR:-$APP_ROOT/backups}" -maxdepth 1 -type f -name 'airproche-*.dump.enc' | sort | tail -1)"
fi
backup="$(realpath "$backup")"
case "$backup" in
  "$APP_ROOT"/backups/airproche-*.dump.enc) ;;
  *) printf 'Restore test accepts only an Airproche encrypted backup.\n' >&2; exit 1 ;;
esac
[[ -f "$backup" && -f "$backup.sha256" ]] || { printf 'Backup or checksum is missing.\n' >&2; exit 1; }
(cd "$(dirname "$backup")" && sha256sum -c "$(basename "$backup").sha256")

existing="$(runuser -u postgres -- psql -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname = '$RESTORE_DB'")"
if [[ -n "$existing" ]]; then
  printf 'Refusing to replace pre-existing database %s.\n' "$RESTORE_DB" >&2
  exit 1
fi

mapfile -t database < <(DATABASE_URL_TO_PARSE="$DATABASE_URL" python3 - <<'PY'
import os
from urllib.parse import unquote, urlsplit, urlunsplit

parsed = urlsplit(os.environ["DATABASE_URL_TO_PARSE"])
if parsed.hostname not in {"127.0.0.1", "localhost"} or unquote(parsed.path.lstrip("/")) != "airproche":
    raise SystemExit("Restore drill is restricted to the local airproche database.")
print(parsed.hostname)
print(parsed.port or 5432)
print(unquote(parsed.username or ""))
print(unquote(parsed.password or ""))
print(urlunsplit(parsed._replace(path="/airproche_restore_test")))
PY
)
if [[ "${database[2]}" != airproche ]] || [[ -z "${database[3]}" ]]; then
  printf 'Dedicated Airproche database credentials are required.\n' >&2
  exit 1
fi

plain="$(mktemp /tmp/airproche-restore.XXXXXX.dump)"
restore_created=false
cleanup() {
  status=$?
  trap - EXIT INT TERM
  rm -f "$plain"
  if [[ "$restore_created" == true ]]; then
    runuser -u postgres -- dropdb --if-exists "$RESTORE_DB" >/dev/null
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM
chmod 0600 "$plain"
BACKUP_ENCRYPTION_KEY="$BACKUP_ENCRYPTION_KEY" openssl enc -d -aes-256-cbc -pbkdf2 \
  -in "$backup" -out "$plain" -pass env:BACKUP_ENCRYPTION_KEY
runuser -u postgres -- createdb --owner=airproche --encoding=UTF8 --template=template0 "$RESTORE_DB"
restore_created=true
PGPASSWORD="${database[3]}" pg_restore --exit-on-error --no-owner --no-privileges \
  --host="${database[0]}" --port="${database[1]}" --username=airproche \
  --dbname="$RESTORE_DB" "$plain"

counts='from django.apps import apps; print("|".join(f"{m._meta.label_lower}={m.objects.count()}" for m in sorted(apps.get_models(), key=lambda item: item._meta.label_lower) if m._meta.managed))'
source_counts="$(runuser -u mignon --preserve-environment -- env HOME=/home/mignon "$APP_ROOT/current/backend/.venv/bin/python" "$APP_ROOT/current/backend/manage.py" shell -c "$counts")"
restore_counts="$(runuser -u mignon --preserve-environment -- env HOME=/home/mignon DATABASE_URL="${database[4]}" "$APP_ROOT/current/backend/.venv/bin/python" "$APP_ROOT/current/backend/manage.py" shell -c "$counts")"
if [[ "$source_counts" != "$restore_counts" ]]; then
  printf 'Restored model counts do not match production.\n' >&2
  exit 1
fi
runuser -u mignon --preserve-environment -- env HOME=/home/mignon DATABASE_URL="${database[4]}" \
  "$APP_ROOT/current/backend/.venv/bin/python" "$APP_ROOT/current/backend/manage.py" check
runuser -u mignon --preserve-environment -- env HOME=/home/mignon DATABASE_URL="${database[4]}" \
  "$APP_ROOT/current/backend/.venv/bin/python" "$APP_ROOT/current/backend/manage.py" migrate --check
printf 'Encrypted Airproche backup restore and model-count drill passed; test database will now be dropped.\n'
