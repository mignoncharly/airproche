#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

bash -n \
  scripts/bootstrap-production.sh \
  scripts/configure-production-secrets.sh \
  scripts/deploy-production.sh \
  scripts/enable-production-tls.sh \
  scripts/airproche-cert-deploy-hook.sh \
  scripts/backup-production.sh \
  scripts/test-production-restore.sh \
  scripts/check-vps-neighbors.sh \
  scripts/smoke-production.sh

grep -q '^gunicorn==26.0.0$' backend/requirements/prod-lock.txt
grep -q '^packaging==26.2$' backend/requirements/prod-lock.txt
grep -q 'Refusing to reuse pre-existing PostgreSQL role or database named airproche' scripts/bootstrap-production.sh
if grep -q 'ALTER ROLE airproche' scripts/bootstrap-production.sh; then
  printf 'Bootstrap must never take over an existing PostgreSQL role.\n' >&2
  exit 1
fi
grep -q 'STRIPE_ENVIRONMENT=test' scripts/bootstrap-production.sh
grep -q 'STRIPE_LIVE_MODE_CONFIRMED=false' scripts/bootstrap-production.sh
grep -q 'NGINX_GROUP=www-data' scripts/bootstrap-production.sh
grep -q 'NGINX_GROUP=www-data' scripts/deploy-production.sh
grep -q 'install -d -m 0710 -o "$APP_USER" -g "$NGINX_GROUP" "$SHARED"' scripts/deploy-production.sh
grep -q 'install -d -m 0750 -o "$APP_USER" -g "$NGINX_GROUP" "$SHARED/static"' scripts/deploy-production.sh
grep -q 'certbot certonly' scripts/enable-production-tls.sh
grep -q -- '--config-dir /etc/letsencrypt-airproche' scripts/enable-production-tls.sh
if grep -REq '/etc/letsencrypt/live/' deploy scripts/enable-production-tls.sh scripts/airproche-cert-deploy-hook.sh; then
  printf 'Airproche must not use shared Certbot state.\n' >&2
  exit 1
fi
if grep -E 'systemctl (restart|stop) ' scripts/*.sh | grep -Ev 'airproche-|nginx'; then
  printf 'Deployment scripts may control only Airproche units and validated Nginx reloads.\n' >&2
  exit 1
fi
if grep -Eiq 'paypal|redis-(server|cli)|redis://|6379' deploy/systemd/* deploy/nginx/*; then
  printf 'PayPal and Redis must not appear in Airproche runtime templates.\n' >&2
  exit 1
fi

work="$(mktemp -d /tmp/airproche-nginx-check.XXXXXX)"
cleanup() { rm -rf "$work"; }
trap cleanup EXIT INT TERM
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj '/CN=airproche.docufisc.de' \
  -keyout "$work/key.pem" -out "$work/cert.pem" >/dev/null 2>&1
sed \
  -e "s#/etc/letsencrypt-airproche/live/airproche.docufisc.de/fullchain.pem#$work/cert.pem#g" \
  -e "s#/etc/letsencrypt-airproche/live/airproche.docufisc.de/privkey.pem#$work/key.pem#g" \
  deploy/nginx/airproche-https.conf >"$work/site-https.conf"
for site in deploy/nginx/airproche-http.conf "$work/site-https.conf"; do
  sed -e "s/listen 80;/listen 18080;/g" \
      -e "s/listen \[::\]:80;/listen [::]:18080;/g" \
      -e "s/listen 443 ssl;/listen 18443 ssl;/g" \
      -e "s/listen \[::\]:443 ssl;/listen [::]:18443 ssl;/g" \
      "$site" >"$work/site-check.conf"
  cat >"$work/nginx.conf" <<EOF_NGINX
pid $work/nginx.pid;
error_log stderr;
events {}
http {
  access_log off;
  include $work/site-check.conf;
}
EOF_NGINX
  nginx -t -p "$work" -c "$work/nginx.conf" >/dev/null
done

APP_ENV=production \
APP_BASE_URL=https://airproche.docufisc.de \
DJANGO_SECRET_KEY=fictional-deploy-check-secret-abcdefghijklmnopqrstuvwxyz-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ \
DJANGO_DEBUG=false \
DJANGO_ALLOWED_HOSTS=airproche.docufisc.de,www.airproche.docufisc.de \
DJANGO_CSRF_TRUSTED_ORIGINS=https://airproche.docufisc.de,https://www.airproche.docufisc.de \
DJANGO_REQUIRE_API_ORIGIN=true \
STAFF_NETWORK_GATE_ENABLED=true \
STAFF_ALLOWED_NETWORKS=192.0.2.1/32 \
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend \
DEFAULT_FROM_EMAIL=no-reply@airproche.example.test \
EMAIL_HOST=smtp.zoho.eu \
EMAIL_HOST_USER=fictional@airproche.example.test \
EMAIL_HOST_PASSWORD=fictional-app-password \
STRIPE_SECRET_KEY=sk_test_fictional \
STRIPE_WEBHOOK_SECRET=whsec_fictional \
STRIPE_ENVIRONMENT=test \
STRIPE_LIVE_MODE_CONFIRMED=false \
DJANGO_USE_SQLITE_FOR_TESTS=true \
backend/.venv/bin/python backend/manage.py check --deploy >/dev/null

printf 'Deployment configuration checks passed.\n'
