# Release qualification

Phase 14 uses fictional records, Stripe test fixtures, isolated Django test
databases, and browser emulation. Live payment credentials and production
personal data are forbidden.

## Automated matrix

| Journey or risk | Evidence |
| --- | --- |
| Guest/authenticated booking and idempotency | `test_bookings.py`, `test_authentication.py` |
| Cross-account dashboard, cancellation, receipts | `test_dashboard.py`, `test_security.py` |
| Stripe checkout, signed retries/out-of-order events, mismatch, refund | `test_payments.py` |
| Operations confirmation, permissions, assignment conflicts/capacity | `test_operations.py`, `test_security.py` |
| Email failure, retry, commit timing | `test_notifications.py`, `test_bookings.py` |
| Contact abuse, injection, CSRF, Origin | `test_notifications.py`, `test_security.py` |
| PWA manifest/cache/update/offline/mobile | frontend unit tests and `e2e/pwa.spec.ts` |
| Keyboard, semantics, form labels, responsive browsers | `e2e/accessibility.spec.ts` on desktop and Pixel 7 |
| SEO, analytics privacy, mobile budget | frontend SEO/analytics tests and `e2e/performance.spec.ts` |
| Clean schema migration | pytest creates a new migrated database; `makemigrations --check` rejects drift |
| PostgreSQL dump/restore integrity | `scripts/rehearse-postgres-restore.sh` |
| Dependencies and tracked secrets | `scripts/audit-dependencies.sh`, `scripts/check-repo-safety.sh` |

Run the complete gate from a clean commit:

```bash
scripts/release-qualification.sh
```

The backend suite recreates an isolated database and applies every migration.
The frontend gate runs lint, TypeScript, all unit tests, a production build, and
desktop/Pixel 7 Playwright checks.

## PostgreSQL backup/restore rehearsal

The full gate calls `scripts/rehearse-postgres-restore.sh` and fails unless all
three safety variables are supplied:

```bash
AIRPROCHE_REHEARSAL_SOURCE_URL=postgresql://airproche_qualification@127.0.0.1:5432/airproche_qualification \
AIRPROCHE_REHEARSAL_ADMIN_URL=postgresql://airproche_qualification@127.0.0.1:5432/postgres \
AIRPROCHE_REHEARSAL_DATA_CLASSIFICATION=fictional \
scripts/release-qualification.sh
```

The source name must match `airproche_*qualification`, both URLs must use a
local host, and the source must contain fictional data only. The script refuses
to replace a pre-existing restore database. It creates a custom-format dump,
restores into a derived `_restore_test` database, runs Django and migration
checks, compares every managed model row count, reports the dump SHA-256, and
always removes the temporary dump and database. It must never target production
or another application. Migration rollback is not inferred from application
rollback and is never run blindly.

## Manual staging checks

After dedicated staging configuration exists, verify keyboard/focus behavior,
screen-reader labels, real SMTP delivery, Stripe test Checkout redirect and
webhook delivery, cancellation/refund reconciliation, and all staff actions.
PayPal is out of scope because it remains intentionally skipped.
