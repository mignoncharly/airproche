import type { Metadata } from "next";

import { ManageBooking } from "@/features/bookings/manage-booking";

export const metadata: Metadata = { title: "Gérer ma réservation", robots: { index: false, follow: false } };

export default async function ManageBookingPage({ searchParams }: { searchParams: Promise<{ reference?: string }> }) {
  const { reference = "" } = await searchParams;
  return <main><ManageBooking initialReference={reference} /></main>;
}
