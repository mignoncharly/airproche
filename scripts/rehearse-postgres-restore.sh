#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

: "${AIRPROCHE_REHEARSAL_SOURCE_URL:?Set AIRPROCHE_REHEARSAL_SOURCE_URL to the fictional qualification database URL.}"
: "${AIRPROCHE_REHEARSAL_ADMIN_URL:?Set AIRPROCHE_REHEARSAL_ADMIN_URL to a local PostgreSQL maintenance URL.}"
if [[ "${AIRPROCHE_REHEARSAL_DATA_CLASSIFICATION:-}" != "fictional" ]]; then
  printf 'Refusing restore rehearsal unless AIRPROCHE_REHEARSAL_DATA_CLASSIFICATION=fictional.\n' >&2
  exit 2
fi

for tool in pg_dump pg_restore psql createdb dropdb sha256sum; do
  command -v "$tool" >/dev/null || { printf 'Missing required tool: %s\n' "$tool" >&2; exit 2; }
done

mapfile -t parsed < <(backend/.venv/bin/python - <<'PY'
import os
import re
from urllib.parse import unquote, urlsplit, urlunsplit

source = urlsplit(os.environ["AIRPROCHE_REHEARSAL_SOURCE_URL"])
admin = urlsplit(os.environ["AIRPROCHE_REHEARSAL_ADMIN_URL"])
if source.scheme not in {"postgres", "postgresql"} or admin.scheme not in {"postgres", "postgresql"}:
    raise SystemExit("Rehearsal URLs must use PostgreSQL.")
if source.hostname not in {"127.0.0.1", "localhost"} or admin.hostname not in {"127.0.0.1", "localhost"}:
    raise SystemExit("Restore rehearsal is restricted to local PostgreSQL hosts.")
source_db = unquote(source.path.lstrip("/"))
admin_db = unquote(admin.path.lstrip("/"))
owner = unquote(source.username or "")
if not re.fullmatch(r"airproche_[a-z0-9_]*qualification", source_db):
    raise SystemExit("Source database must match airproche_*qualification.")
if admin_db not in {"postgres", "template1"}:
    raise SystemExit("The maintenance URL must target postgres or template1.")
if not re.fullmatch(r"[a-z_][a-z0-9_]*", owner):
    raise SystemExit("The qualification database owner is invalid.")
restore_db = f"{source_db}_restore_test"
if len(restore_db) > 63:
    raise SystemExit("Derived restore database name exceeds PostgreSQL's identifier limit.")
restore = source._replace(path=f"/{restore_db}")
print(source_db)
print(owner)
print(restore_db)
print(urlunsplit(restore))
PY
)
source_db="${parsed[0]}"
owner="${parsed[1]}"
restore_db="${parsed[2]}"
restore_url="${parsed[3]}"
dump_file="$(mktemp /tmp/airproche-qualification.XXXXXX.dump)"
restore_created=false

cleanup() {
  status=$?
  trap - EXIT INT TERM
  if [[ "$restore_created" == true ]]; then
    dropdb --if-exists --maintenance-db="$AIRPROCHE_REHEARSAL_ADMIN_URL" "$restore_db" >/dev/null
  fi
  rm -f "$dump_file"
  exit "$status"
}
trap cleanup EXIT INT TERM

existing="$(psql "$AIRPROCHE_REHEARSAL_ADMIN_URL" -Atc "SELECT 1 FROM pg_database WHERE datname = '$restore_db'")"
if [[ -n "$existing" ]]; then
  printf 'Refusing to replace pre-existing database %s.\n' "$restore_db" >&2
  exit 2
fi

manage_counts='from django.apps import apps; print("|".join(f"{m._meta.label_lower}={m.objects.count()}" for m in sorted(apps.get_models(), key=lambda item: item._meta.label_lower) if m._meta.managed))'
source_counts="$(DATABASE_URL="$AIRPROCHE_REHEARSAL_SOURCE_URL" APP_ENV=development DJANGO_DEBUG=false DJANGO_USE_SQLITE_FOR_TESTS=false backend/.venv/bin/python backend/manage.py shell -c "$manage_counts")"

pg_dump --dbname="$AIRPROCHE_REHEARSAL_SOURCE_URL" --format=custom --no-owner --no-privileges --file="$dump_file"
createdb --maintenance-db="$AIRPROCHE_REHEARSAL_ADMIN_URL" --owner="$owner" "$restore_db"
restore_created=true
pg_restore --exit-on-error --no-owner --no-privileges --dbname="$restore_url" "$dump_file"

DATABASE_URL="$restore_url" APP_ENV=development DJANGO_DEBUG=false DJANGO_USE_SQLITE_FOR_TESTS=false backend/.venv/bin/python backend/manage.py check
DATABASE_URL="$restore_url" APP_ENV=development DJANGO_DEBUG=false DJANGO_USE_SQLITE_FOR_TESTS=false backend/.venv/bin/python backend/manage.py migrate --check
restore_counts="$(DATABASE_URL="$restore_url" APP_ENV=development DJANGO_DEBUG=false DJANGO_USE_SQLITE_FOR_TESTS=false backend/.venv/bin/python backend/manage.py shell -c "$manage_counts")"
if [[ "$source_counts" != "$restore_counts" ]]; then
  printf 'Restored Django model row counts do not match the source database.\n' >&2
  exit 1
fi

checksum="$(sha256sum "$dump_file" | awk '{print $1}')"
printf 'PostgreSQL restore rehearsal passed: %s -> %s; SHA-256 %s\n' "$source_db" "$restore_db" "$checksum"
