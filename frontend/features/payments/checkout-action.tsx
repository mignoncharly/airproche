"use client";

import { useState } from "react";

import { type Booking } from "@/lib/booking-api";
import { PaymentApiError, createStripeCheckout } from "@/lib/payment-api";

export function CheckoutAction({ booking }: { booking: Booking }) {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  async function begin() {
    const token = booking.management_token ?? "";
    setLoading(true); setError(null);
    try {
      const result = await createStripeCheckout(booking.public_id, token);
      window.sessionStorage.setItem(`booking-management-token:${booking.public_id}`, token);
      window.location.assign(result.checkoutUrl);
    } catch (caught) {
      setError(caught instanceof PaymentApiError ? caught.message : "Le paiement ne peut pas être initialisé.");
      setLoading(false);
    }
  }
  return <div className="mt-7"><button className="button button-primary" type="button" onClick={begin} disabled={loading}>{loading ? "Ouverture de Stripe…" : "Payer maintenant"}</button>{error ? <p className="form-status-error mt-4" role="alert">{error}</p> : null}</div>;
}
