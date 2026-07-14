#!/usr/bin/env bash
set -euo pipefail

mode=${1:-}
snapshot=${2:-}
if [[ "$mode" != snapshot && "$mode" != verify ]] || [[ -z "$snapshot" ]]; then
  printf 'Usage: %s snapshot|verify SNAPSHOT_FILE\n' "$0" >&2
  exit 1
fi

patterns='^(bauki-|docufisc\.service$|gunicorn\.service$|microsecours-|nckl-|perceptix-|saha-|vlogvoiceai-|nginx\.service$|postgresql@16-main\.service$|redis-server\.service$|redis-bauki\.service$)'
if [[ "$mode" == snapshot ]]; then
  systemctl list-units --type=service --state=running --no-legend --no-pager \
    | awk '{print $1}' | grep -E "$patterns" | sort -u >"$snapshot"
  if [[ ! -s "$snapshot" ]]; then
    printf 'No neighboring application baseline could be captured.\n' >&2
    exit 1
  fi
  nginx -t
  printf 'Captured %s running neighboring services.\n' "$(wc -l <"$snapshot")"
  exit 0
fi

failed=false
while IFS= read -r unit; do
  if ! systemctl is-active --quiet "$unit"; then
    printf 'Previously running service is no longer active: %s\n' "$unit" >&2
    failed=true
  fi
done <"$snapshot"
nginx -t || failed=true
if [[ "$failed" == true ]]; then
  exit 1
fi
printf 'All previously running neighboring services remain active.\n'
