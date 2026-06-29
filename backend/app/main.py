import logging
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text, inspect
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import Base, engine, sync_player_id_sequence
from app.limiter import limiter
from app.routers import auth, clubs, players, competitions, leaderboard, agent, activities, notifications, dashboard, admin
from app.services import admin_service

os.makedirs("data", exist_ok=True)

# 根据环境调整日志级别
log_level = logging.DEBUG if os.getenv("DEBUG") else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/app.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("badminton")


def _backfill_user_created_at():
    """为旧用户补全注册时间、管理员标记"""
    try:
        with engine.connect() as conn:
            if "sqlite" in settings.database_url:
                conn.execute(text("UPDATE users SET created_at = datetime('now') WHERE created_at IS NULL"))
                conn.execute(text("UPDATE users SET is_admin = 0 WHERE is_admin IS NULL"))
            else:
                conn.execute(text("UPDATE users SET created_at = NOW() WHERE created_at IS NULL"))
                conn.execute(text("UPDATE users SET is_admin = false WHERE is_admin IS NULL"))
            conn.commit()
    except Exception as e:
        logger.warning(f"补全 users 字段失败: {e}")


def _sync_admin_users():
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        count = admin_service.sync_all_user_players(db)
        if count:
            logger.info(f"已同步 {count} 个用户昵称到球员记录")
        usernames = [u.strip() for u in settings.admin_usernames.split(",") if u.strip()]
        if usernames:
            admin_service.sync_admin_users(db, usernames)
            logger.info(f"已同步管理员账号: {', '.join(usernames)}")
    finally:
        db.close()


def _auto_migrate():
    """自动检测并添加数据库中缺失的列"""
    inspector = inspect(engine)
    for table_name, table in Base.metadata.tables.items():
        if table_name not in inspector.get_table_names():
            continue
        existing = {c["name"] for c in inspector.get_columns(table_name)}
        for col in table.columns:
            if col.name not in existing:
                col_type = col.type.compile(dialect=engine.dialect)
                nullable = "NOT NULL" if not col.nullable and col.default is None else ""
                try:
                    with engine.connect() as conn:
                        conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type} {nullable}'))
                        conn.commit()
                    logger.info(f"自动迁移: {table_name}.{col.name} ({col_type})")
                except Exception as e:
                    logger.warning(f"迁移 {table_name}.{col.name} 失败: {e}")


def _ensure_competition_club_id_nullable():
    """SQLite 旧库 competitions.club_id 为 NOT NULL，需重建表以支持大厅比赛。"""
    if "sqlite" not in settings.database_url:
        return
    inspector = inspect(engine)
    if "competitions" not in inspector.get_table_names():
        return
    club_col = next((c for c in inspector.get_columns("competitions") if c["name"] == "club_id"), None)
    if not club_col or club_col.get("nullable", True):
        return
    logger.info("自动迁移: competitions.club_id 改为可空（支持大厅比赛）")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE competitions_new (
                id INTEGER NOT NULL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                club_id INTEGER,
                format VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                courts INTEGER,
                scheduled_at DATETIME,
                created_at DATETIME,
                is_public BOOLEAN,
                max_players INTEGER,
                signup_deadline DATETIME
            )
        """))
        conn.execute(text("""
            INSERT INTO competitions_new (
                id, name, club_id, format, status, courts, scheduled_at, created_at,
                is_public, max_players, signup_deadline
            )
            SELECT
                id, name, club_id, format, status, courts, scheduled_at, created_at,
                is_public, max_players, signup_deadline
            FROM competitions
        """))
        conn.execute(text("DROP TABLE competitions"))
        conn.execute(text("ALTER TABLE competitions_new RENAME TO competitions"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("服务启动，初始化数据库...")
    if settings.run_auto_migrate:
        Base.metadata.create_all(bind=engine)
        sync_player_id_sequence()
        _auto_migrate()
        _ensure_competition_club_id_nullable()
        _backfill_user_created_at()
        _sync_admin_users()
    else:
        logger.info("RUN_AUTO_MIGRATE=false，跳过自动建表/迁移；请先执行 Alembic 迁移")
    logger.info("数据库初始化完成")
    yield
    logger.info("服务关闭")


# 创建限流器 - 基于IP地址（与路由共享同一实例）
app = FastAPI(title="Badminton Tournament System", lifespan=lifespan)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"限流触发: {request.client.host if request.client else 'unknown'}")
    return JSONResponse(
        status_code=429,
        content={"detail": "请求过于频繁，请稍后再试"}
    )

# 解析CORS源列表
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if not cors_origins:
    cors_origins = ["http://localhost:5173", "http://localhost:5174"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS允许的域名: {cors_origins}")
logger.info(f"API限流: 每分钟 {settings.max_requests_per_minute} 请求")

app.include_router(auth.router)
app.include_router(clubs.router)
app.include_router(players.router)
app.include_router(competitions.router)
app.include_router(leaderboard.router)
app.include_router(agent.router)
app.include_router(activities.router)
app.include_router(notifications.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    logger.info(
        "%s %s → %s (%.3fs)",
        request.method, request.url.path, response.status_code, elapsed,
    )
    return response


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
