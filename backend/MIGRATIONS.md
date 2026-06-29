# Alembic Migrations

## First-time setup

1. Copy `.env.example` to `.env`
2. Ensure `DATABASE_URL` points to target database

## Common commands

```bash
python -m alembic current
python -m alembic revision --autogenerate -m "describe_change"
python -m alembic upgrade head
python -m alembic downgrade -1
```

## Production recommendation

- Set `ENVIRONMENT=production`
- Set `RUN_AUTO_MIGRATE=false`
- Run `python -m alembic upgrade head` before starting API service
