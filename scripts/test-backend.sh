#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../backend"
DJANGO_USE_SQLITE_FOR_TESTS=true .venv/bin/python manage.py check
DJANGO_USE_SQLITE_FOR_TESTS=true .venv/bin/python manage.py makemigrations --check --dry-run
DJANGO_USE_SQLITE_FOR_TESTS=true .venv/bin/pytest -q
