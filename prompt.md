You are a Principal Software Architect, Senior Full-Stack Engineer, Senior Product Designer, UX/UI Expert, Security Engineer, Payment Integration Specialist, SEO Specialist, PWA Engineer, QA Engineer, and DevOps Engineer.

I need you to design and build a complete, production-ready web platform for a private airport pickup and transport service in France.

This is NOT a simple landing page.

The platform must combine:

1. A professional SEO-optimized marketing website
2. An online transport booking system
3. Customer accounts
4. Guest booking
5. Online payments
6. Stripe integration
7. PayPal integration
8. Booking management
9. Admin dashboard
10. Driver/transport assignment architecture
11. Notifications
12. PWA installation
13. Mobile-first responsive UX
14. Secure backend
15. Production deployment architecture
16. Analytics and operational reporting

The initial business concept is based on the following service:

A private transport service that helps customers arrange airport pickup for themselves, relatives, friends, or other passengers.

Typical service:

- Passenger arrives at an airport in France.
- The customer books the transport online.
- The driver or service provider receives the booking.
- The passenger is welcomed at the airport.
- The driver can assist with luggage.
- The passenger is transported safely to their home, hotel, accommodation, train station, or another destination.
- The service should communicate reliability, security, punctuality, comfort, professionalism, and trust.

Initial airports may include:

- Paris Charles de Gaulle Airport
- Paris Orly Airport
- Paris Beauvais Airport

However, airports must NOT be hardcoded into the application.

The admin must be able to create, edit, activate, deactivate, and manage airports and service zones.

The architecture must support future expansion to other cities, airports, countries, and multiple drivers.

==================================================
1. NON-NEGOTIABLE ENGINEERING RULES
==================================================

Build this as a serious production application.

DO NOT:

- create fake implementations
- create placeholder buttons
- create non-functional forms
- create dead links
- add TODO comments instead of implementing features
- use mock payment success in production flows
- hardcode secrets
- expose secret API keys in the frontend
- trust prices sent by the frontend
- trust payment success reported by the frontend
- trust booking data without backend validation
- create duplicate business logic between frontend and backend
- implement unnecessary microservices
- overengineer the MVP
- use Docker
- leave incomplete features represented as completed
- silently swallow errors
- build a visually attractive application with a weak backend
- build an admin dashboard with fake KPIs
- create buttons that do nothing

Every visible production feature must work end-to-end.

If a feature should not be implemented yet:

- do not pretend it exists
- clearly identify it as a future feature
- keep the architecture extensible for it

Before modifying or creating code:

1. analyze the project
2. create an architecture plan
3. define the domain model
4. identify security boundaries
5. define the payment lifecycle
6. define the booking lifecycle
7. create an implementation plan by phases
8. then implement systematically

==================================================
2. REQUIRED TECHNOLOGY STACK
==================================================

Use the following stack unless a very strong technical reason requires a change.

FRONTEND

- Next.js 16
- App Router
- TypeScript with strict mode
- React
- Tailwind CSS
- accessible reusable component architecture
- React Hook Form where appropriate
- Zod for frontend form validation
- TanStack Query only where client-side server-state management genuinely adds value
- server components by default
- client components only where necessary

BACKEND

- Python
- Django 6
- Django REST Framework
- PostgreSQL
- Django Admin for low-level operational administration
- custom business admin dashboard for normal daily operations

OPTIONAL INFRASTRUCTURE

Use only when actually necessary:

- Redis
- Celery
- Celery Beat

Possible use cases:

- asynchronous emails
- payment reconciliation
- scheduled reminders
- abandoned booking cleanup
- scheduled operational tasks
- notification delivery

Do not introduce Redis or Celery simply because they are popular.

PAYMENTS

Primary:

- Stripe

Alternative:

- PayPal

Stripe should be the primary payment architecture.

Use:

- Stripe Checkout or Payment Element depending on the final UX decision
- backend-created payment sessions/intents
- Stripe webhooks
- idempotent webhook processing
- server-side amount calculation
- payment reconciliation

PayPal:

- PayPal Checkout
- backend order creation
- backend capture/verification
- PayPal webhook processing where required
- idempotent processing

DATABASE

- PostgreSQL

PRODUCTION DEPLOYMENT

No Docker.

Target:

Ubuntu VPS

Use:

- Nginx
- HTTPS
- Let's Encrypt
- systemd services
- PostgreSQL
- Python virtual environment
- Node.js production process for Next.js
- Gunicorn or an appropriate production Django application server
- secure environment files
- separate frontend and backend services

Suggested deployment structure:

/home/<user>/<project>/
    frontend/
    backend/
    storage/
    backups/
    logs/
    scripts/
    docs/

Do not blindly create this structure if an existing repository structure already exists.

==================================================
3. PRODUCT VISION
==================================================

