# Marketplace alignment plan

Status: implementation contract for `feature/marketplace-alignment`  
Decision date: 2026-07-15  
Product decision: AirProche is an independent professional airport-transfer driver directory and lead marketplace.

## 1. Current architecture

The repository is a modular monolith. Next.js renders public, account, driver, and staff experiences. Django REST Framework owns authentication, authorization, persistence, validation, notification orchestration, privacy commands, and staff administration. PostgreSQL is the production system of record. Email is sent through the existing database-backed notification/delivery-attempt architecture; Redis and Celery are intentionally absent.

Two domain paths currently coexist:

1. The original managed-transfer path: tariff quotes, `Booking`, Stripe checkout, refunds, receipts, internal `Driver`/`Vehicle` assignment, customer booking management, and operations reporting.
2. The emerging marketplace path: `MarketplaceDriverProfile`, a public UUID directory, and a minimal `DriverInquiry` record.

Only the marketplace path will remain publicly active. Historical managed-booking records and provider reconciliation code must remain readable and operable by authorized staff until a separate, approved data migration or retention decision permits removal.

## 2. Conflict disposition

| Area | Current conflict | Decision |
| --- | --- | --- |
| Homepage and shared marketing data | Mixes server-priced booking claims with direct-driver contact | Replace with marketplace discovery, trust, and non-binding inquiry language. |
| `/tarifs` | Creates authoritative AirProche quotes | Deprecate publicly, remove from navigation/sitemap, add `noindex`, and present directory migration guidance. |
| `/reservation`, `/reservation/gerer` | Creates/manages AirProche bookings | Deprecate publicly with `noindex`; retain code and historical APIs for staff/data compatibility, but prevent new public booking creation. |
| `/paiement/retour` and payment checkout | Suggest AirProche collects transport fares | Remove public CTA and `noindex` return route. Disable new customer trip checkout at the backend with a marketplace-mode setting. Retain webhook/reconciliation models for historical records. |
| `/compte` | Mixes account/profile and booking dashboard | Convert to marketplace driver/customer account hub; remove active booking actions. Historical booking access remains staff-only. |
| `/operations` | Managed dispatch and assignment | Remove from public navigation and replace its primary staff purpose with marketplace moderation. Retain historical assignment data and restricted legacy views during deprecation. Fix its request race while it exists. |
| Airport/service-area pages | Built around tariff-backed coverage | Migrate discovery to published chauffeur coverage. Do not create thin pages without published drivers. |
| Testimonials | General business testimonials can look like driver reviews | Keep general testimonials clearly separate. Add profile reviews only through an inquiry-linked, moderated workflow. |
| Stripe/PayPal | Transport-fare collection conflicts with marketplace | No public trip-payment flow. PayPal remains absent. Preserve Stripe historical reconciliation only. Future platform monetization is a separate ADR decision. |
| Documentation and legal content | Describes AirProche as transport provider | Rewrite architecture/product docs and publish marketplace legal seed content marked for professional review. |

## 3. Target domain model

### Driver identity and profile

`MarketplaceDriverProfile` remains the aggregate root and is owned one-to-one by an authenticated user. It receives a collision-resistant public slug, explicit workflow state, separate verification/publication timestamps, identity/business fields, professional credentials, public contact controls, languages, operating directions, commercial notes, response expectation, experience, and profile-completion data.

Vehicle details belong to a marketplace-owned `MarketplaceVehicle` linked to the profile. The legacy internal `Driver`, `Vehicle`, and `DriverAssignment` models remain historical-only and are not used by new marketplace inquiries.

### Coverage

Published profiles must have at least one active airport. Many-to-many airport and service-area relations remain authoritative. Every inquiry has exactly one supported direction:

- `AIRPORT_TO_DESTINATION`
- `DESTINATION_TO_AIRPORT`

The selected airport represents one endpoint and a normalized non-airport origin/destination represents the other. Backend validation rejects general point-to-point work.

### Inquiry lifecycle

`DriverInquiry` receives a random reference, lifecycle status, customer contact preferences, direction, luggage and accessibility needs, consent proof, abuse metadata, notification summary, and anonymization timestamp. Controlled transitions are:

- `NEW -> NOTIFIED`
- `NEW|NOTIFIED -> VIEWED`
- `VIEWED|NOTIFIED -> CONTACTED`
- `CONTACTED -> ACCEPTED|DECLINED`
- `ACCEPTED|DECLINED -> CLOSED`
- `CLOSED -> ARCHIVED`
- any non-archived operational state may become `SPAM`

`InquiryStatusHistory` records actor, timestamp, safe notes, and the transition. `InquiryNote` separates internal and customer-visible notes. No state implies a completed transport contract or guaranteed fare.

### Consent, delivery, verification, reviews, and abuse

