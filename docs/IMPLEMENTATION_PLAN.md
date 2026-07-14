# Airport Transfer Platform — Architecture and Implementation Plan
Status: Phases 0-6 and 8-14 complete; Phase 7 (PayPal) skipped by decision; Phase 15 tooling is prepared but production deployment is not complete
Last updated: 2026-07-14
Source of truth: `prompt.md`

## 1. Purpose and current-state audit

This document defines a production-oriented MVP for a private airport-transfer service operating initially in France. It is the implementation contract for the repository: later architecture documents may add detail, but must not contradict the boundaries, lifecycle rules, or security controls here without an explicit architecture decision record.

The repository audit found only `prompt.md`. There is no application code, package manifest, database schema, environment template, test suite, Git history, or deployment configuration. Therefore Phase 0 is the first phase; no feature should be represented as implemented yet.

The platform must combine four coherent products:

1. A fast, French-first marketing and local-SEO site.
2. A guest-friendly quote, booking, and real-payment flow.
3. A customer area for booking management.
4. An operational back office for bookings, payments, drivers, content, and real reporting.

The architecture is deliberately a modular monolith rather than microservices. Next.js renders the web experiences; Django owns the domain, persistence, authentication, authorization, pricing, payment orchestration, and operational APIs; PostgreSQL is the single system of record.

## 2. Business assumptions and unresolved decisions

### 2.1 Safe provisional defaults

These defaults allow implementation to proceed. Each must remain configurable where indicated.

| Topic | Provisional MVP decision | Reason and implementation consequence |
|---|---|---|
| Pricing | Fixed airport-to-service-area tariffs, with explicit option surcharges and admin-only custom quotes | Predictable, auditable, and reliable without a costly routing provider. No arbitrary browser amount is accepted. |
| Price visibility | Show an authoritative quote before collecting personal details | Reduces abandonment and supports transparent pricing. |
| Payment | Online payment in full is enabled; Stripe is primary and PayPal is optional when configured | Simplest confirmation rule. Payment mode is an admin setting, but unsupported modes are not shown. |
| Pay on arrival/deposits | Architecture supports modes, but both are disabled at launch | They require policy and reconciliation decisions. |
| Booking lead time | Default 12 hours; maximum horizon 365 days; admin-configurable | Same-day trips are rejected when inside lead time unless an admin creates/overrides the booking. |
| Coverage | Active airports, service areas, and tariff routes in the database define availability | No airport or geographic list is hardcoded in the frontend. |
| Drivers | Multiple-driver data model; manual assignment only | Works for one driver now without building dispatch optimization. |
| Flight tracking | Manual flight details and operational updates only | The UI must never claim live tracking. |
| WhatsApp | A clearly labelled contact link only | Automated WhatsApp requires a Business API provider, consent rules, and templates. |
| Accounts | Guest checkout is first-class; optional customer registration | Account creation is never a booking prerequisite. |
| Currency | EUR only at launch | Models store ISO currency codes and can be extended, but a quote/payment never mixes currencies. |
| Language | French only at launch with locale-ready structure | English and German are future catalog additions, not fake language switches. |
| Documents | Provider receipts plus a printable booking/payment receipt | Tax invoices wait for the VAT/accounting decision. |
| Child seats | Configurable option with quantity, availability, and surcharge | Hidden or unavailable when disabled by operations. |
| Accessibility | Capture an assistance request; do not promise an accessible vehicle unless a compatible active vehicle is assigned/confirmed | Prevents misleading claims. |
| Waiting/delays | A configurable included waiting window; operational contact after that window | No automatic extra charge in MVP without an approved policy. |
| Luggage | Capacity is validated against the selected tariff/vehicle category; exceptional luggage becomes a manual-review condition | Avoids accepting an operationally impossible trip. |
| Driver details | Released by operations after assignment, and visible only to authorized customer/guest access | Phone exposure and timing are configurable. |
| Supply model | The company is treated as the contracting transport provider | Independent-contractor marketplace logic is excluded pending a business/legal decision. |
| Background work | Database-backed synchronous email after transaction commit initially; no Redis/Celery | Add a queue only when measured reliability or volume justifies it. Failed sends remain visible and retryable by an admin. |
| Maps | Structured addresses can be entered without autocomplete; provider fields are nullable | Autocomplete is enabled only with a configured, restricted provider key and never determines price. |
| Analytics | Consent-aware, privacy-conscious analytics adapter; disabled until configured | No personal data enters analytics events. |

### 2.2 Launch blockers requiring the business owner

These do not block foundation work, but they block production acceptance of the affected feature:

- Legal entity details, trading name, SIREN/SIRET, registered address, publication director, host details, and approved legal notice.
- Final cancellation deadlines, refund percentages, no-show treatment, late-flight treatment, and any waiting-time charges.
- VAT applicability/rate, invoice numbering requirements, and whether a compliant invoice or only a receipt is required.
- Exact service areas, airport coverage, tariff amounts, option prices, passenger/luggage limits, and vehicle capabilities.
- Whether pay-on-arrival or deposits will be offered. Neither will be enabled without a defined collection/refund/reconciliation policy.
- Whether same-day requests are accepted and the final minimum lead time.
- Production Stripe account/webhook keys and whether PayPal is enabled at launch; PayPal credentials and approved sandbox-to-live process if enabled.
- Business contact channels, support hours, escalation procedure, email sender domain, and operational recipients.
- Approved privacy, retention, cookie, cancellation, and terms text after professional legal review.
- Driver employment/contractor model, insurance/transport authorizations, and rules for exposing driver contact details.
- Confirmed accessibility claims and available equipment. The product will record needs but must not make unsupported promises.
- Chosen analytics, maps, error-monitoring, SMTP, and hosting providers, including data-processing agreements where required.

### 2.3 Decisions explicitly deferred

Live flight status, automated WhatsApp/SMS, automatic dispatch, driver PWA, corporate accounts, recurring bookings, promotions, loyalty, multi-currency checkout, multi-country tax logic, and a general-purpose CMS are future features. The model exposes stable extension points without implementing inactive buttons or placeholder screens.

## 3. Final architecture

### 3.1 Repository layout

```text
frontend/
  app/                  # App Router routes, layouts, metadata, error boundaries
  components/           # accessible shared UI primitives and composites
  features/             # booking, account, admin, content feature modules
  lib/                  # API client, i18n, validation, analytics adapter
  public/               # icons and static assets
  tests/                # unit/component tests
backend/
  config/               # settings, URLs, ASGI/WSGI, logging
  apps/
    accounts/
    locations/
    pricing/
    bookings/
    payments/
    drivers/
    notifications/
    content/
    contact/
    audit/
    core/
  tests/
docs/
scripts/
deploy/                 # example systemd and Nginx templates
e2e/                    # Playwright critical journeys
```

