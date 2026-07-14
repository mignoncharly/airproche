#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  printf 'Run this script with sudo from the Airproche repository.\n' >&2
  exit 1
fi

APP_USER=mignon
APP_GROUP=mignon
APP_ROOT=/home/mignon/airproche
SHARED="$APP_ROOT/shared"
ENV_FILE="$SHARED/.env.production"
WEB_ENV_FILE="$SHARED/.env.web"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "$REPO_DIR" != "$APP_ROOT" ]]; then
  printf 'Expected the repository at %s; found %s.\n' "$APP_ROOT" "$REPO_DIR" >&2
  exit 1
fi
if [[ ! -d "$APP_ROOT/.git" ]] || [[ "$(git -C "$APP_ROOT" remote get-url origin)" != "https://github.com/mignoncharly/airproche.git" ]]; then
  printf 'The Airproche GitHub checkout was not found at %s.\n' "$APP_ROOT" >&2
  exit 1
fi
for command in openssl psql createdb nginx systemctl ss install runuser git; do
  command -v "$command" >/dev/null || { printf 'Missing required command: %s\n' "$command" >&2; exit 1; }
done
if ! id "$APP_USER" >/dev/null 2>&1; then
  printf 'Required application user %s does not exist.\n' "$APP_USER" >&2
  exit 1
fi
for port in 3050 8050; do
  if ss -ltnH | awk '{print $4}' | grep -Eq ":${port}$"; then
    printf 'Refusing bootstrap because loopback port %s is already occupied.\n' "$port" >&2
    exit 1
  fi
done

install -d -m 0750 -o "$APP_USER" -g "$APP_GROUP" \
  "$APP_ROOT/releases" "$SHARED" "$SHARED/static" "$SHARED/media" \
  "$SHARED/next-cache" "$APP_ROOT/backups"

if [[ -e "$ENV_FILE" ]]; then
  printf 'Refusing to overwrite existing %s.\n' "$ENV_FILE" >&2
  exit 1
fi

umask 0077
django_secret="$(openssl rand -hex 64)"
database_password="$(openssl rand -hex 32)"
backup_encryption_key="$(openssl rand -hex 32)"
role_exists="$(runuser -u postgres -- psql -d postgres -Atc "SELECT 1 FROM pg_roles WHERE rolname = 'airproche'")"
database_exists="$(runuser -u postgres -- psql -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname = 'airproche'")"
if [[ -n "$role_exists" || -n "$database_exists" ]]; then
  printf 'Refusing to reuse pre-existing PostgreSQL role or database named airproche.\n' >&2
  exit 1
fi
runuser -u postgres -- psql -d postgres >/dev/null <<SQL
CREATE ROLE airproche WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD '$database_password';
SQL
runuser -u postgres -- createdb --owner=airproche --encoding=UTF8 --template=template0 airproche
cat >"$ENV_FILE" <<EOF_ENV
APP_ENV=production
APP_BASE_URL=https://airproche.docufisc.de
DJANGO_SECRET_KEY=$django_secret
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=airproche.docufisc.de,www.airproche.docufisc.de
DJANGO_CSRF_TRUSTED_ORIGINS=https://airproche.docufisc.de,https://www.airproche.docufisc.de
DJANGO_REQUIRE_API_ORIGIN=true
DJANGO_HSTS_PRELOAD=false
DJANGO_LOG_LEVEL=INFO
DJANGO_STATIC_ROOT=$SHARED/static
DJANGO_MEDIA_ROOT=$SHARED/media
DATABASE_URL=postgresql://airproche:$database_password@127.0.0.1:5432/airproche
TRUSTED_PROXY_NETWORKS=127.0.0.1/32,::1/128
DRF_NUM_PROXIES=1
STAFF_NETWORK_GATE_ENABLED=true
STAFF_ALLOWED_NETWORKS=
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=
EMAIL_HOST=smtp.zoho.eu
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=true
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_ENVIRONMENT=test
STRIPE_LIVE_MODE_CONFIRMED=false
BACKUP_DIR=$APP_ROOT/backups
BACKUP_RETENTION_DAYS=14
BACKUP_ENCRYPTION_KEY=$backup_encryption_key
AIRPROCHE_SECRETS_CONFIGURED=false
EOF_ENV
chown "$APP_USER:$APP_GROUP" "$ENV_FILE"
chmod 0600 "$ENV_FILE"

cat >"$WEB_ENV_FILE" <<EOF_WEB
APP_BASE_URL=https://airproche.docufisc.de
BACKEND_INTERNAL_URL=http://127.0.0.1:8050
NEXT_TELEMETRY_DISABLED=1
EOF_WEB
chown "$APP_USER:$APP_GROUP" "$WEB_ENV_FILE"
chmod 0600 "$WEB_ENV_FILE"

install -m 0644 "$REPO_DIR/deploy/systemd/airproche-api.service" /etc/systemd/system/airproche-api.service
install -m 0644 "$REPO_DIR/deploy/systemd/airproche-web.service" /etc/systemd/system/airproche-web.service
install -m 0644 "$REPO_DIR/deploy/systemd/airproche-backup.service" /etc/systemd/system/airproche-backup.service
install -m 0644 "$REPO_DIR/deploy/systemd/airproche-backup.timer" /etc/systemd/system/airproche-backup.timer
install -m 0644 "$REPO_DIR/deploy/systemd/airproche-cert-renew.service" /etc/systemd/system/airproche-cert-renew.service
install -m 0644 "$REPO_DIR/deploy/systemd/airproche-cert-renew.timer" /etc/systemd/system/airproche-cert-renew.timer
systemctl daemon-reload

install -d -m 0755 -o root -g root /var/www/airproche-certbot/.well-known/acme-challenge
install -m 0644 "$REPO_DIR/deploy/nginx/airproche-http.conf" /etc/nginx/sites-available/airproche
ln -sfn /etc/nginx/sites-available/airproche /etc/nginx/sites-enabled/airproche
nginx -t
systemctl reload nginx

printf 'Airproche bootstrap completed without starting application services.\n'
printf 'Generated secrets are stored only in %s (mode 0600).\n' "$ENV_FILE"
printf 'No Redis resource was created because Airproche does not use Redis.\n'
printf 'Next: sudo %s/scripts/configure-production-secrets.sh\n' "$APP_ROOT"
