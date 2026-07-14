#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  printf 'Run this script with sudo.\n' >&2
  exit 1
fi

ENV_FILE=/home/mignon/airproche/shared/.env.production
if [[ ! -f "$ENV_FILE" ]]; then
  printf 'Run bootstrap-production.sh first.\n' >&2
  exit 1
fi

read_value() {
  local prompt=$1
  local secret=${2:-false}
  local value
  if [[ "$secret" == true ]]; then
    IFS= read -r -s -p "$prompt" value </dev/tty
    printf '\n' >/dev/tty
  else
    IFS= read -r -p "$prompt" value </dev/tty
  fi
  printf '%s' "$value"
}

sender="$(read_value 'Zoho sender address (for example no-reply@airproche.docufisc.de): ')"
zoho_user="$(read_value 'Zoho SMTP login address: ')"
zoho_password="$(read_value 'Zoho SMTP app password (hidden): ' true)"
stripe_secret="$(read_value 'Stripe TEST secret key sk_test_... (hidden): ' true)"
stripe_webhook="$(read_value 'Stripe TEST webhook secret whsec_... (hidden): ' true)"
ssh_connection="${SSH_CONNECTION:-}"
detected_ip="${ssh_connection%% *}"
staff_networks="$(read_value "Staff access CIDR list${detected_ip:+ [$detected_ip/32]}: ")"
if [[ -z "$staff_networks" && -n "$detected_ip" ]]; then
  staff_networks="$detected_ip/32"
fi

email_pattern='^[A-Za-z0-9.!#$%&*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
if [[ ! "$sender" =~ $email_pattern ]] || [[ ! "$zoho_user" =~ $email_pattern ]]; then
  printf 'Sender and Zoho login must be valid email addresses.\n' >&2
  exit 1
fi
if [[ -z "$zoho_password" ]]; then
  printf 'A Zoho SMTP app password is required.\n' >&2
  exit 1
fi
if [[ "$stripe_secret" != sk_test_* ]]; then
  printf 'Only a Stripe test secret beginning with sk_test_ is accepted.\n' >&2
  exit 1
fi
if [[ "$stripe_webhook" != whsec_* ]]; then
  printf 'A Stripe test webhook secret beginning with whsec_ is required.\n' >&2
  exit 1
fi
STAFF_NETWORKS_TO_VALIDATE="$staff_networks" python3 - <<'PY'
import ipaddress
import os

values = [item.strip() for item in os.environ["STAFF_NETWORKS_TO_VALIDATE"].split(",") if item.strip()]
if not values:
    raise SystemExit("At least one staff network is required.")
for value in values:
    ipaddress.ip_network(value, strict=False)
PY

set_env() {
  local key=$1
  local value=$2
  local escaped tmp found=false
  escaped=${value//\\/\\\\}
  escaped=${escaped//\"/\\\"}
  tmp="$(mktemp /home/mignon/airproche/shared/.env.production.XXXXXX)"
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" == "$key="* ]]; then
      printf '%s="%s"\n' "$key" "$escaped" >>"$tmp"
      found=true
    else
      printf '%s\n' "$line" >>"$tmp"
    fi
  done <"$ENV_FILE"
  if [[ "$found" != true ]]; then
    printf '%s="%s"\n' "$key" "$escaped" >>"$tmp"
  fi
  chown mignon:mignon "$tmp"
  chmod 0600 "$tmp"
  mv -f "$tmp" "$ENV_FILE"
}

set_env DEFAULT_FROM_EMAIL "$sender"
set_env EMAIL_HOST_USER "$zoho_user"
set_env EMAIL_HOST_PASSWORD "$zoho_password"
set_env STRIPE_SECRET_KEY "$stripe_secret"
set_env STRIPE_WEBHOOK_SECRET "$stripe_webhook"
set_env STAFF_ALLOWED_NETWORKS "$staff_networks"
set_env AIRPROCHE_SECRETS_CONFIGURED true

unset zoho_password stripe_secret stripe_webhook
printf 'Zoho, Stripe test mode, and staff network settings were stored without printing secrets.\n'
printf 'Next: sudo /home/mignon/airproche/scripts/deploy-production.sh\n'