Application boundaries are Django apps, not independently deployed services. Cross-app writes use domain service functions and database transactions, not HTTP calls. Payment-provider adapters isolate provider SDK details without hiding provider-specific semantics.

### 3.2 Runtime topology

```text
Browser / installed PWA
        |
      HTTPS
        |
      Nginx
      /   \
 pages     /api/*, /admin/*, /django-admin/*
   |                    |
Next.js              Gunicorn/Django
   |                    |
   +-- server reads ----+
                        |
                    PostgreSQL
                        |
              SMTP / Stripe / PayPal
```

Nginx exposes a single canonical origin. It routes application pages to Next.js and API/administrative paths to Django. This permits secure, host-only session and CSRF cookies without permissive cross-origin configuration. Next.js server components may call Django through a private loopback URL; the browser uses same-origin `/api/v1/...` routes. Provider webhooks terminate directly at narrowly scoped Django endpoints.

Production uses two systemd application services (Next.js and Gunicorn), PostgreSQL bound locally/private-network only, Nginx, Certbot, a Python virtual environment, and a pinned Node.js LTS runtime compatible with Next.js 16. No Docker is introduced.

### 3.3 Frontend/backend responsibility boundary

The frontend owns:

- Rendering, responsive interaction, accessible step navigation, local non-authoritative validation, and recoverable form state.
- SEO presentation, JSON-LD generated from backend content, install guidance, and consent-aware analytics event emission.
- Displaying server-provided quotes, booking/payment state, field errors, and safe recovery actions.
- Never embedding business secrets, calculating payable totals, authorizing transitions, or treating a redirect as payment proof.

The backend owns:

- All persisted domain state and authoritative validation.
- Availability, tariff selection, immutable price snapshots, booking references, state transitions, cancellation/refund eligibility, and audit records.
- Authentication, permissions, guest access verification, rate limits, CSRF, idempotency, and data minimization.
- Creating and reconciling Stripe/PayPal objects, verifying signatures, and deciding when a booking is confirmed.
- Email rendering context, delivery attempts, retry state, operational reports, and content/settings APIs.

Shared concepts are described by a versioned OpenAPI schema generated from Django REST Framework. Frontend TypeScript API types are generated from that schema; validation logic remains authoritative in Django and is mirrored in Zod only for user feedback.

### 3.4 API conventions

- Versioned JSON API under `/api/v1/`; nouns use stable public UUID/reference fields rather than database IDs.
- Consistent error envelope with machine code, localized safe message, field errors, and request correlation ID.
- Cursor or page-number pagination per collection; explicit allow-listed sort/filter fields.
- `Idempotency-Key` is required for quote conversion, booking submission, payment creation, capture, cancellation, refund, and resend operations where repetition has side effects.
- Optimistic concurrency uses an `updated_at`/version precondition on high-risk admin edits; conflicting edits return `409`.
- API schema and browsable API are disabled or staff-restricted in production as appropriate.

## 4. Domain model

All money uses `Decimal` database fields with an ISO-4217 currency code. All datetimes are timezone-aware and stored in UTC; airport/service time is displayed using the relevant IANA timezone (default `Europe/Paris`). Public identifiers are UUIDs or random references, never sequential IDs.

### 4.1 Accounts and authorization

- **User**: custom user from the first migration; email as normalized unique login, password hash, names, phone, preferred locale, email verification timestamp, active/staff flags, timestamps.
- **EmailVerificationToken / PasswordResetToken**: hashed one-time token, purpose, expiry, consumed timestamp, request metadata with retention limits.
- **ConsentRecord**: user or booking subject reference where lawful, consent type/version, granted/withdrawn timestamp, minimal provenance.
- **Role/permissions**: Django groups and explicit permissions for customer, operations, dispatcher-ready, finance, content manager, and administrator. MVP staff may hold multiple groups.

### 4.2 Locations and service configuration

- **Airport**: public UUID, name, IATA, slug, city, country code, address, coordinates, IANA timezone, terminal guidance, description, SEO title/description, active/order fields.
- **ServiceArea**: public UUID, slug, name, type, country/region/city/postal descriptors, description, optional structured boundary/provider reference, active/order fields.
- **AddressSnapshot**: embedded booking fields or owned record containing formatted address, locality, postal/country code, coordinates, provider/place ID. A snapshot is never mutated by later provider data.
- **BusinessSettings**: singleton/versioned configuration for identity, contact channels, currency, lead/horizon limits, payment modes, included wait text, driver-detail policy, social links, and feature flags. Secrets never live here.

### 4.3 Pricing and quotes

- **Tariff**: airport, service area, direction/booking type, fixed base amount, currency, valid-from/to, active flag, capacity constraints, priority, and database uniqueness preventing overlapping active definitions where enforceable.
- **TariffOption**: option type (child seat, oversized luggage, additional stop where supported), pricing method allowed by MVP, amount, limits, active period.
- **Quote**: random public UUID, normalized route inputs, schedule, passenger/luggage/options counts, matched tariff, calculated total/currency, calculation version, status, expiry, and optional manual-review reason.
- **QuoteLine**: immutable label/code, quantity, unit amount, total, tax treatment field, and calculation metadata.
- **PriceSnapshot / PriceLine**: copied to a booking in the same transaction as conversion. Historical totals never query live tariff values.

MVP calculation is deterministic: select one eligible fixed route tariff, add enabled fixed/per-unit options, validate capacities and schedule, then quantize once to currency precision. Manual quotes are explicitly staff-created, audited, expire, and cannot be silently substituted for automated pricing.

### 4.4 Bookings and operations

- **Booking**: public UUID, unpredictable human reference (for example `TR-2026-` plus random uppercase characters), optional customer, source, booking type, route/address snapshots, airport/terminal/flight fields, requested pickup and scheduled arrival datetimes, passenger/luggage/accessibility/options data, booker/passenger contact snapshots, locale, status, payment mode, price snapshot totals, cancellation fields, management-token generation, and timestamps.
- **BookingStatusHistory**: booking, from/to statuses, actor user or system actor, safe note, correlation ID, timestamp. Append-only.
- **BookingNote**: internal/customer-visible classification, author, content, timestamps; sensitive visibility enforced at serialization.
- **GuestAccessToken**: booking, SHA-256/HMAC token digest only, purpose, expiry, consumed/revoked/rotated timestamps, attempt counters. Raw tokens are sent once and never logged.
- **IdempotencyRecord**: scoped key, actor/session fingerprint, request hash, response/result pointer, status and expiry; a reused key with different input is rejected.
- **CancellationPolicySnapshot**: policy version/text, deadline, computed outcome stored when booking is created/cancelled.
- **DriverAssignment**: booking, driver, vehicle, assigned/unassigned timestamps and actors, release-to-customer timestamp; history is retained.