The product should make booking private airport transport extremely easy.

A customer should be able to arrive on the website and understand within seconds:

- what the service does
- where the service operates
- why the service is trustworthy
- how much the trip may cost
- how to book
- what happens after booking
- how the passenger will be identified
- how payment works
- how to contact the service

The experience must especially work well for:

- mobile users
- diaspora communities booking transport for relatives
- customers who may not be technically experienced
- users booking for another person
- users arriving from abroad
- customers using WhatsApp frequently

The UX must reduce anxiety.

Important trust signals:

- clear service explanation
- professional driver/service provider information
- secure payments
- clear booking confirmation
- transparent pricing
- contact information
- cancellation policy
- privacy policy
- terms and conditions
- service coverage
- airport pickup explanation
- luggage assistance information
- passenger contact process

==================================================
4. BRAND AND VISUAL DIRECTION
==================================================

The current visual identity uses:

- dark navy blue
- bright royal blue
- white
- strong typography
- transport and airport imagery
- trust and safety messaging

Keep the recognizable blue identity but redesign it into a modern premium digital experience.

The new interface must NOT look like:

- a generic Bootstrap template
- an outdated taxi website
- a cheap marketplace
- an AI-generated template
- a cluttered admin interface

Design direction:

- modern
- premium
- trustworthy
- clean
- accessible
- professional
- mobile-first
- warm enough to feel personal
- strong but not visually aggressive

Use:

- large readable typography
- strong whitespace
- clear visual hierarchy
- subtle borders
- refined shadows
- consistent border radii
- accessible color contrast
- polished interactive states
- meaningful icons
- high-quality transport/airport imagery

Avoid excessive:

- gradients
- glassmorphism
- animations
- giant cards
- excessive rounded containers
- visual noise

Animations should be subtle and functional.

Respect:

prefers-reduced-motion

==================================================
5. PUBLIC WEBSITE
==================================================

Create the following public pages.

HOME PAGE

The homepage should contain:

1. Hero section

Example message:

“Votre chauffeur privé pour vos transferts aéroport”

Supporting message:

“Réservez un accueil personnalisé et un transport sécurisé depuis les principaux aéroports.”

Primary CTA:

“Réserver un trajet”

Secondary CTA:

“Obtenir une estimation”

Optional CTA:

“Nous contacter sur WhatsApp”

2. Booking/quote widget

Allow users to quickly enter:

- pickup location
- destination
- date
- approximate time
- number of passengers

3. How it works

Example:

1. Réservez
2. Recevez votre confirmation
3. Nous accueillons le passager
4. Voyagez sereinement

4. Services

Examples:

- airport pickup
- airport drop-off
- luggage assistance
- transport to home
- transport to hotel
- transport for relatives
- long-distance transfer

5. Airport coverage

Dynamic from the backend.

6. Why choose us

- punctuality
- secure transport
- luggage assistance
- communication
- personal service
- availability

7. Customer reviews

Real reviews only.

Admin must be able to manage testimonials.

8. FAQ

9. Final booking CTA

10. Contact information

==================================================
6. ADDITIONAL PUBLIC PAGES
==================================================

Create:

- Services
- Airports
- individual airport SEO landing pages
- Service areas
- How it works
- Pricing / Fare information
- About
- FAQ
- Contact
- Booking
- Booking confirmation
- Track/manage booking
- Login
- Register
- Forgot password
- Reset password
- Privacy Policy
- Terms and Conditions
- Cancellation Policy
- Legal Notice / Mentions légales
- Cookie policy when applicable

Possible SEO pages:

/aeroports/charles-de-gaulle
/aeroports/orly
/aeroports/beauvais

But URLs and entities must be dynamically manageable.

==================================================
7. BOOKING ENGINE
==================================================

Build a complete booking workflow.

STEP 1 — TRIP

Fields:

- booking type
    - airport pickup
    - airport drop-off
    - point-to-point transport

- pickup location
- destination
- pickup date
- pickup time
- airport when applicable
- flight number when applicable
- airline optional
- origin city/country optional

For airport arrivals:

support:

- flight number
- scheduled arrival time
- terminal
- passenger meeting information

Do not initially build an expensive live flight integration unless configured.

Design the data model so live flight tracking can be added later.

STEP 2 — PASSENGERS

- passenger count
- adult count where useful
- child count where useful
- luggage count
- oversized luggage
- wheelchair/accessibility request
- child seat request
- additional requirements
- notes

STEP 3 — CONTACT INFORMATION

The person booking may be different from the passenger.

BOOKER:

- first name
- last name
- email
- phone
- WhatsApp phone if different

PASSENGER:

- same as booker toggle

Otherwise:

- passenger first name
- passenger last name
- passenger phone
- passenger WhatsApp
- preferred language

This is important because many users will book for relatives or friends.

STEP 4 — PRICE

