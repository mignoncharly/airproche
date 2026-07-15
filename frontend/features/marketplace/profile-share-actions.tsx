"use client";

import QRCode from "qrcode";
import { useEffect, useRef, useState } from "react";

export function ProfileShareActions({ name, path, showQr = false }: { name: string; path: string; showQr?: boolean }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [message, setMessage] = useState("");
  const url = typeof window === "undefined" ? path : new URL(path, window.location.origin).toString();

  useEffect(() => {
    if (showQr && canvas.current) void QRCode.toCanvas(canvas.current, new URL(path, window.location.origin).toString(), { width: 180, margin: 2, color: { dark: "#10213f", light: "#ffffff" } });
  }, [path, showQr]);

  async function copy() { await navigator.clipboard.writeText(url); setMessage("Lien copié."); }
  async function share() { if (navigator.share) await navigator.share({ title: `Profil de ${name} sur AirProche`, url }); else await copy(); }
  function downloadQr() { if (!canvas.current) return; const link = document.createElement("a"); link.download = `profil-airproche-${path.split("/").pop()}.png`; link.href = canvas.current.toDataURL("image/png"); link.click(); }

  return <div className="flex flex-wrap items-center gap-3"><button type="button" className="button button-secondary" onClick={() => void copy()}>Copier le lien</button><button type="button" className="button button-secondary" onClick={() => void share()}>Partager le profil</button>{showQr ? <div className="w-full rounded-2xl bg-white p-4 sm:w-auto"><canvas ref={canvas} aria-label={`Code QR du profil de ${name}`} /><button type="button" className="mt-2 block text-sm font-bold text-blue-700 underline" onClick={downloadQr}>Télécharger le QR code</button></div> : null}<span className="text-sm font-semibold text-emerald-700" role="status">{message}</span></div>;
}