### 4.5 Drivers and vehicles

- **Driver**: names, email, phone, active flag, optional protected profile media reference, notes, service-area relation, timestamps.
- **Vehicle**: make/model/registration, passenger/luggage capacity, child-seat/accessibility capabilities, active flag, timestamps.
- Driver and vehicle capacity are validated during assignment. The MVP does not optimize schedules; it detects obvious overlapping active assignments and requires an authorized override with an audit reason.

### 4.6 Payments and refunds

- **Payment**: public UUID, booking, provider, normalized status, amount/currency, provider order/session/payment/capture identifiers as applicable, environment mode, idempotency key, failure code/safe message, provider metadata allow-list, timestamps. Unique constraints cover provider identifiers.
- **PaymentAttempt**: payment, attempt number, status, provider request correlation identifier, safe failure fields, timestamps.
- **Refund**: payment, amount/currency, reason, normalized status, provider refund ID, requested/completed actor/times, idempotency key. Sum of successful/pending refunds cannot exceed captured amount.
- **WebhookEvent**: provider, environment, provider event ID, type, signature-valid flag, processing status/attempts, booking/payment association, received/processed timestamps, minimal redacted payload or encrypted/retained raw payload only if operationally justified. Provider+environment+event ID is unique.

### 4.7 Content, contact, notifications, and audit

- **FAQ**, **Testimonial**, **ServiceContent**: active/published status, ordering, French content, optional SEO fields. Testimonials are never seeded as real customer claims.
- **LegalDocument**: document type, version, effective timestamp, body/link, publication state; publication requires real approved text.
- **ContactMessage**: contact fields, subject/body, state, timestamps, spam signals; protected as personal data.
- **Notification** and **NotificationAttempt**: booking/user, template/version, channel, recipient digest/redacted address, status, provider message ID, attempt count, failure category, timestamps. No asynchronous queue is implied.
- **AuditEvent**: actor, action, target type/public identifier, safe before/after diff, correlation ID, timestamp, source IP in truncated/retention-controlled form. Append-only to application roles.

## 5. Booking lifecycle

Payment state and booking state are separate. A failed payment does not invent an operational trip state; a booking can have multiple payment attempts but at most one satisfied amount obligation.

### 5.1 Statuses

`DRAFT` → `PENDING_PAYMENT` → `CONFIRMED` → `DRIVER_ASSIGNMENT_PENDING` → `DRIVER_ASSIGNED` → `PASSENGER_CONTACTED` → `DRIVER_EN_ROUTE` → `DRIVER_ARRIVED` → `PASSENGER_PICKED_UP` → `IN_PROGRESS` → `COMPLETED`

Terminal/exception states: `CANCELLED`, `NO_SHOW`. `PAYMENT_PROCESSING` is not used as an operational booking status; payment processing belongs to `Payment.status`. This removes ambiguity and prevents provider latency from corrupting operations.

### 5.2 Controlled transitions

| From | To | Allowed actor/condition |
|---|---|---|
| DRAFT | PENDING_PAYMENT | Booker/system after server validation, valid unexpired quote conversion, and atomic price snapshot |
| PENDING_PAYMENT | CONFIRMED | System only after verified sufficient payment, or authorized staff when an enabled pay-later mode applies |
| CONFIRMED | DRIVER_ASSIGNMENT_PENDING | System immediately when assignment is required |
| DRIVER_ASSIGNMENT_PENDING | DRIVER_ASSIGNED | Operations/admin after active compatible driver/vehicle assignment |
| DRIVER_ASSIGNED | PASSENGER_CONTACTED | Operations/admin after actual contact; note optional |
| PASSENGER_CONTACTED or DRIVER_ASSIGNED | DRIVER_EN_ROUTE | Assigned driver-capable staff or operations |
| DRIVER_EN_ROUTE | DRIVER_ARRIVED | Assigned driver-capable staff or operations |
| DRIVER_ARRIVED | PASSENGER_PICKED_UP | Assigned driver-capable staff or operations |
| PASSENGER_PICKED_UP | IN_PROGRESS | Assigned driver-capable staff or operations |
| IN_PROGRESS | COMPLETED | Assigned driver-capable staff or operations |
| Eligible nonterminal state | CANCELLED | Customer/guest before policy deadline, or authorized staff; financial outcome handled separately |
| DRIVER_ARRIVED | NO_SHOW | Operations after policy procedure and required reason |

Admin corrections do not permit arbitrary status assignment. Exceptional rollback/correction is a dedicated, highly privileged command requiring a reason and audit diff. Every successful transition locks the booking row, validates the current state, writes history, and schedules notifications only after transaction commit.

### 5.3 Booking creation

1. Anonymous or authenticated customer requests a quote with route/schedule/capacity inputs.
2. Backend validates service coverage and creates an expiring quote with line items.
3. Frontend collects booker/passenger information and options in accessible steps, preserving recoverable state locally but not secrets.
4. Backend revalidates the quote, lead time, capacity, and contact data, then atomically creates the booking, price snapshot, initial history, and guest access credential as applicable.
5. Backend creates a payment through the selected enabled provider. Repeated submissions with the same idempotency key return the existing result.
6. The confirmation page polls/refreshes server state; it never infers success from the provider redirect.
7. On verified settlement, the system confirms the booking and sends a confirmation. Pending or failed payments show safe retry/reconciliation paths.

## 6. Payment architecture

### 6.1 Common rules

- Provider adapters expose narrowly useful operations: create checkout/order, capture where required, parse/verify webhook, fetch authoritative status, and refund. Provider-specific IDs and event meanings remain visible in their adapter/domain mapping.
- Amount, currency, booking reference, environment, and allowed payment mode come only from the locked backend booking/price snapshot.
- One booking can have multiple failed/cancelled attempts; concurrency controls prevent more than one successful full obligation.
- Webhook handling verifies authenticity before state changes, deduplicates the event, locks affected rows, enforces monotonic normalized transitions, records audit context, and acknowledges only after durable processing.
- Return pages are status views, not confirmation authorities. Unknown/pending events trigger safe provider reconciliation.
- Test and live identifiers are stored with an environment marker and cannot be mixed. Startup checks fail production deployment when test credentials are detected.

