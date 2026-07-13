#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

scripts/check-repo-safety.sh
scripts/audit-dependencies.sh
scripts/test-backend.sh
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run test:e2e

git diff --check
if [[ -n "$(git status --porcelain)" ]]; then
  printf 'Release gate completed, but the working tree is not clean. Commit reviewed changes first.\n' >&2
  exit 1
fi
printf 'Release qualification passed.\n'
