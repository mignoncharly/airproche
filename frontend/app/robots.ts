import type { MetadataRoute } from "next";

import { absoluteUrl } from "@/lib/seo";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: [
        "/api/",
        "/compte",
        "/operations",
        "/reservation",
        "/paiement",
        "/connexion",
        "/inscription",
        "/mot-de-passe-oublie",
        "/reinitialiser-mot-de-passe",
        "/verification-email",
        "/offline",
      ],
    },
    sitemap: absoluteUrl("/sitemap.xml"),
  };
}
