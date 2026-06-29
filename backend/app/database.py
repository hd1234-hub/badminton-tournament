from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def sync_player_id_sequence(db_engine=engine) -> None:
    """PostgreSQL: 用户注册/加入俱乐部会手动指定 player.id，需同步自增序列避免冲突"""
    if "postgresql" not in str(db_engine.url):
        return
    with db_engine.connect() as conn:
        conn.execute(text(
            "SELECT setval(pg_get_serial_sequence('players', 'id'), "
            "COALESCE((SELECT MAX(id) FROM players), 1))"
        ))
        conn.commit()


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
