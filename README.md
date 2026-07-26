# Airproche

Airproche is a booking platform for airport transfers in France. It covers the full path from a public price estimate to booking, payment, customer self-service and day-to-day operations.

The central design decision is straightforward: **the browser never decides the price, availability or payment state**. Those facts are calculated and verified by the backend.

## Architecture

| Area | Technology |
| --- | --- |
| Frontend | Next.js 16, React, strict TypeScript, Tailwind CSS |
| Backend | Django 6, Django REST Framework |
| Database | PostgreSQL |
| Payments | Stripe Checkout and signed webhooks |
| Production | Ubuntu, Nginx and systemd |

The public site and API share one origin. Nginx routes pages to Next.js and `/api/*` requests to Django.

## What is implemented

- Managed airports, service areas and tariff validity windows
- Server-side quotes with capacity and lead-time checks
- Guest and customer booking flows
- Email verification and password reset
- Stripe Checkout, webhook settlement and reconciliation tools
- Customer dashboard, cancellations, repeat booking and receipts
- Staff operations dashboard with audited status changes
- Driver and vehicle assignment with conflict checks
- Contact and notification delivery tracking
- Installable PWA shell with a privacy-safe cache policy
- SEO, structured data and consent-gated analytics
- Security hardening, retention commands and release qualification

PayPal is intentionally not included. Stripe remains in test mode until production checks and business configuration are complete.

## Run it locally

Requirements:

- Node.js 22+
- Python 3.12+
- PostgreSQL 16+

Copy `.env.example` to `.env` and add local database credentials.

### Backend

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements/dev-lock.txt
backend/.venv/Scripts/python backend/manage.py migrate
backend/.venv/Scripts/python backend/manage.py runserver
```

Fast unit tests can use SQLite:

```powershell
$env:DJANGO_USE_SQLITE_FOR_TESTS='true'
backend/.venv/Scripts/python -m pytest backend
```

Development, integration and production environments use PostgreSQL.

### Frontend

```powershell
Set-Location frontend
npm install
npm run dev
```

Quality checks:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

## Business rules worth knowing

- Public routes appear only when an active tariff supports them.
- A quote is calculated and stored by Django; browser-supplied amounts are rejected.
- A payment redirect does not confirm a booking. Settlement comes from a signed webhook.
- Registration stays closed until current Terms and Privacy documents are published.
- Testimonials require an internal source and verification timestamp.
- Customer, booking, payment and token data are never placed in the service-worker cache.

## Production

Deployment is operator-driven and does not use Docker. The runbooks in `docs/` and `deploy/` cover isolated releases, secrets, Nginx, systemd, certificates, backups, restore rehearsals and rollback.

Before calling an installation production-ready, run `scripts/release-qualification.sh` from a clean commit and complete the PostgreSQL backup/restore rehearsal.
