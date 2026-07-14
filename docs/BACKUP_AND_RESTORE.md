# Airproche backup and restore

## Schedule and format

`airproche-backup.timer` runs daily at 02:35 UTC with up to ten minutes of
random delay. It dumps only the localhost database `airproche` through its
least-privilege login, creates a PostgreSQL custom-format archive, encrypts it
with AES-256-CBC/PBKDF2, writes a SHA-256 sidecar, and retains 14 days by
default. Final files are mode `0600` under `/home/mignon/airproche/backups`:

```text
airproche-YYYYMMDDTHHMMSSZ.dump.enc
airproche-YYYYMMDDTHHMMSSZ.dump.enc.sha256
```

The backup encryption key is generated separately from the database password
and stored only in `shared/.env.production`. A same-host key protects misplaced
backup files but is not disaster recovery. Copy only the encrypted archive and
checksum to an approved encrypted off-host destination. The destination,
credentials, retention contract, and monitoring owner are a launch decision;
they must not be borrowed from another application.

Trigger and inspect an on-demand backup:

```bash
sudo systemctl start airproche-backup.service
sudo systemctl status airproche-backup.service
sudo journalctl -u airproche-backup.service -n 50 --no-pager
```

Never upload the environment file or plaintext database dump off-host.
`shared/media` requires its own encrypted backup if personal uploads are ever
enabled; it is not exposed by the Airproche Nginx block.

## Restore drill

After the first backup, run:

```bash
sudo /home/mignon/airproche/current/scripts/test-production-restore.sh
```

An optional encrypted backup pathname may be supplied, but it must resolve
inside the Airproche backup directory and match the Airproche filename. The
script verifies its checksum, decrypts into a mode-`0600` temporary file,
refuses any pre-existing destination, creates only
`airproche_restore_test`, restores without ownership/privilege records, compares
all managed Django model counts, runs Django and migration checks, and always
drops the restore-test database and plaintext temporary file.

This drill briefly contains production data on the same VPS. Restrict operator
access, do not expose the database on a network interface, and inspect logs for
counts/status only—not row contents.

## Emergency production restoration

Production restoration requires an incident decision and maintenance window:

1. record the current release, database status, incident reason, and approver;
2. stop only `airproche-api.service` and `airproche-web.service`;
3. take and preserve a new encrypted pre-restore backup if PostgreSQL is usable;
4. verify the selected archive checksum and successful restore drill;
5. restore to a newly created Airproche-only candidate database first;
6. validate migrations, row counts, critical payments, and booking integrity;
7. switch database configuration only after explicit approval, or restore the
   dedicated `airproche` database under a separately reviewed procedure;
8. start only Airproche services and run health, smoke, and reconciliation;
9. confirm all neighboring application services remain active.

Do not use `migrate --fake`, drop another database, reuse another role, or infer
a database rollback from an application release rollback.
