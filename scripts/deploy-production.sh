#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  printf 'Run this script with sudo.\n' >&2
  exit 1
fi

APP_USER=mignon
APP_GROUP=mignon
NGINX_GROUP=www-data
APP_ROOT=/home/mignon/airproche
SHARED="$APP_ROOT/shared"
ENV_FILE="$SHARED/.env.production"
WEB_ENV_FILE="$SHARED/.env.web"
SOURCE_REF=${1:-origin/main}

for command in git python3 npm node curl systemctl runuser tar ln mv nice getent install; do
  command -v "$command" >/dev/null || { printf 'Missing required command: %s\n' "$command" >&2; exit 1; }
done
if ! getent group "$NGINX_GROUP" >/dev/null 2>&1; then
  printf 'Required Nginx group %s does not exist.\n' "$NGINX_GROUP" >&2
  exit 1
fi
for file in "$ENV_FILE" "$WEB_ENV_FILE" /etc/systemd/system/airproche-api.service /etc/systemd/system/airproche-web.service; do
  [[ -f "$file" ]] || { printf 'Missing bootstrap artifact: %s\n' "$file" >&2; exit 1; }
done
if [[ -n "$(git -C "$APP_ROOT" status --porcelain)" ]]; then
  printf 'Refusing deployment from a dirty Airproche source checkout.\n' >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
if [[ "${AIRPROCHE_SECRETS_CONFIGURED:-}" != true ]]; then
  printf 'Run configure-production-secrets.sh before deployment.\n' >&2
  exit 1
fi
if [[ "${APP_ENV:-}" != production ]] || [[ "${APP_BASE_URL:-}" != https://airproche.docufisc.de ]] || [[ "${DJANGO_DEBUG:-}" != false ]]; then
  printf 'Production environment identity is invalid.\n' >&2
  exit 1
fi
if [[ "${STRIPE_ENVIRONMENT:-}" != test ]] || [[ "${STRIPE_LIVE_MODE_CONFIRMED:-}" != false ]] || [[ "${STRIPE_SECRET_KEY:-}" != sk_test_* ]] || [[ "${STRIPE_WEBHOOK_SECRET:-}" != whsec_* ]]; then
  printf 'Deployment requires explicit Stripe test mode credentials.\n' >&2
  exit 1
fi
if [[ "${EMAIL_HOST:-}" != smtp.zoho.eu ]] || [[ -z "${EMAIL_HOST_USER:-}" ]] || [[ -z "${EMAIL_HOST_PASSWORD:-}" ]] || [[ -z "${DEFAULT_FROM_EMAIL:-}" ]]; then
  printf 'Zoho SMTP production configuration is incomplete.\n' >&2
  exit 1
fi
if [[ "${STAFF_NETWORK_GATE_ENABLED:-}" != true ]] || [[ -z "${STAFF_ALLOWED_NETWORKS:-}" ]]; then
  printf 'The production staff network gate must be configured.\n' >&2
  exit 1
fi

# Nginx needs group-scoped traversal to serve collected Django admin assets.
# Provider secrets remain protected by their independent mode-0600 files.
install -d -m 0710 -o "$APP_USER" -g "$NGINX_GROUP" "$SHARED"
install -d -m 0750 -o "$APP_USER" -g "$NGINX_GROUP" "$SHARED/static"

available_kib="$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)"
if (( available_kib < 700000 )); then
  printf 'Refusing memory-intensive deployment: less than 700 MiB is currently available.\n' >&2
  exit 1
fi

swap_total_kib="$(awk '/SwapTotal:/ {print $2}' /proc/meminfo)"
swap_free_kib="$(awk '/SwapFree:/ {print $2}' /proc/meminfo)"
if (( swap_total_kib > 0 && swap_free_kib < 262144 )); then
  printf 'Refusing memory-intensive deployment: less than 256 MiB of swap is free.\n' >&2
  exit 1
fi
if ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 12))'; then
  printf 'Python 3.12 or newer is required.\n' >&2
  exit 1
fi
node_major="$(node --version | sed 's/^v//; s/\..*$//')"
if [[ ! "$node_major" =~ ^[0-9]+$ ]] || (( node_major < 22 )); then
  printf 'Node.js 22 or newer is required.\n' >&2
  exit 1
fi

