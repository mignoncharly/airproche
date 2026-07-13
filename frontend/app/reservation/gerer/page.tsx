import type { Metadata } from "next";

import { ManageBooking } from "@/features/bookings/manage-booking";

export const metadata: Metadata = { title: "Gérer ma réservation", robots: { index: false, follow: false } };

export default function ManageBookingPage() {
  return <main><ManageBooking /></main>;
}