- `InquiryConsent` stores immutable privacy-policy/version references, text version, timestamp, source, allowed contact channels, and necessary request metadata.
- `MarketplaceNotification` stores idempotent delivery state, redacted target, attempts, retry timing, provider identifier, and safe failure classification. It does not store credentials or full email bodies.
- `DriverVerificationDocument` uses private media storage, generated filenames, allow-listed MIME/extensions, size limits, expiration, review state, and staff-authorized download.
- `DriverVerificationEvent` records workflow decisions and reasons.
- `MarketplaceReview` requires an eligible inquiry, one review per relationship, moderation, and publication. No aggregate rating is exposed until real published reviews exist.
- `MarketplaceAbuseReport` records minimally necessary reports and moderation decisions.
- Existing generic `AuditEvent` is extended/reused for safe marketplace audit summaries without document content or excessive customer data.

## 4. Migration strategy

Migrations are additive first:

1. Add nullable/defaulted marketplace fields and new related tables.
2. Generate unique slugs for existing profiles from display/business names plus a random collision suffix when required.
3. Map legacy marketplace statuses (`draft`, `pending`, `verified`, `rejected`) into the new workflow without self-publishing or deleting profiles.
4. Map existing inquiries (`new`, `contacted`, `closed`) into the controlled lifecycle and create initial history records where safe.
5. Keep legacy booking/payment/assignment tables intact and mark their creation endpoints inactive in marketplace mode.

No historical booking, payment, profile, or inquiry row is destructively deleted by schema migration. Retention/anonymization remains an explicit audited operational command.

## 5. Route strategy

### Active public routes

- `/` marketplace homepage
- `/chauffeurs` searchable directory
- `/chauffeurs/[slug]` standalone, profile-focused public experience
- `/aeroports` and `/aeroports/[slug]` only for airports with published drivers
- `/zones-desservies` and meaningful service-area pages backed by published drivers
- `/fonctionnement`, `/services`, `/securite`, `/devenir-chauffeur`, legal and privacy pages

### Private routes

- `/compte` account and chauffeur workspace
- driver profile/onboarding, inquiries, verification documents, and preview under the authenticated account experience
- `/operations` retained as a noindex staff-only legacy surface until marketplace moderation supersedes it
- Django Admin and permission-scoped staff APIs for moderation and observability

### Deprecated routes

`/tarifs`, `/reservation`, `/reservation/gerer`, and `/paiement/retour` are removed from navigation and sitemap, marked `noindex`, and show an accurate marketplace migration message. New booking and trip-checkout mutations return an explicit deprecation error when marketplace mode is enabled. Historical records remain accessible only through authorized operational paths.

UUID detail routes receive slug compatibility redirects where safe. Public profile lookup is slug-based and never exposes sequential IDs.

## 6. Privacy strategy

- Necessary inquiry consent is explicit, versioned, and separate from future marketing consent.
- Inquiry payloads and logs are minimized; analytics never contain names, contact details, messages, private addresses, or document information.
- Retention periods are configurable, not presented as absolute legal advice. Closed/declined inquiries, spam, notification data, audit metadata, and verification evidence have separate settings.
- Retention performs dry-run reporting before explicit `--apply`, anonymizes customer fields while preserving minimal operational/audit facts, and records the privacy action.
- Account anonymization handles marketplace profile identity/contact/credential data, private documents, notes, notifications, reviews, and linked inquiries without breaking protected relationships.
- Public contact fields are emitted only when the chauffeur enabled the corresponding visibility control.

## 7. Notification strategy

Inquiry creation commits the inquiry and delivery records atomically, then attempts delivery after transaction commit. The customer receives an accurate acknowledgement and the chauffeur receives a new-inquiry notice. Database records remain the source of truth even when SMTP fails.

Delivery states are `PENDING`, `SENT`, `FAILED`, `RETRYING`, and `PERMANENT_FAILURE`. Each delivery has an idempotency key, bounded attempts, `next_attempt_at`, redacted target, safe error category, and timestamps. A management command and permission-scoped staff action retry eligible failures. Permanent failures appear in staff/driver observability. The submission response distinguishes inquiry persistence from email delivery.

Status notifications are allow-listed and use predefined templates. Free-text customer-visible notes require an explicit chauffeur action and are not automatically emailed without confirmation.

## 8. Abuse and security strategy

- CSRF and Origin enforcement remain mandatory for browser mutations.
- Shared database throttling applies by IP/account plus a per-profile recipient limit.
- Honeypot, minimum form age with an accessible lower bound, normalized input, control/header injection rejection, length limits, idempotency keys, and duplicate fingerprints are enforced server-side.
- Driver endpoints always scope queries through `request.user`; staff workflows require model permissions; document downloads authorize every request.
- Workflow serializers use explicit field allow-lists and controlled transition services.
- Private uploads use generated names, size/MIME/extension validation, no executable types, private response headers, and a malware-scanner integration state. Unscanned/failed documents cannot be approved.
- Security logs contain correlation IDs and safe object references, never inquiry messages, contact details, document bytes, or secrets.

## 9. Profile-sharing architecture

