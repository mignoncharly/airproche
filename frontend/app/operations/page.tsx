import type { Metadata } from "next";

import { OperationsDashboard } from "@/features/operations/operations-dashboard";

export const metadata: Metadata = { title: "Opérations", robots: { index: false, follow: false } };

export default function OperationsPage() {
  return <main className="min-h-[70vh] bg-slate-50 py-8 sm:py-12"><div className="site-container"><OperationsDashboard /></div></main>;
}