The backend calculates the price.

Never allow the browser to determine the authoritative payable amount.

Pricing architecture should support:

- fixed airport zones
- base fare
- distance-based fare
- time-based modifiers
- airport surcharge
- night surcharge
- waiting time
- additional stops
- passenger/luggage modifiers
- child seats
- manual custom quote
- promotional discount
- administrator adjustment

For MVP:

choose the simplest reliable pricing model based on the business requirements.

Do not build unnecessary dynamic pricing complexity.

Store a price snapshot on the booking.

A historical booking price must not change when future tariff rules change.

STEP 5 — REVIEW

Show:

- route
- date
- time
- airport
- flight
- passenger
- luggage
- services
- total amount
- cancellation conditions
- payment method

STEP 6 — PAYMENT

Allow:

- Stripe
- PayPal

Architecture should optionally support:

- pay online in full
- deposit
- pay later

However, activate only the payment modes configured by the admin.

STEP 7 — CONFIRMATION

After verified payment or confirmed payment condition:

show:

- booking reference
- booking summary
- payment status
- next steps
- contact information
- manage booking link

Send confirmation email.

==================================================
8. BOOKING STATES
==================================================

Use an explicit booking state machine or controlled transition logic.

Example states:

DRAFT
PENDING_PAYMENT
PAYMENT_PROCESSING
CONFIRMED
DRIVER_ASSIGNMENT_PENDING
DRIVER_ASSIGNED
PASSENGER_CONTACTED
DRIVER_EN_ROUTE
DRIVER_ARRIVED
PASSENGER_PICKED_UP
IN_PROGRESS
COMPLETED
CANCELLED
NO_SHOW

Do not allow arbitrary status transitions.

Define:

- allowed transitions
- actor allowed to perform each transition
- timestamp of each transition
- optional status notes

Keep:

BookingStatusHistory

Every operational status change should be auditable.

==================================================
9. CUSTOMER ACCOUNT
==================================================

Customers should be able to:

- register
- log in
- log out
- verify email
- reset password
- view upcoming bookings
- view past bookings
- view booking details
- download receipts/invoices when applicable
- update contact details
- cancel eligible bookings
- view payment status
- repeat a previous booking
- contact support

Guest checkout must also be supported.

Do not force account creation before booking.

After guest booking, optionally allow:

“Créer mon compte pour gérer mes réservations”

==================================================
10. BOOKING MANAGEMENT WITHOUT LOGIN
==================================================

A guest customer should be able to access a booking securely through a protected booking-management mechanism.

Do not expose bookings through predictable IDs.

Possible secure architecture:

- cryptographically secure management token
- limited expiration where appropriate
- token rotation
- sensitive actions require additional verification

Never expose another customer's booking through ID enumeration.

==================================================
11. ADMIN DASHBOARD
==================================================

Create a proper operational admin interface.

Do not rely exclusively on Django Admin for normal daily operations.

Dashboard:

- bookings today
- upcoming pickups
- pending payments
- unassigned bookings
- confirmed bookings
- completed trips
- cancellations
- revenue
- bookings by airport
- booking trend

Only show metrics computed from real database records.

BOOKING MANAGEMENT

Admin can:

- search bookings
- filter bookings
- sort bookings
- open booking details
- create bookings manually
- edit eligible booking data
- change status through controlled transitions
- record internal notes
- record customer-visible notes
- assign driver
- view payment
- resend confirmation
- cancel booking
- refund where permitted
- see status history
- see communication history

Filters:

- date
- booking status
- payment status
- airport
- driver
- customer
- booking reference

==================================================
12. DRIVER ARCHITECTURE
==================================================

Prepare for multiple drivers even if the initial business has only one driver.

Driver fields:

- first name
- last name
- phone
- email
- active status
- profile image optional
- vehicle
- service areas
- notes

Vehicles:

- make
- model
- registration
- passenger capacity
- luggage capacity
- active status

Admin should be able to assign a driver to a booking.

Do not overbuild a full Uber-like dispatch system.

Future driver application architecture can be prepared, but the MVP should focus on simple admin assignment.

==================================================
13. AIRPORTS AND SERVICE ZONES
==================================================

Create configurable entities.

Airport:

- name
- IATA code
- slug
- city
- country
- address
- latitude
- longitude
- terminals where needed
- active status
- description
- SEO metadata

ServiceArea:

- name
- type
- city/region/postal zone
- pricing configuration
- active status

Do not hardcode airport lists into frontend components.

==================================================
14. PAYMENTS — STRIPE
==================================================

Implement Stripe correctly.

The backend must:

1. calculate authoritative amount
2. create payment session or intent
3. attach internal booking reference through metadata
4. persist provider identifiers
5. process webhooks
6. verify webhook signature
7. use idempotency protection
8. update payment status
9. update booking only after valid server-side payment confirmation