### 6.2 Stripe lifecycle

Stripe Checkout is the MVP choice because it minimizes PCI scope and handles authentication such as 3-D Secure on a Stripe-hosted page.

1. Client sends booking public ID/provider choice and an idempotency key; no amount is accepted.
2. Backend locks the booking, confirms it is payable and Stripe is enabled, reuses or creates a `Payment`, then creates a Checkout Session with server amount/currency, internal references in metadata, success/cancel URLs, and a provider idempotency key.
3. Backend persists the session ID before returning the Checkout URL.
4. Stripe redirects the browser, but the UI displays pending until backend state is verified.
5. `/api/v1/webhooks/stripe/` reads the raw body, verifies the configured endpoint signature and environment, stores/deduplicates the event, and handles relevant Checkout/payment/refund events.
6. A verified paid amount/currency and matching metadata transition the payment to `SUCCEEDED`; the same transaction confirms the eligible booking. Mismatch is quarantined for finance review and never confirms the booking.
7. Failed/expired sessions update the attempt/payment without cancelling a booking that has another valid attempt.
8. Refund commands calculate eligibility server-side, create a pending `Refund`, call Stripe with idempotency, and finalize from the authoritative response/webhook. Partial and full refund states are derived from successful refund totals.

### 6.3 PayPal lifecycle

PayPal remains an independent adapter and is shown only when fully configured.

1. Client requests an order for a payable booking with an idempotency key; no amount is accepted.
2. Backend obtains/caches a server-side PayPal access token, creates an order with exact amount/currency, booking reference/custom ID, return/cancel URLs, and `PayPal-Request-Id`.
3. Backend stores the order ID and returns only safe approval data.
4. After buyer approval, the browser asks the backend to capture. The backend locks the payment and performs one idempotent server-side capture; browser approval alone is not success.
5. Backend verifies capture status, amount, currency, payee/merchant identity, and environment before marking `SUCCEEDED` and confirming the booking.
6. `/api/v1/webhooks/paypal/` verifies event authenticity using PayPal's supported verification flow, deduplicates events, and reconciles captures/refunds/reversals.
7. Capture races between browser callback and webhook converge through row locks, unique provider capture IDs, and monotonic transitions.
8. Refunds use the specific capture ID, server-calculated amount, idempotency, and webhook/retrieval reconciliation.

## 7. Authentication and authorization

- Django session authentication is used through the single public origin. Cookies are `Secure`, `HttpOnly`, host-only, and use an appropriate `SameSite` policy. State-changing requests require CSRF tokens and origin checks.
- Passwords use Django's current strong password hasher and validators. Login/reset/register endpoints are rate-limited without enabling account enumeration.
- Email verification is required before sensitive account actions; a guest can still complete a paid booking using verified payment/contact flows.
- Object permissions require `booking.customer_id == request.user.id` for customers. Staff permissions are explicit per command; list querysets are filtered before serialization.
- Guest management uses at least 256 bits of random entropy. Only a digest is stored. Tokens are purpose-bound, expiring, revocable/rotatable, and never authorization by booking reference alone. Sensitive actions require an email one-time verification step or authenticated account re-check.
- Admin uses the custom operational UI for routine work. Django Admin is restricted to staff with granular permissions and low-level maintenance needs; it is not the sole operations product.
- MFA for privileged staff is a production-launch requirement if supported by the chosen auth package; otherwise admin access must be additionally network-restricted until MFA is implemented.

## 8. Security and privacy architecture

### 8.1 Trust boundaries and controls

- **Browser boundary:** all inputs are hostile; Django validates types, ownership, state, amount, schedule, and transitions. Frontend validation is convenience only.
- **Provider boundary:** webhook signatures, environment, merchant identity, amount, currency, metadata, and monotonic event state are verified. Raw provider payloads are minimized and redacted in logs.
- **Staff boundary:** least-privilege permissions, explicit high-risk commands, re-authentication for sensitive actions where practical, append-only audit events, and no arbitrary mass assignment.
- **Network boundary:** HTTPS only, HSTS after validation, local-only database, firewall permitting SSH/HTTP/HTTPS, trusted proxy settings, strict hosts/origins, and no debug pages in production.
- **Data boundary:** secrets only in root-readable environment files/systemd credentials; database backups encrypted and access-controlled; personal-data exports and deletion/anonymization follow approved retention rules.

### 8.2 Web controls

- CSP designed around Next.js, Stripe, and PayPal allow-lists; `frame-ancestors`, `object-src`, `base-uri`, Referrer-Policy, Permissions-Policy, MIME sniff prevention, and secure caching for authenticated pages.
- Strict CORS: unnecessary under normal same-origin deployment; no wildcard origins or credentials across arbitrary domains.
- DRF throttles plus Nginx edge limits for login, reset, quote, booking, contact, token verification, and webhooks. High-value operations also use idempotency and database constraints.
- ORM queries, serializer allow-lists, output escaping, sanitized rich content, honeypot/time trap on contact, and optional Turnstile only if abuse justifies it.
- Correlation IDs propagate through Nginx/Next.js/Django logs. Logs exclude passwords, raw access tokens, cookies, card data, secrets, and unnecessary passenger details.
- Dependency scanning, pinned lockfiles, secret scanning, migration checks, static analysis, and production configuration checks run in CI.

### 8.3 Privacy/retention baseline

Collect only operationally needed details. Analytics uses event names and coarse non-personal attributes only. Consent records are versioned where consent is the lawful basis. Retention durations remain configuration/documentation blockers until legally approved; deletion workflows must preserve legally required financial/audit facts while anonymizing unnecessary contact/passenger data. Legal documents must be marked for professional review and may not claim guaranteed compliance.

## 9. PWA, accessibility, SEO, and performance

### 9.1 PWA strategy

- Next.js serves a standards-compliant manifest, maskable/regular icons, theme colors, and a minimal service worker.
- Installability enhances the responsive site; all critical booking/account/admin journeys work in the browser without installation.
- Cache only versioned static assets and a safe offline fallback. Never cache authenticated API responses, booking data, payment pages, or personal form submissions.
- Android gets `beforeinstallprompt` guidance where supported after meaningful engagement. iPhone/iPad gets contextual French Share → Add to Home Screen instructions; no claim of a native install banner.
- Updates are conservative and notify users before reloading during an active form. `prefers-reduced-motion`, standalone display, safe areas, and touch target sizing are tested.
- Push notifications are not part of MVP.

### 9.2 Accessibility

