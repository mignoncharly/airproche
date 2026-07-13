# Airport Transfer Platform

Production-oriented airport-transfer booking platform for France. Phases 1-6, 8, and 9 are complete; Phase 7 PayPal remains intentionally skipped.

## Architecture

- `frontend/`: Next.js 16 App Router, React, strict TypeScript, Tailwind CSS.
- `backend/`: Django 6, Django REST Framework, PostgreSQL.
- `docs/`: architecture and phased delivery documentation.

See [the implementation plan](docs/IMPLEMENTATION_PLAN.md) for product decisions, security boundaries, and acceptance criteria.

## Local prerequisites

- Node.js 22+
- Python 3.12+
- PostgreSQL 16+

Copy `.env.example` to `.env` and replace local database credentials. `.env` is ignored and must never be committed.

## Backend setup

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements/dev-lock.txt
backend/.venv/Scripts/python backend/manage.py migrate
backend/.venv/Scripts/python backend/manage.py runserver
```

Run the isolated foundation tests:

```powershell
$env:DJANGO_USE_SQLITE_FOR_TESTS='true'
backend/.venv/Scripts/python -m pytest backend
```

SQLite is allowed only for fast unit tests. Development, staging, production, and PostgreSQL integration tests use `DATABASE_URL`.

## Frontend setup

```powershell
Set-Location frontend
npm install
npm run dev
```

Quality commands:

```powershell
npm run lint
npm run typecheck
npm test
npm run build
```

The production topology uses one public origin: Nginx routes pages to Next.js and `/api/*` to Django.

## Managed public content

Django Admin manages business contact details, services, FAQs, verified testimonials, and versioned legal documents. The public read model is available at `/api/v1/public/content/` with an ETag and a 60-second public cache policy.

Testimonials cannot be activated in Django Admin without a verification timestamp and internal source reference. Legal pages show an explicit unpublished state until approved text is published; the application does not ship invented legal copy.

## Customer authentication

The browser uses same-origin Django sessions and obtains a CSRF token before every authentication mutation. Available routes cover registration, login/logout, current user, verified profile updates, e-mail verification, verification resend, and password reset.

Registration remains closed until current Terms and Privacy documents are published in Django Admin. Successful registration records both exact document versions. Verification links expire after 24 hours; password-reset links expire after one hour; only HMAC token digests are stored.

## Coverage and price estimates

Django Admin manages airports, service areas, fixed route tariffs, tariff validity windows, capacities, and fixed/per-unit options. The public airport and zone pages only show records backed by an active tariff; no airport name or payable amount is hardcoded in the frontend.

The estimator at `/tarifs` sends route facts to `/api/v1/public/pricing/quotes/`. Django selects the eligible tariff, enforces lead time, booking horizon and capacity, calculates every line, and stores an expiring immutable quote snapshot. Browser-supplied amount or currency fields are rejected. Permission-scoped staff CRUD is exposed under `/api/v1/staff/` and records changes in Django’s durable admin log.

To publish a route, create an active airport and service area, then create an active tariff for the required direction and validity window. An airport or zone without a complete tariff-backed route remains absent from public coverage.

In local development, Next.js proxies `/api/*` to `BACKEND_INTERNAL_URL`. Production Nginx owns that routing. Configure a real SMTP backend, `DEFAULT_FROM_EMAIL`, and HTTPS `APP_BASE_URL` before production startup.

## Stripe payments

Phase 6 adds server-created Stripe Checkout, signed webhook settlement, payment status polling, and staff refund/reconciliation commands. Configure `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STRIPE_ENVIRONMENT=test` before enabling online payments. The browser never supplies the payable amount, and a redirect alone never confirms a booking. See [payment architecture](docs/PAYMENT_ARCHITECTURE.md).

## Customer dashboard

Phase 8 adds the authenticated `/compte` dashboard with upcoming and past bookings, payment state, eligible cancellation, fresh-quote repeat booking, and protected printable receipts. Guest booking remains available without an account. Receipts are explicitly booking/payment receipts rather than tax invoices until the VAT and accounting policy is decided. See [customer dashboard](docs/CUSTOMER_DASHBOARD.md).

## Operations dashboard

Phase 9 adds the staff-only `/operations` dashboard with real booking KPIs, filters, controlled transitions, notes, payment/refund visibility, and driver/vehicle assignment. Assignment conflicts and capacity overrides require an explicit reason and all sensitive changes are audited. See [operations dashboard](docs/OPERATIONS_DASHBOARD.md).
## Notifications and contact

Phase 10 persists supported email notifications and delivery attempts, sends
booking/account/contact mail outside business transactions, and exposes
permission-scoped staff observability and retry actions. The public contact form
uses CSRF, rate limiting, a honeypot, a form-age trap, fixed topics, control
character rejection, and idempotency. See
[notifications and contact](docs/NOTIFICATIONS_CONTACT.md).
## Progressive Web App

Phase 11 adds an installable public shell, native Android prompting where
supported, accurate Safari installation guidance, explicit service-worker
updates, and a generic offline page. Cache Storage contains only a fixed static
allow-list and never customer, booking, payment, authenticated API, cookie, or
token data. See [PWA architecture](docs/PWA.md).
