# Notifications and contact

Phase 10 adds a dedicated communications boundary under `apps.notifications`.

## Email lifecycle

Every supported email creates an `EmailNotification` record and one or more
`EmailDeliveryAttempt` records. Templates, subjects, and recipient sources are
fixed in server code. There is no public endpoint that accepts an arbitrary
recipient, subject, or template.

Booking-created and booking-status messages are registered with
`transaction.on_commit(..., robust=True)`. SMTP failures are therefore recorded
after the booking or Stripe settlement transaction commits and cannot roll back
business state. Repeated booking and webhook events reuse deterministic
notification keys.

Verification and password-reset delivery is observable, but raw single-use
tokens are never stored in notification context. These records are deliberately
not retryable. The existing resend flows issue a fresh token instead.

Staff with `view_emailnotification` can inspect delivery history. Retrying also
requires `change_emailnotification` and an `Idempotency-Key`. Reusing the same
key returns the existing attempt without a second provider call.

## Contact lifecycle

`POST /api/v1/contact/` accepts only the fixed contact schema and requires CSRF.
The endpoint applies:

- DRF's IP-based scoped throttle at five submissions per hour;
- a hidden honeypot that returns an opaque accepted response without persistence;
- a three-second minimum and two-hour maximum form age;
- strict lengths, topic choices, email validation, and control-character rejection;
- optional request idempotency with payload-conflict detection;
- an HMAC source fingerprint instead of storing the source IP.

Legitimate messages are persisted before a confirmation email is scheduled.
Email failure cannot roll back the message. Staff contact access uses Django
model permissions; only status, assignment, and staff notes are mutable, and
updates create Django admin log entries.

## Verification

Run:

```bash
DJANGO_USE_SQLITE_FOR_TESTS=true backend/.venv/bin/python -m pytest backend
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

Phase 10 acceptance currently passes 52 backend tests and 16 frontend tests.
