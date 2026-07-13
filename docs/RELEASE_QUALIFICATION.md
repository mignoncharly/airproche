# Release qualification

Phase 14 uses fictional records, Stripe test fixtures, isolated Django test
databases, and browser emulation. Live payment credentials and production
personal data are forbidden.

## Automated matrix

| Journey or risk | Evidence |
| --- | --- |
| Guest/authenticated booking and idempotency | `test_bookings.py`, `test_authentication.py` |
| Cross-account dashboard, cancellation, receipts | `test_dashboard.py`, `test_security.py` |
| Stripe checkout, signed retries, mismatch, refund | `test_payments.py` |
| Operations confirmation, permissions, assignment conflicts/capacity | `test_operations.py`, `test_security.py` |
| Email failure, retry, commit timing | `test_notifications.py`, `test_bookings.py` |
| Contact abuse, injection, CSRF, Origin | `test_notifications.py`, `test_security.py` |
| PWA manifest/cache/update/offline/mobile | frontend unit tests and `e2e/pwa.spec.ts` |
| SEO, analytics privacy, mobile budget | frontend SEO/analytics tests and `e2e/performance.spec.ts` |
| Clean schema migration | pytest creates a new migrated database; `makemigrations --check` rejects drift |
| Dependencies and tracked secrets | `scripts/audit-dependencies.sh`, `scripts/check-repo-safety.sh` |

Run the complete gate from a clean commit:

```bash
scripts/release-qualification.sh
```

The backend suite recreates an isolated database and applies every migration.
The frontend gate runs lint, TypeScript, all unit tests, a production build, and
desktop/Pixel 7 Playwright checks.

## PostgreSQL backup/restore rehearsal

This cannot use another application’s database. After Phase 15 creates the
dedicated Airproche role/database, qualification must additionally:

1. create a fictional-data Airproche backup with `pg_dump --format=custom`;
2. restore it into a newly created Airproche-only `_restore_test` database;
3. run Django checks and row-count/integrity smoke queries against the restore;
4. drop only that restore-test database;
5. record timings and the tested backup artifact checksum.

Until this rehearsal passes, production deployment is blocked. Migration
rollback is never inferred from application rollback and is not run blindly.

## Manual staging checks

After dedicated staging configuration exists, verify keyboard/focus behavior,
screen-reader labels, real SMTP delivery, Stripe test Checkout redirect and
webhook delivery, cancellation/refund reconciliation, and all staff actions.
PayPal is out of scope because it remains intentionally skipped.