Target WCAG 2.2 AA: semantic landmarks, keyboard operation, visible focus, skip links, sufficient contrast, 44px-class touch targets, labelled fields, inline error association and summary, status announcements, reduced motion, accessible dialogs, and no color-only meaning. Automated axe checks supplement keyboard and screen-reader smoke tests.

### 9.3 SEO/local SEO

- Server-rendered/indexable public pages; account, booking management, confirmation, admin, and payment recovery pages use `noindex` and authenticated pages disallow caching.
- Dynamic airport and service-area routes use backend slugs with canonical URLs, localized metadata, breadcrumbs, and real content. Inactive entities return 404/410 intentionally and leave redirects when slugs change.
- Generate XML sitemap(s), robots.txt, Open Graph metadata, and JSON-LD (`LocalBusiness`/most specific valid subtype, `Service`, `FAQPage` only for visible FAQs, `BreadcrumbList`). Never fabricate ratings, reviews, prices, opening hours, or coverage.
- Consistent business name/address/phone, service areas, contact details, and Google Business Profile linking support local SEO.
- French is the launch locale under one deliberate URL strategy; future locales use route segments and correct `hreflang`, not duplicate unlocalized pages.

### 9.4 Performance

Use server components by default, next/image with appropriately licensed assets, font subsetting/self-hosting where permitted, route-level code splitting, bounded client JavaScript, cached public content with revalidation, compressed static assets, database indexes, and query-count checks. Budgets are established for mobile Core Web Vitals and measured in CI/staging; third-party payment/analytics scripts load only when needed/consented.

## 10. Deployment and operations architecture

- Ubuntu LTS VPS, non-root deploy user, Nginx, Certbot, PostgreSQL, Python virtualenv, Gunicorn, Node.js process for Next.js, and systemd units with restart limits and hardening.
- Separate local/staging/production databases, domains, environment files, provider credentials, email configuration, and storage. Production startup rejects debug mode, weak/missing secret keys, insecure origins, and test payment credentials.
- Releases are immutable timestamped directories or Git revisions with a `current` symlink, dependency install/build, migration preflight, database backup for risky migrations, `migrate`, static collection, service restart, and health/smoke verification. Rollback uses the previous release; database migrations require explicit backward-compatible/restore planning.
- Public `/health/live` reports process health only. Protected/internal readiness checks database connectivity without exposing versions, credentials, or stack traces.
- Daily encrypted PostgreSQL backups plus media backups if uploads are introduced; off-host copy, documented retention, checksums, monitoring, and scheduled restore drills to a non-production database.
- Structured JSON logs feed journald/log rotation; alerts cover application errors, health failure, webhook processing backlog/failure, payment reconciliation anomalies, backup failure, disk use, certificate expiry, and email retry failure.
- Redis/Celery are not deployed initially. A transactional outbox plus a systemd timer/management command is the preferred first reliability upgrade if synchronous post-commit notification retries prove insufficient.

## 11. MVP scope versus future scope

### MVP

- French marketing pages, dynamic airports/service areas, real FAQs/content/testimonials, contact flow, legal-page framework, and local SEO.
- Authoritative fixed-zone quote, mobile multi-step guest/customer booking, immutable price snapshot, Stripe Checkout, optionally PayPal when configured, verified webhooks, receipts, cancellation/refund rules.
- Registration, verification, login/logout/reset, customer booking list/details, secure guest management, eligible cancellation, and repeat-booking prefill through a fresh quote.
- Operational dashboard with real KPIs, search/filter/detail, controlled transitions, notes, manual booking, driver/vehicle assignment, payment/refund visibility, resend actions, communication and audit history.
- Email confirmations/status notifications with persisted delivery results, contact link for WhatsApp, responsive accessible UI, installable PWA shell, health/logging/backups/deployment docs.

### Future, deliberately not represented as active

- Live flight API, distance/time dynamic routing, automatic driver dispatch, driver-specific app/PWA, push, automated SMS/WhatsApp, corporate accounts, recurring trips, promo/loyalty, multi-currency, additional locales/countries, complex content CMS, and marketplace/contractor settlement.

## 12. Major risks and edge cases

| Risk/edge case | Required mitigation |
|---|---|
| Duplicate clicks, retries, or two browser tabs | Idempotency key + request hash, row lock, unique constraints, deterministic existing result |
| Webhook arrives before redirect/capture response, out of order, or repeatedly | Provider event uniqueness, monotonic state rules, row locking, reconciliation command |
| Amount/currency/merchant mismatch | Quarantine and alert; never confirm booking |
| Quote expires or tariff changes mid-form | Recalculate server-side, show explicit changed-price consent, preserve non-payment form data |
| Last available capacity/route deactivates | Revalidate atomically at conversion and payment creation; safe unavailability response |
| Daylight-saving transition or ambiguous local time | Accept local date/time with IANA zone, reject nonexistent times, explicitly resolve ambiguity, store UTC plus zone/context |
| Flight scheduled after midnight or delayed into another day | Store flight arrival separately from requested pickup and allow audited operational adjustment |
| Customer books for another passenger | Separate contact snapshots, privacy-aware notifications, clear authorization and consent copy |
| Guest link forwarded/leaked | High entropy, digest storage, expiry/revocation, no-referrer on sensitive pages, additional verification for destructive/sensitive actions |
| Refund API times out after provider accepted it | Persist pending request/idempotency key and reconcile before retrying |
| Booking cancelled while payment succeeds | Lock and policy-driven reconciliation; flag/refund rather than resurrecting silently |
| Driver/vehicle double-booked or capacity mismatch | Conflict/capacity validation with privileged, reasoned override only |
| Email fails after successful payment | Booking remains confirmed; durable notification attempt, admin alert/retry, visible confirmation page |
| Maps/autocomplete unavailable | Manual structured address path remains functional; price still tariff-based |
| Service worker exposes personal data | Static-only cache allow-list; deny API/auth/payment caching |
| Admin KPI time boundaries differ | Store UTC, compute operational reporting using configured business timezone and define metric semantics |
| Unsupported accessibility request | Do not auto-confirm capability; route to manual review with clear customer communication |
| Provider test/live mix-up | Credential/ID environment checks at startup and per payment/webhook |
| Personal data in logs/analytics | Central redaction, safe serializers, event schema allow-lists, tests |
| Legal policy changes | Version and snapshot applicable policy on booking; preserve historical decision basis |

## 13. Phased implementation plan

Each phase ends with updated documentation and demonstrable acceptance criteria. A feature is not complete unless its backend, frontend, validation, authorization, failure states, accessibility/mobile behavior, critical tests, and production configuration are present.

### Phase 0 — Audit and architecture

