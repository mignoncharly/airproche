# Progressive Web App

Phase 11 provides an installable public shell without caching customer or
transactional data.

## Installability

The App Router publishes `/manifest.webmanifest` with 192px, 512px, and
maskable PNG icons derived from the existing Airproche mark. The root layout
declares the manifest, theme color, application name, standard icons, and Apple
web-app metadata.

Chromium browsers expose the application install button only after the native
`beforeinstallprompt` event. Eligible iPhone and iPad users receive accurate
Safari instructions: Share, Sur l’écran d’accueil, then Ajouter. No unsupported
automatic iOS prompt is claimed.

## Cache boundary

`public/sw.js` pre-caches exactly:

- `/offline`;
- `/icons/icon-192.png`;
- `/icons/icon-512.png`;
- `/icons/icon-maskable-512.png`.

Install-time requests use `credentials: "omit"`. The worker never writes a
runtime response to Cache Storage. API, account, operations, booking, payment,
authentication, reset, and verification paths are explicitly bypassed.
Non-GET and cross-origin requests are also bypassed.

Public navigations remain network-first and fall back to the generic offline
document. Sensitive routes are never intercepted for offline fallback and no
customer, booking, payment, authenticated API, cookie, or token data is cached.

## Updates

A newly installed worker waits by default. The UI detects a waiting worker and
offers a user action. Only that action sends `SKIP_WAITING`; the page reloads
only after the resulting `controllerchange`. The worker response itself uses
`Cache-Control: no-cache, no-store, must-revalidate`.

## Verification

```bash
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
npm run test:e2e
```

The unit suite covers manifest, offline markup, allow-list, sensitive-path
bypass, update activation, Android/iOS behavior, and response headers. Playwright
runs manifest, exact-cache, offline-navigation, and responsive overflow checks
in desktop Chromium and Pixel 7 emulation.