Never:

- trust a frontend success redirect as proof of payment
- expose Stripe secret keys
- allow the browser to submit an arbitrary authoritative amount

Payment model should include:

- provider
- provider payment ID
- booking
- amount
- currency
- status
- created date
- updated date
- failure information
- refund amount
- metadata where appropriate

Payment statuses:

PENDING
PROCESSING
SUCCEEDED
FAILED
CANCELLED
PARTIALLY_REFUNDED
REFUNDED

Implement webhook event deduplication.

Store processed webhook event IDs.

==================================================
15. PAYMENTS — PAYPAL
==================================================

Implement PayPal as an independent payment provider.

Do not attempt to force PayPal into Stripe abstractions that create bad domain logic.

The backend must:

- create PayPal orders
- associate the order with the booking
- verify amount server-side
- capture/verify payment server-side
- process relevant webhook events
- prevent duplicate processing
- maintain normalized internal payment state

Frontend PayPal success alone is not sufficient proof of payment.

==================================================
16. PAYMENT ABSTRACTION
==================================================

Create a clean internal payment service interface.

Example conceptual operations:

create_payment()
confirm_payment()
process_webhook()
refund_payment()
get_payment_status()

But avoid unnecessary enterprise patterns.

The domain model should expose a normalized internal payment state while preserving provider-specific identifiers and responses where operationally necessary.

==================================================
17. REFUNDS AND CANCELLATIONS
==================================================

Create a clear cancellation architecture.

Configuration may include:

- free cancellation before a deadline
- partial refund
- no refund after a deadline
- admin override

Do not hardcode a policy without business confirmation.

The admin should be able to configure or manage the applicable cancellation policy.

Refunds must:

- be initiated server-side
- be recorded
- never exceed captured amount
- support partial refund where the provider allows it
- update internal payment state
- create an audit trail

==================================================
18. EMAILS AND NOTIFICATIONS
==================================================

Implement transactional email architecture.

Events:

- booking received
- payment successful
- booking confirmed
- booking modified
- driver assigned
- upcoming trip reminder
- cancellation
- refund
- password reset
- email verification

Use proper HTML and plain-text email alternatives.

Never send sensitive secrets in email.

Design notification architecture so these can later be added:

- SMS
- WhatsApp Business API
- push notifications

Do not implement unofficial WhatsApp automation.

==================================================
19. WHATSAPP
==================================================

WhatsApp is important for this target audience.

Public pages can include:

- WhatsApp contact CTA

Booking confirmation can include:

- contact via WhatsApp

Use a properly formatted WhatsApp deep link.

Do not expose sensitive booking information in URL parameters.

Future architecture may support:

- WhatsApp Business Platform notifications

But do not implement unofficial bots or browser automation.

==================================================
20. PWA
==================================================

The website must function as a Progressive Web App.

Implement:

- web app manifest
- app name
- short name
- icons
- Apple touch icon
- theme color
- background color
- standalone display mode
- service worker where justified
- offline fallback
- installability
- safe update strategy

The booking system must never depend on stale cached transactional data.

Do not aggressively cache:

- authenticated customer data
- admin data
- payment state
- current booking status
- sensitive API responses

Cache only safe static/public assets appropriately.

==================================================
21. PWA INSTALL EXPERIENCE
==================================================

Create a custom installation UX.

ANDROID

When the browser supports the install prompt:

- capture the appropriate install event
- present a non-intrusive custom install CTA
- allow the user to dismiss it
- remember dismissal for a sensible period
- do not repeatedly harass the user

IOS / IPHONE / IPAD

Since installation behavior differs:

detect the relevant environment and show clear instructions such as:

1. Open the Share menu
2. Select “Add to Home Screen”
3. Confirm installation

The UI should use clear visual guidance.

Do not claim that iOS supports the same programmatic install prompt as Android.

Do not show install instructions when already running in standalone mode.

==================================================
22. MOBILE-FIRST REQUIREMENTS
==================================================

The application must be designed mobile-first.

Test at minimum:

- 320 px
- 360 px
- 375 px
- 390 px
- 430 px
- tablet
- desktop
- wide desktop

Requirements:

- no horizontal overflow
- minimum comfortable touch targets
- readable text
- sticky mobile booking CTA where useful
- clear form progression
- accessible mobile navigation
- responsive tables
- admin mobile usability
- no tiny controls
- no hover-only functionality

The booking process should be particularly optimized for smartphones.

==================================================
23. ACCESSIBILITY
==================================================

Target WCAG 2.2 AA principles.

Implement:

- semantic HTML
- correct heading hierarchy
- form labels
- keyboard navigation
- visible focus states
- sufficient contrast
- accessible dialogs
- accessible menus
- accessible error messages
- aria attributes only where semantically necessary
- screen-reader-friendly form validation
- reduced motion support

