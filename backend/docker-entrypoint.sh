#!/bin/sh
set -e

echo "Waiting for database..."
python << 'EOF'
import time
from sqlalchemy import text
from app.database import Base, engine, sync_player_id_sequence
from app import models  # noqa: F401

for i in range(60):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("database not ready after 60s")

Base.metadata.create_all(bind=engine)
sync_player_id_sequence()

# PostgreSQL: ensure club_id nullable for lobby competitions (legacy DBs)
if "postgresql" in str(engine.url):
    with engine.begin() as conn:
        conn.execute(text("""
            DO $$ BEGIN
                ALTER TABLE competitions ALTER COLUMN club_id DROP NOT NULL;
            EXCEPTION
                WHEN others THEN NULL;
            END $$;
        """))

print("database tables ready")
EOF

echo "Running Alembic migrations..."
if ! python -m alembic upgrade head; then
    echo "WARN: alembic upgrade failed; stamping head for legacy database"
    python -m alembic stamp head || true
fi

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
