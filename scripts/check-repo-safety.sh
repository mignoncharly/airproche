#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

bad_names="$(git ls-files | grep -Eiv '^\.env\.example$' | grep -Ei '(^|/)(\.env($|\.)|id_rsa|[^/]+\.(pem|key|p12|pfx|dump|sql)$|backups?/|uploads?/|media/)' || true)"
if [[ -n "$bad_names" ]]; then
  printf 'Forbidden tracked secret or personal-data paths:\n%s\n' "$bad_names" >&2
  exit 1
fi

secret_matches="$(git grep -nEI '(sk_(live|test)_[A-Za-z0-9]{16,}|whsec_[A-Za-z0-9]{16,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|postgres(ql)?://[^[:space:]]+:[^@[:space:]]+@|EMAIL_HOST_PASSWORD=[^[:space:]]+|DJANGO_SECRET_KEY=[^$<{[:space:]][^[:space:]]{15,})' -- . ':(exclude)scripts/check-repo-safety.sh' ':(exclude)backend/tests/**' ':(exclude).env.example' | grep -Ev '[$]database_password@|=(fictional[-_A-Za-z0-9]*)' || true)"
if [[ -n "$secret_matches" ]]; then
  printf 'Potential tracked credentials:\n%s\n' "$secret_matches" >&2
  exit 1
fi

paypal_config="$(git grep -nE 'PAYPAL_(CLIENT|SECRET|ENVIRONMENT)' -- . ':(exclude)scripts/check-repo-safety.sh' || true)"
if [[ -n "$paypal_config" ]]; then
  printf 'PayPal configuration is forbidden because the integration is intentionally skipped:\n%s\n' "$paypal_config" >&2
  exit 1
fi

for candidate in .env.production private.pem backup.sql backups/db.dump media/passport.jpg uploads/customer-id.png; do
  if ! git check-ignore -q "$candidate"; then
    printf 'Expected sensitive path is not ignored: %s\n' "$candidate" >&2
    exit 1
  fi
done

printf 'Repository safety scan passed.\n'
