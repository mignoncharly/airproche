"use client";

import { useEffect, useRef, useState } from "react";

import { Icon } from "@/components/icon";

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

function isIosDevice() {
  const userAgent = window.navigator.userAgent;
  const platform = window.navigator.platform;
  return /iPad|iPhone|iPod/.test(userAgent)
    || (platform === "MacIntel" && window.navigator.maxTouchPoints > 1);
}

function isStandalone() {
  return window.matchMedia("(display-mode: standalone)").matches
    || Boolean((window.navigator as Navigator & { standalone?: boolean }).standalone);
}

export function PwaManager() {
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [iosInstallAvailable, setIosInstallAvailable] = useState(false);
  const [showIosHelp, setShowIosHelp] = useState(false);
  const [waitingWorker, setWaitingWorker] = useState<ServiceWorker | null>(null);
  const refreshRequested = useRef(false);

  useEffect(() => {
    const iosDetectionTimer = window.setTimeout(() => {
      setIosInstallAvailable(isIosDevice() && !isStandalone());
    }, 0);

    function captureInstall(event: Event) {
      event.preventDefault();
      setInstallPrompt(event as BeforeInstallPromptEvent);
    }
    window.addEventListener("beforeinstallprompt", captureInstall);

    if (!("serviceWorker" in navigator)) {
      return () => {
        window.clearTimeout(iosDetectionTimer);
        window.removeEventListener("beforeinstallprompt", captureInstall);
      };
    }

    let active = true;
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).then((registration) => {
      if (!active) return;
      if (registration.waiting) setWaitingWorker(registration.waiting);
      registration.addEventListener("updatefound", () => {
        const worker = registration.installing;
        worker?.addEventListener("statechange", () => {
          if (worker.state === "installed" && navigator.serviceWorker.controller) {
            setWaitingWorker(worker);
          }
        });
      });
    }).catch(() => {
      // The application remains fully usable when service-worker registration fails.
    });

    function reloadAfterUpdate() {
      if (refreshRequested.current) window.location.reload();
    }
    navigator.serviceWorker.addEventListener("controllerchange", reloadAfterUpdate);

    return () => {
      active = false;
      window.clearTimeout(iosDetectionTimer);
      window.removeEventListener("beforeinstallprompt", captureInstall);
      navigator.serviceWorker.removeEventListener("controllerchange", reloadAfterUpdate);
    };
  }, []);

  async function install() {
    if (!installPrompt) return;
    await installPrompt.prompt();
    await installPrompt.userChoice;
    setInstallPrompt(null);
  }

  function applyUpdate() {
    if (!waitingWorker) return;
    refreshRequested.current = true;
    waitingWorker.postMessage({ type: "SKIP_WAITING" });
  }

  if (!installPrompt && !iosInstallAvailable && !waitingWorker) return null;

  return (
    <aside className="pointer-events-auto w-full max-w-xl rounded-2xl border border-slate-300 bg-white p-4 shadow-xl" aria-label="Installation de l’application">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm font-bold text-slate-950">
          {waitingWorker ? "Une mise à jour est prête." : "Installer Airproche sur cet appareil."}
        </p>
        <div className="flex flex-wrap gap-2">
          {waitingWorker ? (
            <button className="button button-primary" type="button" onClick={applyUpdate}>
              <Icon name="refresh" className="size-4" /> Mettre à jour
            </button>
          ) : null}
          {installPrompt ? (
            <button className="button button-primary" type="button" onClick={() => void install()}>
              <Icon name="download" className="size-4" /> Installer
            </button>
          ) : null}
          {iosInstallAvailable ? (
            <button className="button button-secondary" type="button" onClick={() => setShowIosHelp((current) => !current)} aria-expanded={showIosHelp}>
              <Icon name="share" className="size-4" /> Installation iPhone/iPad
            </button>
          ) : null}
        </div>
      </div>
      {showIosHelp ? (
        <p className="mt-3 border-t border-slate-200 pt-3 text-sm leading-6 text-slate-700">
          Ouvrez cette page dans Safari. Touchez Partager, puis Sur l’écran d’accueil, puis Ajouter.
        </p>
      ) : null}
    </aside>
  );
}
