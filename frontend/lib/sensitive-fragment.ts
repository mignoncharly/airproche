"use client";

import { useEffect, useState } from "react";

export function parseSensitiveFragment(hash: string): URLSearchParams {
  return new URLSearchParams(hash.startsWith("#") ? hash.slice(1) : hash);
}

export function useSensitiveFragment(): URLSearchParams | null {
  const [params, setParams] = useState<URLSearchParams | null>(null);

  useEffect(() => {
    const captured = parseSensitiveFragment(window.location.hash);
    window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}`);
    const timer = window.setTimeout(() => setParams(captured), 0);
    return () => window.clearTimeout(timer);
  }, []);

  return params;
}
