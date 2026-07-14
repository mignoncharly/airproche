#!/usr/bin/env bash
set -euo pipefail
certificate=/etc/letsencrypt-airproche/live/airproche.docufisc.de/fullchain.pem
private_key=/etc/letsencrypt-airproche/live/airproche.docufisc.de/privkey.pem
[[ -f "$certificate" && -f "$private_key" ]] || { printf 'Airproche certificate files are missing.\n' >&2; exit 1; }
nginx -t
systemctl reload nginx
