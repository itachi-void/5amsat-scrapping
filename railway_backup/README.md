Railway Backup endpoint

This small Flask service exposes:
- POST /api/backup : store incoming backup JSON (requires Authorization Bearer token if `RAILWAY_BACKUP_TOKEN` is set)
- GET  /api/backup : return latest backup JSON (requires token if set)

Deployment (Railway CLI):

1. From this folder run:

```bash
railway init  # if not already linked to a project
railway up
```

2. Set variables in Railway (Dashboard > Variables) or via CLI:

```bash
railway variables set RAILWAY_BACKUP_TOKEN=some-secret-token
# Optional: add a PostgreSQL plugin and set DATABASE_URL automatically
# railway add postgres
# The plugin will provide DATABASE_URL in environment
```

3. In your bot project (or Railway service for the bot) set:

- `RAILWAY_BACKUP_URL` to your deployed service URL, e.g. `https://<app>.up.railway.app/api/backup`
- `RAILWAY_BACKUP_TOKEN` to the same token used above

After deploy the bot will automatically call `download_railway_backup()` at startup and `telegraph_sync_thread` will push backups to `RAILWAY_BACKUP_URL` when configured.

If you want I can try to deploy this service for you now (you are already logged in with Railway CLI)."