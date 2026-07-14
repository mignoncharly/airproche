# Airproche production deployment

Status: prepared but not deployed. The canonical URL is
`https://airproche.docufisc.de`; `https://www.airproche.docufisc.de` redirects
to the canonical host. The Stripe webhook URL is
`https://airproche.docufisc.de/api/v1/payments/webhooks/stripe/`.

## Isolation map

| Resource | Airproche value |
| --- | --- |
| Root | `/home/mignon/airproche` |
| Releases | `/home/mignon/airproche/releases/<git-sha>` |
| Current release | `/home/mignon/airproche/current` symlink |
| Secret environment | `shared/.env.production`, mode `0600` |
| Web-only environment | `shared/.env.web`, mode `0600`, no backend secrets |
| Static/media/cache | `shared/static`, `shared/media`, `shared/next-cache` |
| Backups | `/home/mignon/airproche/backups` |
| PostgreSQL | database `airproche`, login role `airproche`, localhost only |
| API | `airproche-api.service`, `127.0.0.1:8050` |
| Web | `airproche-web.service`, `127.0.0.1:3050` |
| Backup | `airproche-backup.service` and `.timer` |
| Nginx | `/etc/nginx/sites-available/airproche` only |
| Certificate | Dedicated `/etc/letsencrypt-airproche`; canonical and `www` names |
| Certificate renewal | `airproche-cert-renew.service` and `.timer` only |

Airproche does not need Redis: production throttling/cache state uses its own
PostgreSQL cache table. No Redis instance, port, database, password, or service
is created or shared. PayPal remains skipped and has no deployment variables.

## Audited VPS baseline

The read-only audit on 2026-07-14 found Ubuntu 24.04, PostgreSQL 16, Nginx, and
many unrelated applications. Ports 3050 and 8050 were unused. No Airproche
units existed. Disk capacity was sufficient, but swap was effectively full and
available memory was near 1 GiB. Deployment refuses to build below 700 MiB `MemAvailable` or with less than
256 MiB free swap; schedule the build when pressure is low and do not stop
another application to make space.

`certbot.service` and `docufisc-service-health.service` were already failed.
They are not Airproche resources and these scripts never restart, repair, or
change them. The deployment captures the running neighboring application units
before work and fails if any of those units are no longer active afterward.

## Prerequisites

1. Point both `airproche.docufisc.de` and `www.airproche.docufisc.de` A records
   to `82.165.94.233` and wait for public DNS propagation.
2. Create a Zoho SMTP mailbox/app password. The interactive script uses
   `smtp.zoho.eu`, port 587, STARTTLS. Configure and verify the chosen sender's
   SPF, DKIM, and DMARC records in Zoho/DNS.
3. Create Stripe **test-mode** API and webhook secrets. Register the exact
   webhook URL above. Live keys are rejected by the deployment script.
4. Choose the administrator/VPN CIDRs permitted to reach staff endpoints.
5. Ensure the source checkout is clean and synchronized:

```bash
git -C /home/mignon/airproche fetch origin
git -C /home/mignon/airproche pull --ff-only origin main
```

Do not paste passwords or keys into command arguments or shell history.

## Operator sequence

Run these commands yourself on the VPS:

```bash
cd /home/mignon/airproche
sudo scripts/bootstrap-production.sh
sudo scripts/configure-production-secrets.sh
sudo scripts/deploy-production.sh origin/main
sudo scripts/enable-production-tls.sh YOUR_CERTBOT_CONTACT_EMAIL
./scripts/smoke-production.sh
```

### Bootstrap guarantees

`bootstrap-production.sh` generates independent Django, PostgreSQL, and backup
encryption secrets with OpenSSL and stores them without printing. It creates
only the fixed PostgreSQL role and database named `airproche`, and refuses to
reuse either name if it already exists. It installs only `airproche-*` units
and an HTTP-only Airproche ACME block after `nginx -t`. It also refuses an
existing environment file, dirty repository identity, missing prerequisites,
or occupied Airproche ports. It does not start the application.

### Interactive provider configuration

`configure-production-secrets.sh` reads the Zoho app password, Stripe test key,
and Stripe test webhook secret from `/dev/tty` with hidden input. Values are
written atomically to the mode-`0600` environment file and never printed. It
rejects live Stripe keys and validates staff CIDRs. The detected SSH client
address is offered as a `/32` default; use a stable VPN/office CIDR where
possible.

### Immutable deployment

`deploy-production.sh` fetches the selected commit, exports it to a new SHA
release, creates that release's Python virtualenv and Node tree, runs production
checks and migration preflight, creates an encrypted database backup, applies
migrations, creates the PostgreSQL cache table, collects shared static files,
and builds Next.js with an allow-listed environment containing no backend
secrets. It atomically switches `current`, restarts only the two Airproche
services, starts the Airproche backup timer, verifies local readiness, and
checks that neighboring services remain active.

On application failure it restores the previous `current` symlink and restarts
only Airproche. It never reverses database migrations automatically. A failed
release directory remains available for inspection and is never silently
reused or mutated.

### Dedicated TLS

`enable-production-tls.sh` refuses DNS addresses other than this VPS. It calls
`certbot certonly --webroot` with dedicated config, work, and log directories
(`/etc/letsencrypt-airproche`, `/var/lib/letsencrypt-airproche`, and
`/var/log/letsencrypt-airproche`). It does not call Certbot's Nginx installer,
read or write the shared `/etc/letsencrypt`, alter `certbot.service`, or touch
another certificate. Renewal is performed only by the Airproche renewal timer. It installs
only the Airproche TLS block and validates all Nginx configuration before reload, verifies public health, and verifies the
`www` redirect.

## Operations

```bash
systemctl status airproche-api.service airproche-web.service
systemctl status airproche-backup.timer
journalctl -u airproche-api.service -u airproche-web.service --since today
curl -fsS https://airproche.docufisc.de/api/v1/health/live/
curl -fsS https://airproche.docufisc.de/api/v1/health/ready/
```

Application logs go to journald and use the backend redacting JSON formatter.
Do not enable shell tracing around environment or provider scripts.

## Rollback

1. Identify the preceding directory under `releases/` and confirm it is a
   reviewed Airproche SHA.
2. Review migrations made by the failed release. Do not reverse them blindly.
3. Atomically point `current` to the preceding release.
4. Restart only `airproche-api.service` and `airproche-web.service`.
5. Run local health, the public smoke script, and neighboring-service checks.

Database restoration is an incident operation, not an automatic application
rollback. Follow `BACKUP_AND_RESTORE.md`.

## Remaining launch checks

Deployment is not complete until the operator sequence succeeds. Real Zoho
mail delivery, Stripe test Checkout/webhook/reconciliation, published business
content, staff access from the approved network, encrypted off-host backup
copy, and the Phase 16 customer/guest/staff journeys remain required. Production
must not contain fictional qualification records.
