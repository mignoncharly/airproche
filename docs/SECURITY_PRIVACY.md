# Security and privacy hardening

Phase 13 reviewed the application as a same-origin Next.js and Django system
behind one trusted Nginx reverse proxy. PostgreSQL, Django, and Next.js must bind
only to loopback or private interfaces. Nginx is the only public application
entry point.

## Authorization and request integrity

Customer booking queries are owner-scoped. Guest access requires a UUID/reference
and a 256-bit bearer token stored only as an HMAC digest. Staff access through
shared booking/payment helpers requires the relevant `view_*`, `change_*`, or
`add_*` model permission; `is_staff` alone grants no booking, refund, reconcile,
or transition access.

Django session authentication enforces CSRF. Central API Origin middleware
rejects supplied untrusted Origin/Referer values on unsafe requests and requires
an Origin in production. The signed Stripe webhook is the only exemption. It
still requires a timestamped HMAC signature within the tolerance window.

Production rejects wildcard hosts, wildcard/non-HTTPS CSRF origins, weak Django
secrets, debug mode, and a non-HTTPS application URL. `APP_BASE_URL`, not a
request Host header, creates outbound links.

## Tokens and payments

Verification tokens expire after 24 hours and reset tokens after one hour. New
tokens revoke earlier unconsumed tokens; use is atomic and single-use. Guest
management tokens expire after 30 days. Raw account and guest tokens are never
stored in the database or notification context.

Account tokens, guest booking credentials, booking references in management
links, and Stripe Checkout session credentials use URL fragments. The client
captures and removes the fragment before making API calls, so Nginx/Next access
logs and HTTP referrers do not receive these values.

Stripe test mode is the default even when `APP_ENV=production`. Live mode
requires all of:

- `STRIPE_ENVIRONMENT=live`;
- an `sk_live_` key;
- `STRIPE_LIVE_MODE_CONFIRMED=true` after explicit launch approval;
- a live webhook secret configured for the final endpoint.

Payments and webhook events retain an environment marker. Amount, currency,
booking reference, payment identifier, session identifier, and environment are
matched before settlement. Mismatches are quarantined and never confirm a
booking.

## Abuse and network controls

Authentication, token, quote, booking, payment, contact, webhook, communication,
and staff operations endpoints have scoped throttles. Production uses Django's
PostgreSQL-backed cache so limits are shared across API workers. Deployment must
run after migrations:

```bash
python manage.py createcachetable airproche_cache
```

Set `DRF_NUM_PROXIES=1` only when one trusted Nginx proxy is present. Nginx must
overwrite, not append untrusted client values, for `X-Forwarded-For` and
`X-Forwarded-Proto`.

MFA is not implemented. Until MFA is deployed, production defaults the staff
network gate to enabled. `STAFF_ALLOWED_NETWORKS` must contain approved
administrator/VPN CIDRs. Forwarded client IPs are accepted only when the direct
peer is in `TRUSTED_PROXY_NETWORKS`. The gate covers Django Admin, staff APIs,
legacy booking transitions, refunds, and reconciliation. An empty allow-list
prevents production startup.

## Browser, cache, and logs

Non-public API responses default to `Cache-Control: no-store, private` and
`Pragma: no-cache`. Even an explicitly public API response becomes private when
a session cookie is present. The service worker retains its fixed static
allow-list and never caches an API response.

The production Next.js CSP restricts content, connection, worker, manifest,
frame, object, base, and form sources to the application. Framing is denied;
permissions, referrer, MIME-sniffing, opener, and resource policies are set.
Next.js currently requires inline boot/style support, so `unsafe-inline` remains
a documented residual risk; external script/network wildcards are forbidden.

Structured logs allow only correlation/event/status/provider fields. The
formatter redacts email, phone-like values, bearer credentials, token/session
parameters, Stripe secrets, and database URL credentials from messages and
exception text. Raw webhook bodies and SMTP exceptions are not logged.

## Retention and erasure

Retention periods require legal/business approval and have no hidden defaults.
The command is dry-run unless `--apply` is provided:

```bash
python manage.py enforce_data_retention \
  --booking-days APPROVED_DAYS \
  --contact-days APPROVED_DAYS \
  --notification-days APPROVED_DAYS
```

It anonymizes only terminal old bookings, preserving price/payment facts while
removing addresses, contact snapshots, free-text notes, guest credentials, and
customer association. It deletes old contact/email records, expired account and
guest tokens, and expired idempotency records.

An approved individual erasure request uses:

```bash
python manage.py anonymize_account --public-id USER_UUID
python manage.py anonymize_account --public-id USER_UUID --apply
```

The command refuses staff accounts and accounts with nonterminal bookings,
revokes login and tokens, anonymizes terminal bookings, and retains pseudonymous
consent/financial evidence. Staff/driver retention requires a separate access
and employment-policy review.

## Automated evidence

Run:

```bash
scripts/check-repo-safety.sh
scripts/audit-dependencies.sh
DJANGO_USE_SQLITE_FOR_TESTS=true backend/.venv/bin/pytest -q
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build
```

On 2026-07-13, both exact Python lockfiles and the npm lockfile reported no known
vulnerabilities. The repository scan found no tracked environment file, private
key, database dump, backup, uploaded personal media, or credential pattern.
PayPal configuration is explicitly rejected because PayPal remains skipped.

## Launch decisions still required

- exact public app/www/webhook/sender domains;
- approved administrator/VPN CIDRs or deployment of staff MFA;
- approved booking, contact, notification, staff, and driver retention periods;
- production SMTP provider and sender-domain authentication;
- explicit approval before Stripe live mode.