runuser -u "$APP_USER" -- git -C "$APP_ROOT" fetch --prune origin
sha="$(git -C "$APP_ROOT" rev-parse --verify "${SOURCE_REF}^{commit}")"
if [[ ! "$sha" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'Selected ref did not resolve to a commit.\n' >&2
  exit 1
fi
release="$APP_ROOT/releases/$sha"
if [[ -e "$release" ]]; then
  printf 'Release %s already exists; refusing to mutate it.\n' "$sha" >&2
  exit 1
fi

install -d -m 0750 -o "$APP_USER" -g "$APP_GROUP" "$release"
runuser -u "$APP_USER" -- bash -c 'git -C "$1" archive "$2" | tar -x -C "$3"' _ "$APP_ROOT" "$sha" "$release"

neighbor_snapshot="$(mktemp /tmp/airproche-neighbors.XXXXXX)"
"$release/scripts/check-vps-neighbors.sh" snapshot "$neighbor_snapshot"
previous=""
if [[ -L "$APP_ROOT/current" ]]; then
  previous="$(readlink -f "$APP_ROOT/current")"
fi
rollback_application() {
  local status=$?
  trap - ERR
  printf 'Airproche deployment failed after release preparation.\n' >&2
  if [[ -n "$previous" && -d "$previous" ]]; then
    ln -sfn "$previous" "$APP_ROOT/.current-rollback"
    mv -Tf "$APP_ROOT/.current-rollback" "$APP_ROOT/current"
    systemctl restart airproche-api.service airproche-web.service || true
    printf 'Application symlink restored to %s. Database migrations were not rolled back.\n' "$previous" >&2
  else
    systemctl stop airproche-api.service airproche-web.service || true
  fi
  "$release/scripts/check-vps-neighbors.sh" verify "$neighbor_snapshot" || true
  rm -f "$neighbor_snapshot"
  exit "$status"
}
trap rollback_application ERR

runuser -u "$APP_USER" -- python3 -m venv "$release/backend/.venv"
runuser -u "$APP_USER" -- "$release/backend/.venv/bin/pip" install --disable-pip-version-check --no-deps -r "$release/backend/requirements/prod-lock.txt"
runuser -u "$APP_USER" -- env -i HOME=/home/mignon PATH=/usr/local/bin:/usr/bin:/bin NEXT_TELEMETRY_DISABLED=1 nice -n 10 npm --prefix "$release/frontend" ci --no-audit --no-fund

run_backend() {
  runuser -u "$APP_USER" --preserve-environment -- env HOME=/home/mignon \
    "$release/backend/.venv/bin/python" "$release/backend/manage.py" "$@"
}
run_backend check --deploy
run_backend migrate --plan
runuser -u "$APP_USER" --preserve-environment -- env HOME=/home/mignon "$release/scripts/backup-production.sh"
run_backend migrate --noinput
run_backend createcachetable
run_backend collectstatic --noinput

web_app_base="$(sed -n 's/^APP_BASE_URL=//p' "$WEB_ENV_FILE")"
web_backend="$(sed -n 's/^BACKEND_INTERNAL_URL=//p' "$WEB_ENV_FILE")"
runuser -u "$APP_USER" -- env -i HOME=/home/mignon PATH=/usr/local/bin:/usr/bin:/bin \
  APP_BASE_URL="$web_app_base" BACKEND_INTERNAL_URL="$web_backend" \
  NODE_OPTIONS=--max-old-space-size=768 NEXT_TELEMETRY_DISABLED=1 \
  nice -n 10 npm --prefix "$release/frontend" run build
install -d -m 0750 -o "$APP_USER" -g "$APP_GROUP" "$SHARED/next-cache"
if [[ -d "$release/frontend/.next/cache" ]]; then
  rm -rf "$release/frontend/.next/cache"
fi
ln -s "$SHARED/next-cache" "$release/frontend/.next/cache"
runuser -u "$APP_USER" -- env -i HOME=/home/mignon PATH=/usr/local/bin:/usr/bin:/bin \
  npm --prefix "$release/frontend" prune --omit=dev --no-audit --no-fund

ln -sfn "$release" "$APP_ROOT/.current-$sha"
mv -Tf "$APP_ROOT/.current-$sha" "$APP_ROOT/current"
systemctl enable airproche-api.service airproche-web.service airproche-backup.timer
systemctl restart airproche-api.service
systemctl restart airproche-web.service
systemctl start airproche-backup.timer

api_ready=false
web_ready=false
for _ in $(seq 1 30); do
  if curl -fsS -H 'Host: airproche.docufisc.de' -H 'X-Forwarded-Proto: https' http://127.0.0.1:8050/api/v1/health/ready/ >/dev/null; then
    api_ready=true
  fi
  if curl -fsS -H 'Host: airproche.docufisc.de' http://127.0.0.1:3050/ >/dev/null; then
    web_ready=true
  fi
  if [[ "$api_ready" == true && "$web_ready" == true ]]; then
    break
  fi
  sleep 2
done
if [[ "$api_ready" != true || "$web_ready" != true ]]; then
  printf 'Local Airproche health checks did not become ready.\n' >&2
  false
fi

"$release/scripts/check-vps-neighbors.sh" verify "$neighbor_snapshot"
rm -f "$neighbor_snapshot"
trap - ERR
printf 'Airproche release %s is active on loopback ports 8050 and 3050.\n' "$sha"
printf 'Database migrations were applied and a pre-migration backup was created.\n'
printf 'Next: sudo %s/scripts/enable-production-tls.sh YOUR_CERTBOT_EMAIL\n' "$APP_ROOT"
