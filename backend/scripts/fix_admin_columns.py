"""One-off migration helper: backfill users.created_at / is_admin.

Usage:
  ADMIN_USERNAMES=alice,bob python -m scripts.fix_admin_columns
"""
import os

from sqlalchemy import inspect, text

from app.database import engine

ADMIN_USERNAMES = [u.strip() for u in os.getenv("ADMIN_USERNAMES", "").split(",") if u.strip()]

insp = inspect(engine)
cols = {c["name"] for c in insp.get_columns("users")}
print("columns:", cols)

with engine.connect() as conn:
    if "created_at" not in cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP WITH TIME ZONE"))
        conn.commit()
        print("added created_at")

    conn.execute(text("UPDATE users SET created_at = NOW() WHERE created_at IS NULL"))
    conn.execute(text("UPDATE users SET is_admin = false WHERE is_admin IS NULL"))

    for username in ADMIN_USERNAMES:
        conn.execute(
            text("UPDATE users SET is_admin = true WHERE username = :username"),
            {"username": username},
        )
        row = conn.execute(
            text("SELECT username, is_admin FROM users WHERE username = :username"),
            {"username": username},
        ).fetchone()
        print(f"{username} admin:", row)

    conn.commit()
