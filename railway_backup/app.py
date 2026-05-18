from flask import Flask, request, jsonify
import os
import json
import datetime
import pathlib

app = Flask(__name__)

BACKUPS_DIR = pathlib.Path("backups")

DB_URL = os.getenv("DATABASE_URL", "").strip()
TOKEN = os.getenv("RAILWAY_BACKUP_TOKEN", "").strip()
REQUIRE_TOKEN = os.getenv("REQUIRE_BACKUP_TOKEN", "1").strip() == "1"
REQUIRE_DB = os.getenv("REQUIRE_DATABASE", "1").strip() == "1"

# Lazy import of psycopg2 if DATABASE_URL present
db_conn = None
psycopg2 = None
if DB_URL:
    try:
        import psycopg2
        import psycopg2.extras
        db_conn = psycopg2.connect(DB_URL)
        with db_conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                data JSONB
            )
            """)
            db_conn.commit()
    except Exception as e:
        app.logger.warning(f"Failed to init DB: {e}")
        db_conn = None

if REQUIRE_TOKEN and not TOKEN:
    raise RuntimeError("RAILWAY_BACKUP_TOKEN is required when REQUIRE_BACKUP_TOKEN=1")

if REQUIRE_DB and not db_conn:
    raise RuntimeError("DATABASE_URL is required and must be reachable when REQUIRE_DATABASE=1")


def _authorize(req):
    if not TOKEN:
        return True
    auth = req.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1] == TOKEN
    return False


@app.route("/api/backup", methods=["GET", "POST"])
def backup():
    if not _authorize(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 403

    if request.method == "POST":
        data = request.get_json(force=True)
        if data is None:
            return jsonify({"ok": False, "error": "invalid json"}), 400

        if db_conn:
            try:
                with db_conn.cursor() as cur:
                    cur.execute("INSERT INTO backups (data) VALUES (%s) RETURNING id, created_at", (json.dumps(data),))
                    res = cur.fetchone()
                    db_conn.commit()
                    return jsonify({"ok": True, "id": res[0], "created_at": res[1].isoformat()})
            except Exception as e:
                app.logger.error(f"DB insert failed: {e}")
                return jsonify({"ok": False, "error": "db_error"}), 500
        else:
            if REQUIRE_DB:
                return jsonify({"ok": False, "error": "database_required"}), 500
            try:
                BACKUPS_DIR.mkdir(exist_ok=True)
                ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                fp = BACKUPS_DIR / f"backup_{ts}.json"
                with fp.open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                # also update latest.json
                latest = BACKUPS_DIR / "latest.json"
                with latest.open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                return jsonify({"ok": True, "path": str(fp)})
            except Exception as e:
                app.logger.error(f"File write failed: {e}")
                return jsonify({"ok": False, "error": "write_error"}), 500

    else:  # GET
        if db_conn:
            try:
                with db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT data, created_at FROM backups ORDER BY created_at DESC LIMIT 1")
                    row = cur.fetchone()
                    if not row:
                        return jsonify({"ok": False, "error": "not_found"}), 404
                    return jsonify({"ok": True, "backup": row["data"], "created_at": row["created_at"].isoformat()})
            except Exception as e:
                app.logger.error(f"DB select failed: {e}")
                return jsonify({"ok": False, "error": "db_error"}), 500
        else:
            if REQUIRE_DB:
                return jsonify({"ok": False, "error": "database_required"}), 500
            latest = BACKUPS_DIR / "latest.json"
            if not latest.exists():
                return jsonify({"ok": False, "error": "not_found"}), 404
            try:
                with latest.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                return jsonify({"ok": True, "backup": data})
            except Exception as e:
                app.logger.error(f"File read failed: {e}")
                return jsonify({"ok": False, "error": "read_error"}), 500


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "ok": True,
        "service": "railway-backup",
        "token_required": REQUIRE_TOKEN,
        "database_required": REQUIRE_DB,
        "database_connected": bool(db_conn),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