Do not use div elements as fake buttons.

==================================================
24. SEO
==================================================

SEO is a first-class requirement.

Use server-rendered or statically generated public content where appropriate.

Implement:

- unique title per page
- unique meta description
- canonical URLs
- robots.txt
- sitemap.xml
- Open Graph metadata
- social sharing metadata
- favicon
- structured headings
- semantic HTML
- optimized images
- descriptive alt text
- clean URLs
- internal linking
- noindex for private pages

Create structured data where valid:

- LocalBusiness
- Service
- FAQPage
- BreadcrumbList

Only use structured data when the visible content genuinely supports it.

Create dynamic SEO pages for airports and service zones.

Example:

Transfert aéroport Charles-de-Gaulle vers [City]

But do not generate thin, duplicated SEO spam pages.

==================================================
25. LOCAL SEO
==================================================

Prepare the site for local search.

Admin-manageable data:

- business name
- phone
- email
- address when applicable
- service areas
- opening hours
- social links

Keep business identity information consistent.

Add:

- contact information
- service coverage
- airport coverage
- structured data
- map/location information where appropriate

==================================================
26. PERFORMANCE
==================================================

Optimize for strong Core Web Vitals.

Implement:

- responsive image sizes
- image optimization
- lazy loading where appropriate
- font optimization
- minimized client JavaScript
- server components by default
- route-level loading states
- sensible caching
- code splitting
- database indexes
- paginated admin lists

Do not solve poor performance by hiding it behind loading animations.

==================================================
27. SECURITY
==================================================

Treat security as a core requirement.

Implement:

AUTHENTICATION

- secure password hashing through Django
- password validation
- email verification where appropriate
- secure password reset
- session security
- secure logout
- rate limiting for sensitive endpoints

AUTHORIZATION

Use role-based authorization.

Possible roles:

- customer
- driver
- dispatcher
- admin
- superadmin

Never rely only on hidden frontend buttons.

Every protected backend action must perform authorization.

INPUT SECURITY

Validate:

- all API payloads
- query parameters
- uploaded files
- IDs
- payment parameters
- dates
- status transitions

Protect against:

- SQL injection
- XSS
- CSRF
- IDOR
- mass assignment
- broken access control
- brute-force authentication
- credential stuffing where practical
- unrestricted uploads
- malicious redirects

Use Django ORM.

Do not build SQL strings from user input.

==================================================
28. SECURITY HEADERS
==================================================

Configure appropriate headers:

- Content-Security-Policy
- Strict-Transport-Security
- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy
- frame protection

Use secure:

- Secure cookies
- HttpOnly cookies
- appropriate SameSite settings

Do not weaken browser security merely to make development easier.

==================================================
29. CSRF, CORS AND DOMAINS
==================================================

Design correct production boundaries.

Potential production architecture:

Frontend:
https://example.com

Backend API:
https://api.example.com

Or use a same-origin reverse proxy architecture where that improves security and simplicity.

Configure:

- explicit allowed origins
- explicit CSRF trusted origins
- no wildcard production CORS with credentials
- secure cookies
- HTTPS only

Choose the architecture deliberately and document the decision.

==================================================
30. API DESIGN
==================================================

Create clean versioned APIs where useful.

Example:

/api/v1/

Possible resources:

- auth
- profile
- airports
- service areas
- quotes
- bookings
- payments
- customer bookings
- admin bookings
- drivers
- vehicles
- testimonials
- FAQs
- contact requests

Do not expose internal models directly without thinking about API boundaries.

Use:

- serializers
- permissions
- validation
- pagination
- filtering
- throttling where appropriate

==================================================
31. DOMAIN MODEL
==================================================

Design entities such as:

User
CustomerProfile
DriverProfile
Vehicle
Airport
ServiceArea
Address
Booking
BookingPassenger
BookingStatusHistory
BookingNote
BookingExtra
PriceQuote
PriceSnapshot
PricingRule
Payment
PaymentWebhookEvent
Refund
PromoCode
Notification
NotificationLog
ContactRequest
FAQ
Testimonial
SiteSetting
AuditLog

Do not automatically create every possible table.

First model the domain properly and remove unnecessary complexity.

==================================================
32. QUOTE ARCHITECTURE
==================================================

Separate:

Quote

from:

Booking

A quote may:

- expire
- be recalculated
- become a booking

Once a booking is confirmed:

store the agreed price snapshot.

Do not allow later pricing rule changes to alter historical booking totals.

==================================================
33. BOOKING REFERENCE
==================================================

Generate a customer-friendly booking reference.

Example format conceptually:

TR-2026-XXXXXX

Do not use sequential database IDs as public identifiers.

Public booking references must not make unauthorized access possible.

==================================================
34. ADMIN SETTINGS
==================================================

The admin should be able to manage:

- business name
- contact phone
- WhatsApp
- email
- supported currencies
- airports
- service areas
- pricing rules
- payment modes
- cancellation text
- booking lead time
- maximum booking horizon
- testimonial visibility
- FAQs
- legal content or links
- social networks

Do not create a CMS that is more complex than the business requires.

==================================================
35. CONTENT MANAGEMENT
==================================================

Frequently changing operational content should be manageable without code changes.

Examples:

- FAQs
- testimonials
- airport descriptions
- service area descriptions
- homepage contact information
- service descriptions
- business settings

Marketing page structure can remain code-controlled.

==================================================
36. CONTACT SYSTEM
==================================================

Contact form:

- name
- email
- phone optional
- subject
- message

Implement:

- validation
- spam protection
- rate limiting
- database persistence
- admin visibility
- email notification

Do not expose email SMTP credentials.

==================================================
37. ANTI-SPAM
==================================================

Use proportionate anti-spam protection.

Possible combination:

- honeypot
- rate limiting
- time-based form checks
- Turnstile or another privacy-conscious challenge when necessary

Do not create unnecessary friction for all users.

==================================================
38. ANALYTICS AND PRIVACY
==================================================

Use privacy-conscious analytics where possible.

Track meaningful conversion events:

- quote started
- quote completed
- booking started
- booking completed
- payment started
- payment successful
- contact clicked
- WhatsApp clicked

Do not include:

- full passenger names
- email addresses
- phone numbers
- payment details

inside analytics events.

Respect consent requirements applicable to the selected analytics provider.

==================================================
39. GDPR / PRIVACY
==================================================

The service operates in Europe.

Implement privacy-by-design principles.

Include:

- privacy policy
- legal notice
- appropriate consent management when required
- minimal data collection
- defined data retention strategy
- account data management architecture
- secure deletion/anonymization strategy where applicable
- consent logging where required

Do not claim automatic legal compliance.

Provide implementation support, but flag legal texts and retention policies for professional legal review.

==================================================
40. AUDITABILITY
==================================================

Audit important administrative actions:

- booking status changes
- price overrides
- refunds
- driver assignment
- manual booking changes
- payment-related administrative actions

Audit records should contain:

- actor
- action
- target
- timestamp
- relevant before/after information where appropriate

Do not log:

- passwords
- full card information
- secret keys

==================================================
41. LOGGING
==================================================

Implement structured application logging.

Log:

- request correlation ID
- major payment events
- booking state transitions
- webhook processing
- email failures
- unexpected errors

Never log:

- passwords
- tokens
- payment secrets
- full card details
- unnecessary personal data

==================================================
42. ERROR HANDLING
==================================================

Create:

- friendly public error pages
- proper API error responses
- field-level form errors
- retry-safe webhook behavior
- payment failure recovery
- network failure handling

Examples:

- payment pending
- payment failed
- PayPal window closed
- quote expired
- booking no longer available
- duplicate form submission

Do not display raw stack traces in production.

==================================================
43. CONCURRENCY AND IDEMPOTENCY
==================================================

Prevent:

- duplicate bookings caused by repeated submission
- duplicate payments
- duplicate webhook processing
- duplicate refunds
- repeated notification execution

Use database transactions where appropriate.

Use unique constraints and idempotency where appropriate.

==================================================
44. DATABASE QUALITY
==================================================

Use:

- foreign keys
- indexes
- constraints
- meaningful nullability
- timestamps
- timezone-aware datetimes

Do not store:

- dates as arbitrary strings
- money as floating-point numbers

Use decimal monetary fields and ISO currency codes.

==================================================
45. TIMEZONES
==================================================

Store datetimes safely.

Use timezone-aware timestamps.

Clearly distinguish:

- flight arrival time
- requested pickup time
- creation time
- payment time

Display times in the relevant local timezone.

==================================================
46. INTERNATIONALIZATION
==================================================

French is the initial primary language.

Build the architecture so additional languages can be added cleanly.

Do not hardcode all UI strings throughout components.

Potential future languages:

- English
- German

Use locale-aware:

- dates
- numbers
- currency

==================================================
47. TESTING
==================================================

Create meaningful automated tests.

BACKEND

Test:

- authentication
- permissions
- booking creation
- price calculation
- booking transitions
- payment state transitions
- webhook idempotency
- cancellation rules
- refund rules
- unauthorized access
- guest booking access

FRONTEND

Test:

- critical forms
- validation
- booking progression
- error states

E2E

Use Playwright for critical journeys:

1. guest booking
2. customer booking
3. Stripe test payment
4. PayPal sandbox flow where automation is practical
5. admin confirms booking
6. booking cancellation
7. mobile booking flow

Do not chase meaningless 100% test coverage.

Prioritize business-critical paths.

==================================================
48. DEVELOPMENT AND PRODUCTION ENVIRONMENTS
==================================================

Support:

- local development
- staging
- production

Separate:

- databases
- Stripe keys
- PayPal credentials
- webhook secrets
- email configuration
- domains

Never allow development credentials to silently operate in production.

==================================================
49. STRIPE TEST AND LIVE MODE
==================================================

Provide a documented process for:

- development with Stripe test mode
- webhook local development
- staging
- production live keys
- production webhook endpoints

The UI or logs must make environment mistakes detectable.

Do not accidentally mix test and live identifiers.

==================================================
50. PAYPAL SANDBOX AND LIVE MODE
==================================================

Provide equivalent separation for:

- PayPal sandbox
- PayPal production

Never use production credentials in development.

==================================================
51. SECRETS
==================================================

Secrets belong only in secure environment configuration.

Examples:

- Django SECRET_KEY
- database credentials
- Stripe secret key
- Stripe webhook secret
- PayPal client secret
- email password
- storage credentials

Never:

- commit .env files
- expose secret keys through NEXT_PUBLIC variables
- print secrets into logs

Create:

.env.example

with variable names and safe dummy values only.

==================================================
52. FILE UPLOADS
==================================================

Only implement uploads if genuinely needed.

Possible future examples:

- driver documents
- vehicle documents

If uploads are implemented:

- validate MIME type
- validate extension
- validate size
- generate safe filenames
- store outside executable paths
- prevent direct execution
- authorization-protect private files

==================================================
53. RESPONSIVE ADMIN
==================================================

The admin dashboard must work on desktop and tablet and remain usable on mobile.

Use:

- responsive navigation
- mobile filter drawer
- responsive booking cards when tables become impractical
- accessible action menus

Do not simply squeeze desktop tables onto mobile.

==================================================
54. USER EXPERIENCE DETAILS
==================================================

Implement:

- loading states
- disabled submit during submission
- double-submit prevention
- success feedback
- clear empty states
- confirmation dialogs for destructive actions
- unsaved-change warnings where important
- route progress where useful

Forms must preserve user input when recoverable errors occur.

==================================================
55. BOOKING PROGRESS UX
==================================================

On mobile, use a clear booking step flow.

Example:

Trajet
Voyageur
Options
Paiement

Avoid showing a giant form containing every field at once.

Allow:

- previous step
- continue
- progress indicator

Do not lose entered information when moving backward.

==================================================
56. TRUST AND CONVERSION
==================================================

Throughout the design, answer these user questions:

- Is this service legitimate?
- Who will pick up my relative?
- What happens after I pay?
- What happens if the flight is delayed?
- Can I contact someone?
- Is my payment secure?
- Can I cancel?
- How will the passenger identify the driver?

Make these answers easy to find.

==================================================
57. FLIGHT DELAY ARCHITECTURE
==================================================

For the MVP:

Allow:

- flight number
- expected arrival time
- admin notes
- manual operational adjustment

Prepare the domain for future integration with a flight-status API.

Do not pretend to have live flight tracking without a real provider.

==================================================
58. MAP AND ROUTE ARCHITECTURE
==================================================

Support address autocomplete where configured.

Never trust the displayed address alone.

Store where appropriate:

- formatted address
- latitude
- longitude
- provider place ID

The backend remains authoritative for pricing.

Do not expose unrestricted expensive map API keys.

Apply provider restrictions.

==================================================
59. FUTURE FEATURES TO PREPARE FOR
==================================================

Keep the architecture extensible for:

- live flight tracking
- SMS
- WhatsApp Business notifications
- driver PWA
- dispatcher role
- multi-driver scheduling
- recurring corporate customers
- business accounts
- promo codes
- loyalty program
- multilingual support
- multi-currency
- additional countries

Do not implement all of these in the MVP unless required.

==================================================
60. RECOMMENDED PROJECT STRUCTURE
==================================================

Design a clean structure.

Example concept:

frontend/
    app/
    components/
    features/
    lib/
    services/
    hooks/
    types/
    public/

backend/
    config/
    apps/
        accounts/
        bookings/
        payments/
        pricing/
        drivers/
        locations/
        notifications/
        content/
        audit/
    tests/

docs/
scripts/

Adapt this structure intelligently.

Do not create a huge number of tiny modules with no architectural benefit.

==================================================
61. DOCUMENTATION
==================================================

Create:

README.md

docs/ARCHITECTURE.md
docs/DOMAIN_MODEL.md
docs/BOOKING_FLOW.md
docs/PAYMENT_ARCHITECTURE.md
docs/SECURITY.md
docs/DEPLOYMENT.md
docs/ENVIRONMENT_VARIABLES.md
docs/BACKUP_AND_RESTORE.md
docs/OPERATIONS.md

Documentation must reflect the actual implementation.

==================================================
62. DEPLOYMENT
==================================================

Create production deployment instructions for Ubuntu without Docker.