The canonical profile URL is `/chauffeurs/<unique-slug>`. The page uses a reduced chauffeur-first shell while retaining an AirProche verified-profile mark, marketplace safety context, discovery link, and legal/privacy links. Metadata, Open Graph, structured data, and canonical URL derive only from published public fields.

The driver workspace displays publication/verification/completion states and provides preview, open, copy, Web Share, and a locally generated QR representation. Sharing events contain only a non-personal public profile identifier. Unpublished previews require authentication and ownership/staff authorization and are `noindex`.

## 10. Discovery, SEO, analytics, accessibility, and UI

The directory supports airport, service area, direction, passengers, luggage, language, vehicle category, accessibility, child seat, verified state, sort, and paginated results. Availability is described as requiring direct confirmation unless the chauffeur supplies a non-real-time note.

Only published, discoverable profiles and coverage pages with meaningful real content enter the sitemap. Private, deprecated, incomplete, and unpublished routes are `noindex`. Ratings and `AggregateRating` are emitted only from eligible moderated reviews.

Marketplace analytics remain consent-gated and schema allow-listed. Events use coarse non-personal dimensions and public random identifiers only. WCAG-oriented forms use labels, descriptions, associated field errors, focus management, status announcements, keyboard-safe dialogs, visible focus, reduced motion, and mobile-first layouts down to 320px.

## 11. Testing plan

Backend coverage will include airport-only validation, consent/version integrity, anti-abuse controls, idempotency/duplicates, lifecycle transitions, ownership/IDOR, publication and slug access, directory filters/pagination, notification creation/retry/failure, audit events, private upload authorization/validation, retention, and account anonymization.

Frontend coverage will include directory filters, profile rendering/sharing, inquiry validation and acknowledgement, field-error mapping, onboarding/coverage selection, inbox filters/actions, localized states, loading/error/empty states, and the operations filter race.

Playwright will cover the public search/profile/inquiry path, duplicate prevention, authenticated driver inbox/status/profile changes, unauthorized access, staff publication where a safe fixture is available, unpublished denial, and mobile profile/inquiry behavior. Obsolete public trip-payment assumptions will be removed.

Release qualification includes Django checks/migrations/tests, PostgreSQL rehearsal, Ruff, frontend lint/type/unit/build/Playwright, dependency and secret scans, encoding/broken-link checks, accessibility budgets, sitemap/robots/structured-data review, and explicit credential-dependent staging checks.

## 12. Implementation phases

1. Add the target domain and non-destructive migrations.
2. Enforce security, permissions, consent, abuse controls, retention, and anonymization.
3. Implement inquiry delivery, retry, observability, and status notifications.
4. Complete onboarding, coverage, vehicle, credentials, media, and verification.
5. Build the driver workspace, inquiry inbox, sharing, and profile preview.
6. Build public discovery and the standalone profile experience.
7. Deactivate managed-booking/payment entry points and align all public content/legal claims.
8. Fix form validation, operations races, localized states, encoding, component structure, loading, and dialogs.
9. Complete SEO, analytics, accessibility, PWA, and responsive behavior.
10. Add lifecycle/security/privacy tests, update documentation, and run release qualification.

## 13. Risks and safeguards

- **Legal classification:** marketplace/intermediary wording is an engineering default and remains subject to professional legal review.
- **Document storage:** local private media is acceptable for this deployment topology only with filesystem permissions, encrypted backups, and authorized Django delivery; object storage requires a later reviewed adapter.
- **Malware scanning:** approval is blocked unless the configured scanner reports clean. Production activation requires an actual scanner command/service and staging validation.
- **Email credentials:** implementation and console/test delivery can be qualified locally; real SMTP delivery cannot be claimed without staging credentials.
- **Historical data:** managed-booking/payment code is deactivated, not destructively removed. A later retention/migration decision owns deletion.
- **Scope pressure:** release acceptance prioritizes a secure complete inquiry lifecycle, ownership, privacy, discovery, and honest public claims over speculative monetization or real-time availability.

## 14. Acceptance criteria

The implementation is acceptable when the public product exposes only the independent-driver airport-transfer marketplace; published profiles are discoverable and shareable by slug; every inquiry involves an active airport and records consent; persistence and delivery state are honest; customer and chauffeur emails are observable/retryable; drivers have an authorized inbox with controlled audited transitions; onboarding, verification, private documents, coverage, vehicle data, and publication are controlled; marketplace data participates in retention/anonymization; public trip-payment/booking creation is disabled and absent from discovery; state labels and French copy are polished; critical backend/frontend/browser tests pass; and credential-dependent staging work is reported rather than fabricated.

## 15. Contradiction review

This plan deliberately separates three concepts that were previously conflated:

- An **inquiry** is a lead recorded and transmitted by AirProche, never a booking.
- A chauffeur's **acceptance state** records intent inside AirProche, not proof of a finalized fare or transport contract.
- A **published/verified profile** means AirProche completed the documented verification scope; it is not a guarantee of availability, trip performance, or fare.

No active design in this plan requires AirProche to assign a driver, calculate a fare, collect the transport payment, issue a fare receipt, or promise a completed ride.
