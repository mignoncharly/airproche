#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [[ ! -x backend/.venv/bin/pip-audit ]]; then
  printf 'pip-audit is required in backend/.venv for this check.\n' >&2
  exit 1
fi
backend/.venv/bin/pip-audit -r backend/requirements/prod-lock.txt
backend/.venv/bin/pip-audit -r backend/requirements/dev-lock.txt
npm --prefix frontend audit --audit-level=moderate
