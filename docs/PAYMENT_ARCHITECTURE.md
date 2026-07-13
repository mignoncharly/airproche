# Stripe payments

Phase 6 implements Stripe Checkout in test mode when `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STRIPE_ENVIRONMENT=test` are configured. PayPal is not enabled by this phase.

The browser never supplies an amount or currency. Checkout is created from the locked booking price snapshot, and the server sends Stripe the booking reference, public identifiers, exact minor-unit amount, currency, and environment metadata.

## Flow

1. A guest or authenticated customer submits `POST /api/v1/payments/bookings/<booking_public_id>/checkout/` with the booking-management token when applicable and a unique `Idempotency-Key`.
2. The server locks the booking and its one-to-one `Payment`. A pending checkout session is reused, so retries do not create a second open session or charge.
3. Stripe Checkout receives the customer through the returned URL. Redirects are never treated as payment proof.
4. Stripe sends the signed event to `POST /api/v1/payments/webhooks/stripe/`. The raw request body is verified with the endpoint secret before JSON processing.
5. `checkout.session.completed` is accepted only when session ID, metadata, amount, currency, environment, and `payment_status=paid` match the local snapshot. Only then is the payment marked succeeded and a `PENDING_PAYMENT` booking moved to `CONFIRMED`.
6. Duplicate provider event IDs are acknowledged without repeating the state transition. Mismatches are stored as quarantined webhook events and never confirm a booking.

The return page at `/paiement/retour` captures booking and Checkout session identifiers from the URL fragment, removes the fragment, then polls server status. It can show pending, failed, canceled, succeeded, or quarantined outcomes without treating the redirect as payment proof.

## Refunds and reconciliation

Staff can reconcile a payment from its Checkout session and create full or partial refunds through permission-protected endpoints. Refund requests require an idempotency key; pending and successful refunds are reserved against the captured amount, and a booking is never resurrected if it was canceled while payment settled. Stripe failures remain visible on the payment/refund record.

## Configuration

```text
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_ENVIRONMENT=test
```

Use a separate Stripe account/key/webhook endpoint for each environment. Never expose these values with `NEXT_PUBLIC_`, store them in the database, or log raw webhook payloads/secrets. Production live mode requires `sk_live_...`, `STRIPE_ENVIRONMENT=live`, `STRIPE_LIVE_MODE_CONFIRMED=true` after explicit approval, HTTPS, and a real webhook secret.

The local webhook endpoint can be exercised with the Stripe CLI or signed fixtures in `backend/tests/test_payments.py`. Live-provider smoke testing and production endpoint registration remain release activities for Phase 14–16.
