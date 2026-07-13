# Operations dashboard

Phase 9 adds the staff-only operations surface at `/operations` and the API namespace `/api/v1/staff/operations/`.

## Daily workflow

The dashboard provides:

- KPI cards for bookings, unassigned upcoming trips, active trips, payment attention, and confirmed revenue;
- search by reference, customer name, e-mail, or phone;
- status, assignment, and payment filters;
- responsive booking list/detail views;
- controlled booking transitions using the existing booking state machine;
- internal booking notes;
- driver and vehicle assignment with capacity, service-area, accessibility, and overlap checks;
- explicit override reasons for exceptional assignments;
- payment status and full-refund action through the existing Stripe staff command;
- a link to Django Admin for content, coverage, pricing, and settings maintenance.

## Domain and security

Drivers, vehicles, historical assignments, and append-only operational audit events are stored in `apps.operations`. An active assignment is unique per booking. A driver or vehicle cannot be assigned to another active trip within the two-hour operational conflict window unless an authorized operator supplies an override reason.

All operational endpoints require an authenticated staff session plus the relevant Django model permission. The seeded Operations, Dispatcher, Finance, and Administrator groups receive scoped permissions; non-staff users cannot use the API even if they know the URLs.

KPI periods use the configured Django timezone (`Europe/Paris` in the current deployment) and UTC-backed timestamps. Empty periods return zero values with `has_data=false`; no placeholder metrics are generated.

Sensitive transitions, notes, assignments, unassignments, and overrides write `AuditEvent` records with actor, before/after data, reason, correlation ID, and timestamp.

## Verification

Phase 9 tests cover staff and permission isolation, KPI/list filters, capacity and overlapping-assignment conflicts, controlled overrides, status history, notes, and audit records. Frontend lint, typecheck, Vitest, and production build checks pass.