- **Objectives:** Establish requirements, assumptions, blockers, architecture, domain/payment/booking/security boundaries, MVP scope, risks, and phase gates.
- **Files/modules:** `docs/IMPLEMENTATION_PLAN.md`; later split stable details into required architecture documents.
- **Database/API/frontend:** None.
- **Security:** Identify trust boundaries and launch blockers before code exists.
- **Tests:** Manual coverage/contradiction review against all sections of `prompt.md`.
- **Acceptance:** This document exists; every mandated planning topic is covered; fake features and unjustified infrastructure are excluded.
- **Dependencies:** None.

### Phase 1 — Project foundation

- **Objectives:** Scaffold Next.js 16 strict TypeScript/Tailwind and Django 6/DRF/PostgreSQL projects; establish formatting, linting, tests, OpenAPI, settings, logging, health, CI, and environment separation.
- **Files/modules:** root README/ignore/editor config; `frontend/*`; `backend/config`, `backend/apps/core`, initial custom user app; `.env.example`; CI workflow; initial docs.
- **Database:** Custom `User` in migration 0001; core timestamp/public-ID conventions. No SQLite production fallback.
- **API:** `/api/v1/health/` internal readiness and consistent error/correlation middleware; schema generation.
- **Frontend:** Root French layout, fonts/tokens, error/not-found/loading boundaries, typed API client skeleton.
- **Security:** Secure settings split, secret validation, allowed hosts/origins, cookie/CSRF baseline, security headers, redacted JSON logging, dependency pins.
- **Tests:** Django/DRF smoke tests, settings checks, frontend unit smoke, lint/typecheck/build, migration drift check.
- **Acceptance:** Clean checkout can install, migrate, test, lint, typecheck, and build using documented development config; production checks reject unsafe configuration.
- **Dependencies:** Phase 0.

### Phase 2 — Design system and public website

- **Objectives:** Build premium mobile-first accessible design system and all code-controlled public page structures with real empty-state behavior.
- **Files/modules:** frontend components/layout/navigation/footer; public routes for home, services, how-it-works, pricing, about, contact shell, FAQ shell, legal shells; content API clients.
- **Database:** Initial content/business-setting models needed for contact details, service descriptions, FAQs, testimonials, and legal document publication.
- **API:** Read-only published content/settings endpoints with caching/ETags; never return secrets/internal drafts.
- **Frontend:** Hero, quote entry shell linked to Phase 4/5 flow, trust/process/services sections, responsive navigation, accessible components, real-data testimonial omission when none exist.
- **Security:** Rich text sanitation/allow-list, safe external links, no invented reviews/legal claims, public cache controls.
- **Tests:** Component interaction/accessibility, responsive visual checks, content visibility rules, keyboard navigation.
- **Acceptance:** All visible links work; no placeholder action exists; pages meet contrast/keyboard/mobile standards and render sensible real empty states.
- **Dependencies:** Phase 1.

### Phase 3 — Accounts and authentication

- **Objectives:** Registration, verification, login/logout, password reset, profile update, staff groups, and secure session handling.
- **Files/modules:** backend accounts services/serializers/views/emails; frontend auth/account routes and forms.
- **Database:** Verification/reset token and consent records; user indexes/constraints.
- **API:** CSRF bootstrap, register, verify, session login/logout/current user, reset request/confirm, profile endpoints with anti-enumeration behavior.
- **Frontend:** Accessible validated forms and recovery states; no account requirement in booking.
- **Security:** Secure cookies, CSRF/origin validation, password policy/hashers, rate limits, token hashing/expiry/single use, session rotation, staff permission seeds.
- **Tests:** Authentication/authorization, enumeration resistance, rate limits, token reuse/expiry, CSRF, profile ownership, email failure handling.
- **Acceptance:** Customer and staff session journeys work end-to-end; unauthorized object access is rejected; emails use real configured delivery or explicit development console backend.
- **Dependencies:** Phase 1; Phase 2 components.

### Phase 4 — Airports, service areas, pricing, and content operations

- **Objectives:** Configurable coverage and deterministic fixed-zone quotes; operational editing through Django Admin initially and custom content screens where needed.
- **Files/modules:** backend locations/pricing/content; frontend airport/service-area/pricing routes and quote widget.
- **Database:** Airport, ServiceArea, BusinessSettings, Tariff, TariffOption, Quote/QuoteLine, content models and constraints/indexes.
- **API:** Published coverage/detail, quote create/retrieve, staff CRUD with permissions; quote expiry and stable calculation error codes.
- **Frontend:** Dynamic airport/area landing pages, authoritative estimation before personal data, coverage/manual-review/unavailable states.
- **Security:** Server-only price calculation, staff allow-lists/audit, quote public UUID and expiry, rate limits, no expensive unrestricted map key.
- **Tests:** Tariff selection, boundaries, rounding, capacity, inactive/expired rules, quote expiry, staff permissions, SEO route behavior.
- **Acceptance:** Admin-created airport/tariff appears without code change; quoted totals are reproducible and frontend manipulation cannot change them.
- **Dependencies:** Phases 1–3.

### Phase 5 — Booking engine

- **Objectives:** Mobile step flow, guest/customer booking conversion, immutable snapshots, status machine, guest access, cancellation policy evaluation, notes, and operational core.
- **Files/modules:** backend bookings domain services/API/admin; frontend booking steps, review, confirmation/pending, manage-booking views.
- **Database:** Booking/contact/address/price/policy snapshots, history, notes, guest token, idempotency and transition constraints/indexes.
- **API:** Create from quote, review/retrieve, guest token exchange/verification, controlled transition commands, eligible cancellation, repeat-booking-to-new-quote.
- **Frontend:** Trajet/Voyageur/Options/Paiement progression, back navigation without loss, review/consent, pending/failure/expired/conflict recovery, guest management.
- **Security:** Atomic conversion, idempotency, token digest/rotation, object permissions, policy snapshots, row locks, audit, PII-minimized responses.
- **Tests:** Guest/customer creation, manipulation, double submit, quote race/expiry, every allowed/forbidden transition, access isolation, cancellation boundaries, DST, mobile flow.
- **Acceptance:** A real persisted unpaid booking can be created once from a valid quote and securely managed; every status change is controlled and audited.
- **Dependencies:** Phases 3–4.

### Phase 6 — Stripe payments

