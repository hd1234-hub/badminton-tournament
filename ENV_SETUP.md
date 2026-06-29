# Environment Setup (Safe for Open Source)

This repository is configured to keep secrets out of Git.

## Local development

1. Copy template files:
   - `backend/.env.example` -> `backend/.env`
   - `frontend/.env.example` -> `frontend/.env.local`
2. Fill your local secrets in `backend/.env`:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `ANTHROPIC_AUTH_TOKEN` (optional if you do not use AI features)
3. Keep `backend/.env` and `frontend/.env.local` local-only.

## Production

Use `backend/.env.production` as a template and set real values on your server:
- `ENVIRONMENT=production`
- `RUN_AUTO_MIGRATE=false`
- real `DATABASE_URL`, `SECRET_KEY`, `ANTHROPIC_AUTH_TOKEN`
- `CORS_ORIGINS` set to your real domain

Then run migration:

`python -m alembic upgrade head`

## Important

- Never commit real `.env` files.
- If a secret was ever exposed, rotate it immediately.
