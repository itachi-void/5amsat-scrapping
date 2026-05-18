Railway Backup endpoint

This Flask service exposes:

- `POST /api/backup`: store incoming backup JSON
- `GET /api/backup`: return latest backup JSON

Security and persistence defaults:

- `RAILWAY_BACKUP_TOKEN` is required by default (`REQUIRE_BACKUP_TOKEN=1`)
- `DATABASE_URL` is required by default (`REQUIRE_DATABASE=1`)
- This guarantees data persistence across Railway deploys/restarts via Postgres

Deployment (Railway):

1. Deploy this folder (`railway_backup`) as a service.
2. Add PostgreSQL in Railway project (plugin/service) and ensure `DATABASE_URL` is available in this service.
3. Set service variables:

```bash
RAILWAY_BACKUP_TOKEN=<strong-random-token>
REQUIRE_BACKUP_TOKEN=1
REQUIRE_DATABASE=1
```

4. Use this endpoint in bot service variables:

- `RAILWAY_BACKUP_URL=https://<your-service>.up.railway.app/api/backup`
- `RAILWAY_BACKUP_TOKEN=<same-token>`

Behavior:

- Bot calls `download_railway_backup()` on startup to restore latest backup.
- Bot pushes fresh backups to `RAILWAY_BACKUP_URL` during sync loop.

This setup ensures backup data survives new deploys and restarts.