- **Objectives:** Real Stripe test-mode Checkout, verified webhooks, reconciliation, full/partial refund commands, and payment recovery.
- **Files/modules:** backend payments common domain plus Stripe adapter/webhook/commands; frontend provider selection, redirect, pending/result UI; Stripe operations docs.
- **Database:** Payment, PaymentAttempt, Refund, WebhookEvent and provider uniqueness/idempotency indexes.
- **API:** Create Stripe checkout, status, raw-body webhook, staff reconcile/refund with explicit permissions.
- **Frontend:** Secure checkout handoff and server-confirmed status; cancel/failure/pending retry that cannot duplicate charges.
- **Security:** Signature/raw-body verification, exact amount/currency/metadata/environment validation, secret isolation, webhook throttling strategy, audit/redaction.
- **Tests:** Adapter contract, mocked signed webhook fixtures, duplicate/out-of-order events, mismatches, concurrent attempts, refund timeout/retry, Stripe test integration where credentials exist.
- **Acceptance:** Stripe test payment confirms exactly one booking only through verified backend evidence; refund state reconciles and all operations are auditable.
- **Dependencies:** Phase 5 and approved payment/cancellation rules for production.

### Phase 7 — PayPal payments

- **Objectives:** Independent PayPal sandbox order creation, server capture, webhook verification/reconciliation, and refunds.
- **Files/modules:** PayPal adapter/auth client/webhook; frontend PayPal UI loaded only when enabled; operations docs.
- **Database:** Reuse normalized payment tables with PayPal-specific identifiers/constraints; no lossy Stripe-shaped abstraction.
- **API:** Order create, idempotent capture, webhook, reconcile/refund.
- **Frontend:** Approval/cancel/window-close/pending/retry states; unavailable when configuration is incomplete.
- **Security:** Server credentials only, merchant/amount/currency/environment validation, verified webhooks, capture race control.
- **Tests:** Sandbox-contract mocks, duplicate capture/webhook, approval without capture, mismatches, refund/reversal, optional sandbox smoke.
- **Acceptance:** PayPal sandbox settles/refunds correctly and never confirms from browser approval alone; disabling PayPal removes all visible PayPal actions.
- **Dependencies:** Phase 6 common domain; PayPal business decision/credentials.

### Phase 8 — Customer dashboard and receipts

- **Objectives:** Upcoming/past lists, details, payment state, contact support, eligible cancellation, repeat booking, profile, and real provider/booking receipts.
- **Files/modules:** customer-scoped backend queries/serializers; frontend account routes; receipt rendering/download.
- **Database:** Optional receipt sequence/snapshot only after accounting decision; otherwise no new core entity.
- **API:** Customer-only paginated bookings/details/actions and protected receipt endpoint.
- **Frontend:** Responsive cards/detail timeline, clear empty states, cancellation confirmation, fresh-quote repeat flow.
- **Security:** Queryset/object ownership, no shared caching, safe PDF/HTML generation, re-auth/additional verification for sensitive actions.
- **Tests:** Cross-account access, list classification/timezones, cancellation race, receipt access/content, mobile/accessibility.
- **Acceptance:** Customers can manage only their own persisted bookings; guest booking remains equally functional without forced signup.
- **Dependencies:** Phases 5–7; invoice/VAT decision before tax invoice claims.

### Phase 9 — Operational admin dashboard and driver assignment

- **Objectives:** Real KPIs, filters/search/sort, booking detail/actions, manual booking, notes, driver/vehicle assignment, payment/refund views, content/settings operations, and responsive use.
- **Files/modules:** backend drivers/audit/reporting/admin APIs; frontend protected admin layout/dashboard/features.
- **Database:** Driver, Vehicle, Assignment, AuditEvent; reporting indexes; no denormalized KPI table until measurements require it.
- **API:** Permission-scoped staff endpoints and command actions; defined metric semantics/timezone; optimistic conflict responses.
- **Frontend:** Desktop/tablet tables and mobile cards/filter drawer; confirmation dialogs; histories; no fake KPI when data is empty.
- **Security:** Staff roles, least privilege, MFA/network gate, audit before/after, formula injection protection for future exports, conflict/override reasons.
- **Tests:** Role matrix, KPI correctness, filters, assignment collisions/capacity, manual price override audit, controlled transitions/refunds, responsive accessibility.
- **Acceptance:** Operations can execute each promised daily task against real records; every sensitive change is permitted, validated, and auditable.
- **Dependencies:** Phases 4–8.

### Phase 10 — Notifications and contact system

- **Objectives:** Persisted confirmation/status/reset email outcomes, resend/retry, contact form persistence/notification, and proportionate spam controls.
- **Files/modules:** backend notifications/contact/templates/management command; frontend contact and support interactions.
- **Database:** ContactMessage, Notification, NotificationAttempt and retention indexes.
- **API:** Contact submit, staff contact management, authorized notification resend; no public arbitrary recipient/template endpoint.
- **Frontend:** Validated contact form, honeypot/time trap, safe success/failure; WhatsApp tel/link actions from settings.
- **Security:** Header injection prevention, recipient allow-lists, rate limit, redacted logging, sanitized templates, optional Turnstile feature flag.
- **Tests:** Delivery success/failure/retry/idempotency, spam/rate limits, injection, permissions, transaction-commit timing.
- **Acceptance:** Required emails and contact messages are persisted, observable, and retryable; payment/booking success survives email failure.
- **Dependencies:** Booking/account events from Phases 3/5 and production SMTP decision.

### Phase 11 — PWA

- **Objectives:** Installable safe shell, platform-specific education, offline fallback, update behavior, and standalone testing.
- **Files/modules:** manifest, icons, service worker/build integration, install component, offline route.
- **Database/API:** None; explicit no-store headers on private API responses.
- **Frontend:** Android prompt and iOS instructions only when relevant; reduced motion and form-safe update prompt.
- **Security:** Static allow-list caching; no PII/API/payment cache; CSP-compatible worker.
- **Tests:** Manifest audit, cache inspection, offline fallback, Android/iOS/standalone responsive smoke, update during form.
- **Acceptance:** Supported browsers can install; iOS guidance is accurate; private booking data is absent from caches.
- **Dependencies:** Stable Phase 2 shell and Phase 5 routes.

### Phase 12 — SEO, analytics, and performance

- **Objectives:** Metadata/canonicals, sitemap/robots, valid structured data, local SEO, consent-aware conversion events, and measured performance budgets.
- **Files/modules:** Next metadata/sitemap/robots/JSON-LD; analytics consent adapter; performance config.
- **Database:** Optional consent proof/config fields already designed; no raw personal analytics store.
- **API:** Published SEO data and cache invalidation/revalidation hook secured for content changes.
- **Frontend:** Events for quote/booking/payment/contact milestones with allow-listed non-PII payloads.
- **Security:** Noindex/private cache controls, consent gating, CSP provider update, signed revalidation hook.
- **Tests:** Schema validation, sitemap active-only routes, canonical/hreflang, analytics PII schema rejection, Lighthouse/realistic mobile checks.
- **Acceptance:** Search artifacts contain only real public entities; analytics sends no PII and respects consent; agreed mobile budgets pass.
- **Dependencies:** Phases 2, 4, 5, 11 and provider decision.