Include:

- system dependencies
- PostgreSQL creation
- backend virtualenv
- backend environment setup
- database migrations
- Django collectstatic when relevant
- frontend install
- frontend build
- systemd services
- Nginx configuration
- SSL
- firewall
- file permissions
- backup strategy
- log inspection
- restart commands
- deployment update process
- rollback approach

Do not expose:

- PostgreSQL
- Redis

directly to the public internet.

==================================================
63. BACKUPS
==================================================

Provide a practical backup strategy.

At minimum:

- PostgreSQL backups
- uploaded media backups when applicable
- retention policy
- restore procedure
- periodic restore testing

A backup without a tested restore process is incomplete.

==================================================
64. OBSERVABILITY
==================================================

Implement or prepare:

- application health endpoint
- structured logs
- error monitoring integration point
- payment webhook monitoring
- failed job monitoring when background jobs exist

Do not expose sensitive diagnostic information publicly.

==================================================
65. DELIVERY PHASES
==================================================

Before implementation, produce a phased plan.

Suggested structure:

PHASE 0
Existing codebase audit, if applicable

PHASE 1
Architecture and project foundation

PHASE 2
Design system and public website

PHASE 3
Accounts and authentication

PHASE 4
Airports, service zones, and pricing

PHASE 5
Booking engine

PHASE 6
Stripe payments

PHASE 7
PayPal payments

PHASE 8
Customer dashboard

PHASE 9
Operational admin dashboard

PHASE 10
Notifications

PHASE 11
PWA

PHASE 12
SEO and structured data

PHASE 13
Security hardening

PHASE 14
Testing

PHASE 15
Production deployment

PHASE 16
Post-deployment validation

For every phase specify:

- objectives
- files/modules affected
- database changes
- API changes
- frontend changes
- security considerations
- tests
- acceptance criteria
- dependencies on previous phases

==================================================
66. FIRST TASK
==================================================

DO NOT immediately generate thousands of lines of code.

First perform the following:

1. Analyze the business requirements.
2. State the assumptions you are making.
3. Identify missing business decisions that block implementation.
4. Separate blockers from decisions that can safely use sensible defaults.
5. Propose the final architecture.
6. Explain the frontend/backend responsibility boundaries.
7. Design the domain model.
8. Design the booking lifecycle.
9. Design the payment lifecycle for Stripe.
10. Design the payment lifecycle for PayPal.
11. Design authentication and authorization.
12. Define the PWA strategy for Android and iPhone.
13. Define the SEO architecture.
14. Define the security architecture.
15. Define the deployment architecture without Docker.
16. Create the complete phased implementation plan.
17. Identify MVP features versus future features.
18. Identify major risks and edge cases.

Then create:

docs/IMPLEMENTATION_PLAN.md

The implementation plan must be detailed enough that another senior developer could implement the platform from it.

After the plan is complete:

- inspect it for contradictions
- verify that all requirements are covered
- verify that no fake or incomplete features are being proposed
- verify that the architecture is not unnecessarily overengineered

Only after completing this analysis should implementation begin.

==================================================
67. IMPORTANT PRODUCT QUESTIONS TO RESOLVE
==================================================

During the initial analysis, explicitly resolve or flag these questions:

1. Is pricing fixed by airport and destination zone, calculated by distance, or manually quoted?
2. Must customers pay 100% during booking?
3. Is payment on arrival allowed?
4. Is a deposit allowed?
5. What is the cancellation/refund policy?
6. How long before pickup can a customer book?
7. Can users book same-day transport?
8. What geographic areas are served?
9. Is there currently one driver or multiple drivers?
10. Is automatic driver assignment required?
11. Does the business need live flight tracking now?
12. Is WhatsApp only for contact or also for automated notifications?
13. Are customer accounts required, or is guest booking sufficient for MVP?
14. Should prices be visible before the user submits personal details?
15. Does the business issue invoices or simple payment receipts?
16. Is VAT applicable, and at what rate?
17. What currencies are accepted?
18. What languages are required at launch?
19. Are child seats available?
20. Are wheelchair-accessible vehicles available?
21. Is waiting time charged?
22. What happens if a flight is delayed?
23. Is there a maximum luggage capacity?
24. Should the customer receive driver details before pickup?
25. Is the service provided by the company itself or by independent drivers?

Do not block all planning because some answers are missing.

Make sensible, explicitly documented assumptions where safe.

==================================================
68. DEFINITION OF DONE
==================================================

The application is not complete merely because it compiles.

A feature is complete only when:

- frontend works
- backend works
- validation works
- authorization works
- errors are handled
- mobile layout works
- accessibility is considered
- tests exist for critical behavior
- production configuration is documented
- no placeholder implementation remains
- the feature works with real persisted data

The final product must feel like a real professional transport company platform capable of accepting real customer bookings and real payments.