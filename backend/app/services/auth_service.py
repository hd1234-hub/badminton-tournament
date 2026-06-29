import hashlib
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User


def _admin_username_set() -> set[str]:
    return {u.strip() for u in settings.admin_usernames.split(",") if u.strip()}


def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(plain: str, hashed: str) -> bool:
    salt_hex, key_hex = hashed.split(":")
    salt = bytes.fromhex(salt_hex)
    key = bytes.fromhex(key_hex)
    new_key = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, 100000)
    return new_key == key


def create_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def get_user_from_token(token: str, db: Session) -> User | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
        return db.query(User).filter(User.id == user_id).first()
    except (JWTError, ValueError):
        return None


def sync_user_player(db: Session, user: User) -> None:
    from app.services.club_service import _ensure_player
    _ensure_player(db, user)
    db.commit()


def register(db: Session, username: str, password: str, name: str,
             gender: str = "", skill_level: int = 0, birth_year: int = 0, bio: str = "") -> tuple[User, str]:
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError("用户名已存在")
    user = User(
        username=username,
        hashed_password=hash_password(password),
        name=name,
        gender=gender,
        skill_level=skill_level,
        birth_year=birth_year,
        bio=bio,
        is_admin=username in _admin_username_set(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    sync_user_player(db, user)
    return user, create_token(user.id)


def login(db: Session, username: str, password: str) -> tuple[User, str]:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("用户名或密码错误")
    return user, create_token(user.id)


def get_user_stats(db: Session, user_id: int) -> dict:
    from app.models.player import Player
    player = db.query(Player).filter(Player.id == user_id).first()
    if not player:
        return {"win_rate": 0, "total_matches": 0, "wins": 0}
    return {
        "win_rate": player.win_rate or 0,
        "total_matches": player.total_matches or 0,
        "wins": player.wins or 0,
    }


def update_profile(db: Session, user: User, name: str, gender: str,
                   skill_level: int, birth_year: int, bio: str) -> User:
    user.name = name
    user.gender = gender
    user.skill_level = skill_level
    user.birth_year = birth_year
    user.bio = bio
    db.commit()
    db.refresh(user)
    sync_user_player(db, user)
    return user
