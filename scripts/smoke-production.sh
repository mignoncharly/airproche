#!/usr/bin/env bash
set -euo pipefail
BASE_URL=${1:-https://airproche.docufisc.de}
if [[ "$BASE_URL" != https://airproche.docufisc.de ]]; then
  printf 'Production smoke is restricted to https://airproche.docufisc.de.\n' >&2
  exit 1
fi

expect_status() {
  local expected=$1
  local url=$2
  shift 2
  local actual
  actual="$(curl -sS -o /dev/null -w '%{http_code}' "$@" "$url")"
  if [[ "$actual" != "$expected" ]]; then
    printf 'Expected HTTP %s from %s; received %s.\n' "$expected" "$url" "$actual" >&2
    exit 1
  fi
}

for path in / /contact /robots.txt /sitemap.xml /manifest.webmanifest /offline /api/v1/health/live/ /api/v1/health/ready/ /api/v1/public/content/; do
  expect_status 200 "$BASE_URL$path"
done
expect_status 403 "$BASE_URL/api/v1/staff/operations/summary/"
expect_status 400 "$BASE_URL/api/v1/payments/webhooks/stripe/" \
  -X POST -H 'Content-Type: application/json' -H 'Stripe-Signature: t=1,v1=fictional' --data '{}'

headers="$(curl -fsSI "$BASE_URL/")"
for header in 'strict-transport-security:' 'content-security-policy:' 'x-content-type-options:' 'referrer-policy:'; do
  if ! grep -qi "^$header" <<<"$headers"; then
    printf 'Missing production response header: %s\n' "$header" >&2
    exit 1
  fi
done
redirect="$(curl -fsSI https://www.airproche.docufisc.de/ | awk 'BEGIN {IGNORECASE=1} /^location:/ {print $2}' | tr -d '\r')"
if [[ "$redirect" != "$BASE_URL/" ]]; then
  printf 'Unexpected www redirect: %s\n' "$redirect" >&2
  exit 1
fi
printf 'Non-destructive Airproche production smoke passed.\n'
