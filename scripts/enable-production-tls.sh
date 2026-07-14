#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  printf 'Run this script with sudo.\n' >&2
  exit 1
fi
if [[ $# -ne 1 ]] || [[ ! "$1" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
  printf 'Usage: sudo %s CERTBOT_CONTACT_EMAIL\n' "$0" >&2
  exit 1
fi

CONTACT_EMAIL=$1
APP_ROOT=/home/mignon/airproche
EXPECTED_IP=82.165.94.233
HTTP_CONFIG="$APP_ROOT/deploy/nginx/airproche-http.conf"
HTTPS_CONFIG="$APP_ROOT/deploy/nginx/airproche-https.conf"
ACTIVE_CONFIG=/etc/nginx/sites-available/airproche

for command in certbot nginx systemctl getent curl install; do
  command -v "$command" >/dev/null || { printf 'Missing required command: %s\n' "$command" >&2; exit 1; }
done
for domain in airproche.docufisc.de www.airproche.docufisc.de; do
  mapfile -t addresses < <(getent ahostsv4 "$domain" | awk '{print $1}' | sort -u)
  if [[ ${#addresses[@]} -eq 0 ]]; then
    printf 'DNS does not resolve for %s.\n' "$domain" >&2
    exit 1
  fi
  for address in "${addresses[@]}"; do
    if [[ "$address" != "$EXPECTED_IP" ]]; then
      printf '%s resolves to %s instead of this VPS (%s).\n' "$domain" "$address" "$EXPECTED_IP" >&2
      exit 1
    fi
  done
done

curl -fsS http://airproche.docufisc.de/.well-known/acme-challenge/nonexistent-probe -o /dev/null || status=$?
if [[ ${status:-0} -ne 22 ]]; then
  printf 'Unexpected HTTP reachability result for the ACME vhost.\n' >&2
  exit 1
fi

certbot certonly \
  --webroot --webroot-path /var/www/airproche-certbot \
  --config-dir /etc/letsencrypt-airproche \
  --work-dir /var/lib/letsencrypt-airproche \
  --logs-dir /var/log/letsencrypt-airproche \
  --cert-name airproche.docufisc.de \
  --domains airproche.docufisc.de,www.airproche.docufisc.de \
  --non-interactive --agree-tos --email "$CONTACT_EMAIL" --expand

[[ -f /etc/letsencrypt-airproche/live/airproche.docufisc.de/fullchain.pem ]] || { printf 'Airproche certificate was not created.\n' >&2; exit 1; }
[[ -f /etc/letsencrypt-airproche/live/airproche.docufisc.de/privkey.pem ]] || { printf 'Airproche private key was not created.\n' >&2; exit 1; }

backup="$(mktemp /tmp/airproche-nginx.XXXXXX)"
cp "$ACTIVE_CONFIG" "$backup"
restore_http() {
  status=$?
  trap - ERR
  install -m 0644 "$backup" "$ACTIVE_CONFIG"
  nginx -t && systemctl reload nginx || true
  rm -f "$backup"
  exit "$status"
}
trap restore_http ERR
install -m 0644 "$HTTPS_CONFIG" "$ACTIVE_CONFIG"
nginx -t
systemctl reload nginx
systemctl enable --now airproche-cert-renew.timer
rm -f "$backup"
trap - ERR

curl -fsS https://airproche.docufisc.de/api/v1/health/live/ >/dev/null
redirect="$(curl -fsSI https://www.airproche.docufisc.de/ | awk 'BEGIN {IGNORECASE=1} /^location:/ {print $2}' | tr -d '\r')"
if [[ "$redirect" != https://airproche.docufisc.de/ ]]; then
  printf 'The www redirect is not canonical: %s\n' "$redirect" >&2
  exit 1
fi
printf 'Dedicated Airproche TLS certificate and canonical www redirect are active.\n'
