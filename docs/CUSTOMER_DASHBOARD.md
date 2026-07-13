# Customer dashboard

Phase 8 adds the authenticated customer area at `/compte`.

## Customer experience

The account panel shows:

- upcoming and past bookings, classified from the persisted pickup time and booking status;
- route, pickup details, passengers, total, booking status, and payment status;
- payment continuation when Stripe Checkout is still required;
- cancellation when the booking is still eligible;
- a fresh quote for repeat booking, so the original price is never reused;
- a protected printable receipt link for each booking.

Guest booking and guest management remain available through the existing reference and management-token flow. An account is not required to make or manage a guest booking.

## API boundaries

`GET /api/v1/bookings/mine/` returns only bookings whose `customer` is the authenticated session user. The response includes payment environment and payment status so the UI can distinguish pending, paid, failed, refunded, and not-yet-created payments.

`GET /api/v1/bookings/<public_id>/receipt/` is never cached and is available to the booking owner, staff, or a guest presenting the management token. It returns a safe printable HTML receipt with `no-store` and `noindex` headers. It is a booking/payment receipt, not a tax invoice; invoice numbering, VAT treatment, and compliant invoice generation remain blocked on the accounting decision.

Cancellation and repeat-booking endpoints reuse the existing ownership and guest-access rules. Repeating a booking requests a new quote and therefore revalidates availability, lead time, capacity, and current pricing.

## Verification

Backend tests cover account ownership isolation, receipt privacy, authenticated booking association, cancellation, and repeat booking. Frontend lint, typecheck, Vitest, and production build checks cover the dashboard integration.
