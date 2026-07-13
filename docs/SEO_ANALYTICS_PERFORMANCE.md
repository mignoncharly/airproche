# SEO, analytics, and performance

Phase 12 exposes search metadata only for genuinely public content and measures
conversion milestones without collecting personal data.

## Search publication

`APP_BASE_URL` is the sole canonical origin. Public pages use absolute canonical
and Open Graph URLs. `robots.txt` points to the generated sitemap and excludes
API, customer, staff, authentication, booking-management, payment-return, and
offline routes. Those private page modules also declare `noindex` metadata.

The dynamic sitemap contains only:

- the public core pages;
- services, FAQ, and contact routes when corresponding managed content exists;
- active airports and service areas backed by a currently valid active tariff.

The public location list and detail API enforces the same tariff-backed rule, so
a hand-crafted URL cannot publish an uncovered entity. The homepage
`LocalBusiness` JSON-LD uses published business settings and managed services
only. Airport JSON-LD is emitted only after the covered airport is resolved.
JSON-LD serialization escapes `<` to prevent a script-closing injection.

No revalidation endpoint is required: the sitemap is dynamic and the existing
public reads use the bounded server cache. A future webhook must authenticate
before invalidating content and must never accept a caller-provided URL.

## Analytics boundary

Analytics is disabled until the visitor explicitly grants consent. Refusal and
absence of consent produce no event dispatch. The adapter supports only these
milestones:

- `quote_started` and `quote_created`;
- `booking_started` and `booking_created`;
- `payment_started` and `payment_succeeded`;
- `contact_submitted`.

Each event has a fixed property allow-list. Current values are limited to trip
type, currency, Stripe as provider, and the fixed contact topic. Unknown events,
unknown keys, personal-data key names, email-like values, and phone-like values
throw before the consent check. The adapter writes only to the in-browser
`dataLayer`; no third-party analytics script is loaded in this phase.

Consent is stored as `granted` or `denied` in local storage and is synchronized
through browser events. It is not an authorization decision and is never sent
with booking, payment, or contact payloads.

## Mobile performance budget

`frontend/performance-budgets.json` defines the release budget for Pixel 7
Chromium emulation:

- DOM content loaded: at most 3000 ms;
- window load: at most 5000 ms;
- JavaScript transfer: at most 650000 bytes;
- cumulative layout shift: at most 0.1;
- no horizontal viewport overflow.

The Playwright check runs against the production Next.js build. Timings on a
busy shared host can vary; a repeatable regression must be investigated rather
than increasing a budget without a documented reason.

## Verification

```bash
cd backend
.venv/bin/python manage.py check
.venv/bin/pytest -q

cd ../frontend
npm run lint
npm run typecheck
npm test
npm run build
npm run test:e2e
```

Tests cover canonical generation, active-only sitemap entries, structured-data
escaping, robots/private-page indexing, consent gating, PII rejection, and the
real mobile browser budget.
