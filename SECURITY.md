# Security Policy

## Reporting a Vulnerability

If you discover a security issue, please **do not** open a public GitHub issue with exploit details.

Instead, open a private security advisory on GitHub (if enabled) or contact the maintainers directly with:

- A clear description of the issue
- Steps to reproduce
- Impact assessment (if known)

## Secrets and Deployment

Never commit real credentials to the repository:

- `SECRET_KEY`
- `DB_PASSWORD` / `DATABASE_URL`
- `ANTHROPIC_AUTH_TOKEN` or other AI API keys
- `deploy.config.json` (copy from `deploy.config.json.example` locally)

Use:

- `backend/.env.example` for local backend development
- `.env.deploy.example` for Docker production deployment
- `deploy.config.json.example` for remote deploy scripts

## Before Going Public

- Rotate any keys that may have appeared in git history
- Remove production server IPs from local-only deploy scripts
- Do not expose PostgreSQL (`5432`) or the API port (`8000`) directly on the public internet; use HTTPS and a reverse proxy