### Phase 13 — Security and privacy hardening

- **Objectives:** Threat-model review, staff MFA/gate, headers/CSP, throttles, retention/anonymization commands, dependency/secrets checks, and penetration-style authorization review.
- **Files/modules:** security middleware/settings, retention commands, CI scanners, threat model and incident notes.
- **Database:** Retention markers/tombstones only where justified; audit immutability controls.
- **API/frontend:** Recheck every endpoint/action, security headers, safe errors, re-authentication, consent controls.
- **Security:** This phase validates rather than postpones controls already required in earlier phases.
- **Tests:** IDOR, CSRF, XSS, injection, brute force, token leakage/reuse, host/origin spoofing, cache exposure, webhook forgery, privilege escalation, dependency audit.
- **Acceptance:** No critical/high findings remain; medium findings have owners/rationale; production security check passes; legal review gaps are visibly documented.
- **Dependencies:** All feature phases and approved privacy/retention policies.

### Phase 14 — Full testing and release qualification

- **Objectives:** Complete critical backend/frontend/E2E suites, concurrency/failure coverage, accessibility/manual browser matrix, and staging payment journeys.
- **Files/modules:** backend tests, frontend tests, `e2e/`, fixtures/factories, CI matrices and runbooks.
- **Database/API/frontend:** Test fixtures only; production-like staging migrations and data seed procedure with fictional, labelled data.
- **Security:** Test logs/screenshots/traces redact secrets and personal data; test credentials cannot target live mode.
- **Tests:** Guest/customer booking, Stripe retries and ordering, admin confirm/assign, cancellation/refund, mobile, email failure, webhook races, backup restore, accessibility.
- **Acceptance:** All critical journeys pass in staging; no flaky release-blocking tests; unresolved defects are triaged and no incomplete feature is presented as done.
- **Dependencies:** Phases 1–13.

### Phase 15 — Production deployment

- **Objectives:** Provision without Docker, configure services/TLS/firewall/backups/logging/monitoring, deploy with rollback, and document operations.
- **Files/modules:** `deploy/` Nginx/systemd templates, deployment/backup/environment/operations docs, scripts with safe preflight.
- **Database:** Production PostgreSQL roles/database, migrations, indexes, backup/restore validation.
- **API/frontend:** Canonical domains, proxy routes, secure cookies/origins, production builds, health checks.
- **Security:** Least-privilege users/files, secret delivery, SSH/firewall, TLS/HSTS staged rollout, local-only DB, test/live credential assertions.
- **Tests:** Config validation, smoke tests, webhook endpoint registration, payment low-value/test-to-live checklist, email/DNS, backup and rollback rehearsal.
- **Acceptance:** Reproducible deployment and rollback succeed; monitoring/backups are green; production secrets are absent from repository/logs/client bundles.
- **Dependencies:** Phase 14 and all launch blockers resolved for enabled features.

### Phase 16 — Post-deployment validation

- **Objectives:** Validate production journeys, observability, indexing controls, operational training, and incident/payment reconciliation procedures.
- **Files/modules:** launch checklist, operational handover, architecture/docs updated to actual deployment.
- **Database/API/frontend:** Verify real configuration/content and metrics definitions; no test data presented as real.
- **Security:** External header/TLS checks, permissions audit, log/redaction review, backup off-host verification.
- **Tests:** Controlled real-provider transaction/refund, guest/account/admin journeys, email, install, mobile browsers, webhook retry, restore evidence.
- **Acceptance:** Business owner signs off policies/content/prices; real booking/payment/refund can be reconciled; known limitations are documented; monitoring and support ownership are active.
- **Dependencies:** Phase 15.

## 14. Required documentation map

During Phases 1–15 this plan is decomposed into documentation that reflects actual code:

- `README.md`: development setup and verified commands.
- `docs/ARCHITECTURE.md`: runtime/component decisions and ADR links.
- `docs/DOMAIN_MODEL.md`: implemented entities, constraints, and diagrams.
- `docs/BOOKING_FLOW.md`: implemented transitions, actors, and recovery.
- `docs/PAYMENT_ARCHITECTURE.md`: provider flows, reconciliation, and operational procedures.
- `docs/SECURITY.md`: threat model, controls, incident response, and limitations.
- `docs/DEPLOYMENT.md`: Ubuntu provisioning, release, rollback, TLS/firewall.
- `docs/ENVIRONMENT_VARIABLES.md`: every variable, owner, environment, safe examples.
- `docs/BACKUP_AND_RESTORE.md`: schedule, retention, encryption, restore drills.
- `docs/OPERATIONS.md`: booking/payment/email/webhook/admin runbooks.

## 15. Phase 0 consistency and coverage review

- **No fake features:** Testimonials, live flight status, PayPal, analytics, maps, legal claims, and accessibility capabilities render only when real content/configuration exists. Future items have no active controls.
- **No client authority:** Prices, transitions, access, cancellation/refunds, payment success, and provider environment are server-owned.
- **No payment/booking state contradiction:** Payment processing is separate from operational booking status; only verified settlement or an explicitly enabled staff-controlled offline mode confirms a booking.
- **No premature infrastructure:** PostgreSQL is required; Redis/Celery, live flight, maps, and dispatch optimization are excluded until justified.
- **Guest/account parity:** Guest booking is complete and secure; accounts add convenience but are not required.
- **Historical integrity:** Address, contacts, price, tax/policy, and relevant service details are snapshotted; future configuration changes do not rewrite history.
- **Operational reality:** KPIs use database facts, emails have observable failures, payment redirects are pending until verified, and admin actions use controlled commands.
- **Requirement coverage:** Public site, dynamic coverage, booking, accounts, guest access, Stripe, PayPal, refunds, drivers, operational admin, notifications, PWA, SEO/local SEO, analytics/privacy, accessibility, performance, security, testing, backups, observability, and no-Docker deployment each have an owning phase.
- **Unresolved policy honesty:** Legal, VAT, cancellation, operating coverage/capacity, provider credentials, and accessibility claims are explicit launch blockers and are not silently invented.

Phase 0 is complete when this review remains true after stakeholder feedback. Phase 1 may begin using the provisional defaults, but no affected production feature may launch until its listed business blocker is resolved and documented.
