# 羽毛球比赛编排系统 — 第一期实施计划

> **给执行者：** 必须使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 来逐任务实现。步骤用 checkbox (`- [ ]`) 追踪。

**目标：** 搭建羽毛球比赛系统第一期（MVP），包含注册登录、俱乐部管理、八人转编排、手动创建比赛、录比分、比赛看板、排行榜。Agent 功能在第二期叠加。

**架构：** FastAPI 后端 + React 前端，SQLite 数据库。赛制引擎是纯算法模块不依赖 Agent，比赛编排走 Service 层 + REST API。

**技术栈：** Python 3.11+, FastAPI, SQLAlchemy 2.0, SQLite, React 18, TypeScript, Tailwind CSS, Vite

## 全局约束

- Python 版本 >= 3.11
- 数据库文件路径 `./data/badminton.db`，可通过环境变量 `DATABASE_URL` 覆盖
- 所有 API 路由前缀 `/api/v1`
- JWT token 有效期 7 天
- 八人转：8 人 7 轮，每人与其他 7 人各搭档一次
- 比分：21 分制单局（MVP 简化，不做三局两胜）

## 文件结构总览

```
backend/
  app/
    __init__.py              # 空文件，标记为 Python 包
    main.py                  # FastAPI 应用入口，注册路由
    config.py                # 配置类（数据库地址、JWT密钥等）
    database.py              # 数据库引擎 + Session + get_db 依赖
    deps.py                  # 通用依赖（获取当前登录用户等）
    models/                  # 数据库表定义（SQLAlchemy ORM）
      __init__.py
      user.py                # 用户表
      player.py              # 球员表 + 俱乐部成员关联表
      club.py                # 俱乐部表
      competition.py         # 比赛表 + 轮次表 + 对阵表
    schemas/                 # 请求/响应的数据结构（Pydantic）
      __init__.py
      auth.py                # 注册/登录/用户信息
      club.py
      player.py
      competition.py
    routers/                 # API 路由（相当于 Controller）
      __init__.py
      auth.py
      clubs.py
      players.py
      competitions.py
      leaderboard.py
    services/                # 业务逻辑层
      __init__.py
      auth_service.py
      club_service.py
      player_service.py
      competition_service.py
      leaderboard_service.py
      format_engine/         # 赛制引擎（纯算法）
        __init__.py
        base.py              # 抽象基类
        eight_player.py      # 八人转核心算法
  tests/
    __init__.py
    conftest.py              # pytest 夹具（内存数据库 + 测试客户端）
    test_auth.py
    test_clubs.py
    test_eight_player.py     # 赛制引擎测试（最重要）
    test_competitions.py
    test_leaderboard.py
  requirements.txt
  Dockerfile

frontend/
  src/
    App.tsx                  # 路由总配置
    main.tsx                 # React 入口
    index.css                # Tailwind 基础样式
    api/                     # 后端 API 调用封装
      client.ts              # axios 实例（自动带 token）
      auth.ts
      clubs.ts
      competitions.ts
      leaderboard.ts
    types/
      index.ts               # 前端类型定义
    hooks/
      useAuth.ts             # 登录状态管理
      useCompetition.ts      # 比赛数据获取
    components/
      Layout.tsx             # 全局布局（导航栏 + 内容区）
      ProtectedRoute.tsx     # 路由守卫（未登录跳转）
      AgentPanel.tsx         # Agent 对话面板（第二期占位）
    pages/
      LoginPage.tsx
      RegisterPage.tsx
      Dashboard.tsx          # 首页（俱乐部列表）
      ClubPage.tsx           # 俱乐部详情（成员 + 创建比赛入口）
      CreateCompetition.tsx  # 创建比赛（选人 + 配置）
      CompetitionBoard.tsx   # 比赛看板（对阵表 + 录比分）
      ProfilePage.tsx        # 个人主页
      LeaderboardPage.tsx    # 排行榜
  package.json
  vite.config.ts
  tailwind.config.js
  index.html
  Dockerfile
  nginx.conf

docker-compose.yml           # 一键启动前后端
```

---

### Task 1：后端项目骨架

**要创建的文件：** `backend/requirements.txt`, `backend/app/__init__.py`, `backend/app/main.py`, `backend/app/config.py`, `backend/app/database.py`, `backend/tests/__init__.py`, `backend/tests/conftest.py`

**产出：** FastAPI 应用能启动，`/api/v1/health` 返回 ok，测试夹具就绪

- [ ] **步骤 1：创建 requirements.txt**

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
pydantic==2.9.0
pydantic-settings==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
pytest==8.3.0
httpx==0.27.0
```

- [ ] **步骤 2：创建 app/config.py（配置类）**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/badminton.db"
    secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **步骤 3：创建 app/database.py（数据库连接）**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **步骤 4：创建 app/main.py（应用入口）**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

app = FastAPI(title="Badminton Tournament System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
```

- [ ] **步骤 5：创建 tests/conftest.py（测试夹具）**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **步骤 6：安装依赖并验证**

```bash
cd backend && pip install -r requirements.txt
mkdir -p data
pytest -v
```
预期：收集到 0 个测试，无报错。

- [ ] **步骤 7：提交**

```bash
git add backend/
git commit -m "feat: 搭建后端项目骨架 FastAPI + SQLite"
```

---

### Task 2：前端项目骨架

**要创建的文件：** `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tailwind.config.js`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/index.css`, `frontend/src/api/client.ts`, `frontend/src/types/index.ts`

**产出：** React 应用在 `localhost:5173` 跑起来，显示 "Hello Badminton!"，axios 客户端就绪

- [ ] **步骤 1：创建 package.json**

```json
{
  "name": "badminton-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.4",
    "typescript": "^5.5.0",
    "vite": "^5.4.0"
  }
}
```

- [ ] **步骤 2：创建 vite.config.ts**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
```

- [ ] **步骤 3：创建 tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
```

- [ ] **步骤 4：创建 index.html**

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>羽毛球比赛系统</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **步骤 5：创建 src/main.tsx**

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

- [ ] **步骤 6：创建 src/App.tsx**

```tsx
import { Routes, Route } from "react-router-dom";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<div className="p-8 text-2xl">Hello Badminton!</div>} />
    </Routes>
  );
}
```

- [ ] **步骤 7：创建 src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **步骤 8：创建 src/api/client.ts（axios 封装）**

```typescript
import axios from "axios";

const client = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// 请求拦截器：自动带 token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
```

- [ ] **步骤 9：创建 src/types/index.ts（前端类型定义）**

```typescript
export type CompetitionFormat = "eight_player_rotation";

export type CompetitionStatus = "pending" | "in_progress" | "completed";

export interface User {
  id: number;
  username: string;
  name: string;
}

export interface Player {
  id: number;
  name: string;
  level: number;
  handedness: string;
  gender: string;
}

export interface Club {
  id: number;
  name: string;
  owner_id: number;
}

export interface Match {
  id: number;
  round_id: number;
  court: number;
  team_a: number[];
  team_b: number[];
  score_a: number | null;
  score_b: number | null;
}

export interface Round {
  id: number;
  competition_id: number;
  round_number: number;
  matches: Match[];
}

export interface Competition {
  id: number;
  name: string;
  club_id: number;
  format: CompetitionFormat;
  status: CompetitionStatus;
  courts: number;
  scheduled_at: string;
  players: Player[];
  rounds: Round[];
}
```

- [ ] **步骤 10：安装依赖并启动验证**

```bash
cd frontend && npm install && npm run dev
```
预期：浏览器打开 http://localhost:5173 显示 "Hello Badminton!"

- [ ] **步骤 11：提交**

```bash
git add frontend/
git commit -m "feat: 搭建前端项目骨架 React + TypeScript + Tailwind"
```

---

### Task 3：数据库模型

**要创建的文件：** `backend/app/models/__init__.py`, `backend/app/models/user.py`, `backend/app/models/player.py`, `backend/app/models/club.py`, `backend/app/models/competition.py`

**产出：** 完整的数据库表定义，执行后自动建表

- [ ] **步骤 1：创建 app/models/user.py（用户表）**

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    name = Column(String(50), nullable=False)

    owned_clubs = relationship("Club", back_populates="owner")
```

- [ ] **步骤 2：创建 app/models/player.py（球员表 + 俱乐部成员表）**

```python
from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    level = Column(Integer, default=3)       # 水平分档 1-5
    handedness = Column(String(10), default="right")
    gender = Column(String(10), default="male")

    win_rate = Column(Float, default=0.0)
    total_matches = Column(Integer, default=0)
    wins = Column(Integer, default=0)


class ClubMember(Base):
    __tablename__ = "club_members"

    id = Column(Integer, primary_key=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    role = Column(String(20), default="member")

    club = relationship("Club", back_populates="members")
    player = relationship("Player")

    __table_args__ = (UniqueConstraint("club_id", "player_id"),)
```

- [ ] **步骤 3：创建 app/models/club.py（俱乐部表）**

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="owned_clubs")
    members = relationship("ClubMember", back_populates="club", cascade="all, delete-orphan")
```

- [ ] **步骤 4：创建 app/models/competition.py（比赛/轮次/对阵表）**

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    format = Column(String(50), nullable=False, default="eight_player_rotation")
    status = Column(String(20), nullable=False, default="pending")
    courts = Column(Integer, default=2)
    scheduled_at = Column(DateTime, nullable=True)

    rounds = relationship("Round", back_populates="competition", cascade="all, delete-orphan",
                          order_by="Round.round_number")
    competition_players = relationship("CompetitionPlayer", back_populates="competition",
                                       cascade="all, delete-orphan")

    @property
    def players(self):
        """返回参赛球员列表，方便 API 序列化"""
        return [cp.player for cp in self.competition_players] if self.competition_players else []


class CompetitionPlayer(Base):
    __tablename__ = "competition_players"

    id = Column(Integer, primary_key=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    competition = relationship("Competition", back_populates="competition_players")
    player = relationship("Player")


class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    round_number = Column(Integer, nullable=False)

    competition = relationship("Competition", back_populates="rounds")
    matches = relationship("Match", back_populates="round", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    court = Column(Integer, nullable=False)
    team_a = Column(JSON, nullable=False)    # 例如 [1, 2]
    team_b = Column(JSON, nullable=False)    # 例如 [3, 4]
    score_a = Column(Integer, nullable=True)  # null 表示还没录入
    score_b = Column(Integer, nullable=True)

    round = relationship("Round", back_populates="matches")
```

- [ ] **步骤 5：创建 app/models/__init__.py（统一导出）**

```python
from app.models.user import User
from app.models.player import Player, ClubMember
from app.models.club import Club
from app.models.competition import Competition, CompetitionPlayer, Round, Match
```

- [ ] **步骤 6：验证建表**

```bash
cd backend && python -c "
from app.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('Tables created')
"
```
预期：输出 `Tables created`，`data/badminton.db` 文件生成。

- [ ] **步骤 7：提交**

```bash
git add backend/app/models/
git commit -m "feat: 创建所有数据库模型"
```

---

### Task 4：用户认证系统

**要创建的文件：** `backend/app/schemas/auth.py`, `backend/app/services/auth_service.py`, `backend/app/routers/auth.py`, `backend/app/deps.py`, `backend/tests/test_auth.py`

**产出：** 注册、登录、获取当前用户信息三个接口，JWT 认证

- [ ] **步骤 1：先写测试（一定会失败）— backend/tests/test_auth.py**

```python
def test_register(client):
    """测试注册：应该返回 token 和用户信息"""
    resp = client.post("/api/v1/auth/register", json={
        "username": "player1",
        "password": "test123456",
        "name": "张三",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["name"] == "张三"
    assert "token" in data


def test_login(client):
    """测试登录：注册后登录应该成功"""
    client.post("/api/v1/auth/register", json={
        "username": "player2", "password": "test123456", "name": "李四",
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "player2", "password": "test123456",
    })
    assert resp.status_code == 200
    assert "token" in resp.json()


def test_login_wrong_password(client):
    """测试密码错误：应该返回 401"""
    client.post("/api/v1/auth/register", json={
        "username": "player3", "password": "test123456", "name": "王五",
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "player3", "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_me(client):
    """测试获取当前用户：带 token 请求应该返回用户信息"""
    resp = client.post("/api/v1/auth/register", json={
        "username": "player4", "password": "test123456", "name": "赵六",
    })
    token = resp.json()["token"]
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "player4"
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd backend && pytest tests/test_auth.py -v
```
预期：4 个测试全部失败（404 找不到路由）。

- [ ] **步骤 3：创建 app/schemas/auth.py（请求和响应的数据结构）**

```python
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    name: str = Field(min_length=1, max_length=50)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    name: str

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    token: str
    user: UserResponse
```

- [ ] **步骤 4：创建 app/services/auth_service.py（认证业务逻辑）**

```python
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.jwt_expire_days)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def get_user_from_token(token: str, db: Session) -> User | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
        return db.query(User).filter(User.id == user_id).first()
    except (JWTError, ValueError):
        return None


def register(db: Session, username: str, password: str, name: str) -> tuple[User, str]:
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError("用户名已存在")
    user = User(username=username, hashed_password=hash_password(password), name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, create_token(user.id)


def login(db: Session, username: str, password: str) -> tuple[User, str]:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("用户名或密码错误")
    return user, create_token(user.id)
```

- [ ] **步骤 5：创建 app/deps.py（依赖注入：获取当前用户）**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_user_from_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    user = get_user_from_token(credentials.credentials, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 token")
    return user
```

- [ ] **步骤 6：创建 app/routers/auth.py（认证路由）**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user, token = auth_service.register(db, req.username, req.password, req.name)
        return {"token": token, "user": UserResponse.model_validate(user)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    try:
        user, token = auth_service.login(db, req.username, req.password)
        return {"token": token, "user": UserResponse.model_validate(user)}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
```

- [ ] **步骤 7：在 main.py 中注册路由**

在 `app/main.py` 中加上：
```python
from app.routers import auth
app.include_router(auth.router)
```

- [ ] **步骤 8：运行测试**

```bash
cd backend && pytest tests/test_auth.py -v
```
预期：4 个测试全部通过。

- [ ] **步骤 9：提交**

```bash
git add backend/app/schemas/ backend/app/services/ backend/app/routers/ backend/app/deps.py backend/app/main.py backend/tests/test_auth.py
git commit -m "feat: 实现用户注册、登录、JWT 认证"
```

---

### Task 5：俱乐部和球员管理

**要创建的文件：** `backend/app/schemas/club.py`, `backend/app/schemas/player.py`, `backend/app/services/club_service.py`, `backend/app/services/player_service.py`, `backend/app/routers/clubs.py`, `backend/app/routers/players.py`, `backend/tests/test_clubs.py`

**产出：** 创建俱乐部、列出俱乐部、加入俱乐部、创建球员、列出球员

- [ ] **步骤 1：先写测试 — backend/tests/test_clubs.py**

```python
def register_user(client):
    """辅助函数：注册并返回 token"""
    return client.post("/api/v1/auth/register", json={
        "username": "clubtest", "password": "test123456", "name": "测试",
    }).json()["token"]


def test_create_club(client):
    """测试创建俱乐部"""
    token = register_user(client)
    resp = client.post("/api/v1/clubs", json={"name": "阳光羽毛球俱乐部"},
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "阳光羽毛球俱乐部"
    assert data["owner_id"] is not None


def test_list_clubs(client):
    """测试列出用户的俱乐部"""
    token = register_user(client)
    client.post("/api/v1/clubs", json={"name": "阳光羽毛球俱乐部"},
                headers={"Authorization": f"Bearer {token}"})
    resp = client.get("/api/v1/clubs", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_join_club(client):
    """测试加入俱乐部"""
    token = register_user(client)
    club = client.post("/api/v1/clubs", json={"name": "测试俱乐部"},
                       headers={"Authorization": f"Bearer {token}"}).json()
    resp = client.post(f"/api/v1/clubs/{club['id']}/join",
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_get_club_players(client):
    """测试获取俱乐部成员列表"""
    token = register_user(client)
    club = client.post("/api/v1/clubs", json={"name": "测试俱乐部"},
                       headers={"Authorization": f"Bearer {token}"}).json()
    client.post(f"/api/v1/clubs/{club['id']}/join",
                headers={"Authorization": f"Bearer {token}"})
    resp = client.get(f"/api/v1/clubs/{club['id']}/players",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd backend && pytest tests/test_clubs.py -v
```
预期：4 个测试全部失败（404）。

- [ ] **步骤 3：创建 schemas**

`app/schemas/club.py`:
```python
from pydantic import BaseModel, Field


class ClubCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class ClubResponse(BaseModel):
    id: int
    name: str
    owner_id: int

    class Config:
        from_attributes = True
```

`app/schemas/player.py`:
```python
from pydantic import BaseModel, Field


class PlayerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    level: int = Field(default=3, ge=1, le=5)
    handedness: str = Field(default="right")
    gender: str = Field(default="male")


class PlayerResponse(BaseModel):
    id: int
    name: str
    level: int
    handedness: str
    gender: str
    win_rate: float
    total_matches: int
    wins: int

    class Config:
        from_attributes = True
```

- [ ] **步骤 4：创建 services**

`app/services/club_service.py`:
```python
from sqlalchemy.orm import Session

from app.models.club import Club
from app.models.player import ClubMember, Player
from app.models.user import User


def create_club(db: Session, user: User, name: str) -> Club:
    club = Club(name=name, owner_id=user.id)
    db.add(club)
    db.commit()
    db.refresh(club)
    return club


def list_user_clubs(db: Session, user: User) -> list[Club]:
    owned = db.query(Club).filter(Club.owner_id == user.id).all()
    member_club_ids = db.query(ClubMember.club_id).filter(ClubMember.player_id == user.id).distinct()
    joined = db.query(Club).filter(Club.id.in_(member_club_ids)).all()
    return owned + joined


def join_club(db: Session, club_id: int, user: User) -> ClubMember:
    existing = db.query(ClubMember).filter(
        ClubMember.club_id == club_id, ClubMember.player_id == user.id
    ).first()
    if existing:
        raise ValueError("你已加入该俱乐部")
    member = ClubMember(club_id=club_id, player_id=user.id, role="member")
    db.add(member)
    db.commit()
    return member


def get_club_players(db: Session, club_id: int) -> list[Player]:
    return db.query(Player).join(ClubMember).filter(ClubMember.club_id == club_id).all()
```

`app/services/player_service.py`:
```python
from sqlalchemy.orm import Session

from app.models.player import Player


def create_player(db: Session, name: str, level: int, handedness: str, gender: str) -> Player:
    player = Player(name=name, level=level, handedness=handedness, gender=gender)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def list_players(db: Session) -> list[Player]:
    return db.query(Player).all()
```

- [ ] **步骤 5：创建 routers**

`app/routers/clubs.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.club import ClubCreate, ClubResponse
from app.schemas.player import PlayerResponse
from app.services import club_service

router = APIRouter(prefix="/api/v1/clubs", tags=["clubs"])


@router.post("", response_model=ClubResponse)
def create(req: ClubCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return club_service.create_club(db, user, req.name)


@router.get("", response_model=list[ClubResponse])
def list_clubs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return club_service.list_user_clubs(db, user)


@router.post("/{club_id}/join")
def join(club_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        club_service.join_club(db, club_id, user)
        return {"message": "已加入俱乐部"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{club_id}/players", response_model=list[PlayerResponse])
def get_players(club_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return club_service.get_club_players(db, club_id)
```

`app/routers/players.py`:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.player import PlayerCreate, PlayerResponse
from app.services import player_service

router = APIRouter(prefix="/api/v1/players", tags=["players"])


@router.post("", response_model=PlayerResponse)
def create(req: PlayerCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return player_service.create_player(db, req.name, req.level, req.handedness, req.gender)


@router.get("", response_model=list[PlayerResponse])
def list_players(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return player_service.list_players(db)
```

- [ ] **步骤 6：在 main.py 注册路由**

```python
from app.routers import auth, clubs, players
app.include_router(clubs.router)
app.include_router(players.router)
```

- [ ] **步骤 7：运行测试**

```bash
cd backend && pytest tests/test_clubs.py -v
```
预期：4 个测试全部通过。

- [ ] **步骤 8：提交**

```bash
git add backend/app/schemas/club.py backend/app/schemas/player.py backend/app/services/club_service.py backend/app/services/player_service.py backend/app/routers/clubs.py backend/app/routers/players.py backend/app/main.py backend/tests/test_clubs.py
git commit -m "feat: 实现俱乐部管理和球员增删查"
```

---

### Task 6：八人转赛制引擎（核心算法）

**要创建的文件：** `backend/app/services/format_engine/__init__.py`, `backend/app/services/format_engine/base.py`, `backend/app/services/format_engine/eight_player.py`, `backend/tests/test_eight_player.py`

**产出：** 八人转对阵生成函数，纯算法，不依赖数据库

- [ ] **步骤 1：先写测试 — backend/tests/test_eight_player.py**

```python
import pytest
from app.services.format_engine.eight_player import generate_eight_player_rotation


def test_生成7轮():
    """8人转应该生成7轮比赛"""
    players = [1, 2, 3, 4, 5, 6, 7, 8]
    rounds = generate_eight_player_rotation(players, courts=2)
    assert len(rounds) == 7


def test_2场地每轮2场():
    """2个场地时每轮应该有2场比赛"""
    players = [1, 2, 3, 4, 5, 6, 7, 8]
    rounds = generate_eight_player_rotation(players, courts=2)
    for rnd in rounds:
        assert len(rnd) == 2


def test_每轮所有球员都上场():
    """每轮所有8个球员都必须出现在对阵中"""
    players = [1, 2, 3, 4, 5, 6, 7, 8]
    rounds = generate_eight_player_rotation(players, courts=2)
    for rnd in rounds:
        in_round = []
        for m in rnd:
            in_round.extend(m["team_a"])
            in_round.extend(m["team_b"])
        assert sorted(in_round) == players


def test_每人搭档恰好一次():
    """每人与其他7人恰好各搭档一次"""
    players = list(range(1, 9))
    rounds = generate_eight_player_rotation(players, courts=2)
    partners = {}
    for rnd in rounds:
        for m in rnd:
            for side in [m["team_a"], m["team_b"]]:
                p1, p2 = sorted(side)
                partners.setdefault(p1, {})[p2] = partners.get(p1, {}).get(p2, 0) + 1
    for p in range(1, 9):
        for q in range(p + 1, 9):
            assert partners[p].get(q, 0) == 1, f"球员 {p} 和 {q} 搭档了 {partners[p].get(q, 0)} 次"


def test_每轮每人至少打一场():
    """每轮每个人至少出现在一场比赛中"""
    players = list(range(1, 9))
    rounds = generate_eight_player_rotation(players, courts=2)
    for rnd in rounds:
        appeared = set()
        for m in rnd:
            appeared.update(m["team_a"])
            appeared.update(m["team_b"])
        assert appeared == set(range(1, 9))


def test_人数不对报错():
    """不是8个人应该抛出错误"""
    with pytest.raises(ValueError, match="需要恰好 8 名球员"):
        generate_eight_player_rotation([1, 2, 3], courts=2)


def test_场地数不对报错():
    """场地数不是1或2或4应该报错"""
    with pytest.raises(ValueError):
        generate_eight_player_rotation(list(range(1, 9)), courts=3)


def test_4场地支持():
    """4个场地时每轮4场比赛"""
    players = list(range(1, 9))
    rounds = generate_eight_player_rotation(players, courts=4)
    assert len(rounds) == 7
    for rnd in rounds:
        assert len(rnd) == 4
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd backend && pytest tests/test_eight_player.py -v
```
预期：全部失败（ImportError，文件不存在）。

- [ ] **步骤 3：创建抽象基类 — app/services/format_engine/base.py**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MatchSlot:
    court: int
    team_a: list[int]
    team_b: list[int]


class FormatEngine(ABC):
    @abstractmethod
    def generate(self, players: list[int], courts: int) -> list[list[MatchSlot]]: ...
```

- [ ] **步骤 4：实现八人转算法 — app/services/format_engine/eight_player.py**

```python
from app.services.format_engine.base import MatchSlot

# 八人转标准对阵矩阵（7轮，每轮2组双打）
# 数学上保证每人与其他7人恰好各搭档一次
EIGHT_PLAYER_MATRIX = [
    [[(1, 2), (3, 4)], [(5, 6), (7, 8)]],
    [[(1, 3), (5, 7)], [(2, 4), (6, 8)]],
    [[(1, 4), (6, 7)], [(2, 3), (5, 8)]],
    [[(1, 5), (2, 6)], [(3, 7), (4, 8)]],
    [[(1, 6), (4, 5)], [(2, 7), (3, 8)]],
    [[(1, 7), (2, 8)], [(3, 5), (4, 6)]],
    [[(1, 8), (3, 6)], [(4, 7), (2, 5)]],
]


def generate_eight_player_rotation(players: list[int], courts: int) -> list[list[dict]]:
    """
    生成八人转对阵表。

    参数:
        players: 8个球员ID的列表
        courts: 场地数（1 或 2 或 4）

    返回:
        [[{court, round_number, team_a, team_b}, ...], ...]  共7轮
    """
    if len(players) != 8:
        raise ValueError("需要恰好 8 名球员")
    if courts not in (1, 2, 4):
        raise ValueError("场地数必须是 1、2 或 4")

    result = []
    for round_number, round_template in enumerate(EIGHT_PLAYER_MATRIX):
        round_matches = []
        for court_index, ((a1, a2), (b1, b2)) in enumerate(round_template):
            if court_index >= courts:
                break
            round_matches.append({
                "court": court_index + 1,
                "round_number": round_number + 1,
                "team_a": [players[a1 - 1], players[a2 - 1]],
                "team_b": [players[b1 - 1], players[b2 - 1]],
            })
        result.append(round_matches)
    return result
```

- [ ] **步骤 5：创建 __init__.py**

```python
from app.services.format_engine.eight_player import generate_eight_player_rotation

__all__ = ["generate_eight_player_rotation"]
```

- [ ] **步骤 6：运行测试**

```bash
cd backend && pytest tests/test_eight_player.py -v
```
预期：8 个测试全部通过。

- [ ] **步骤 7：提交**

```bash
git add backend/app/services/format_engine/ backend/tests/test_eight_player.py
git commit -m "feat: 实现八人转赛制引擎核心算法"
```

---

### Task 7：比赛服务 + 录比分

**要创建的文件：** `backend/app/schemas/competition.py`, `backend/app/services/competition_service.py`, `backend/app/routers/competitions.py`, `backend/tests/test_competitions.py`

**产出：** 创建比赛、开始比赛、录比分、查看比赛详情

- [ ] **步骤 1：先写测试 — backend/tests/test_competitions.py**

```python
def register_and_create_club(client):
    """辅助函数：注册用户并创建俱乐部"""
    resp = client.post("/api/v1/auth/register", json={
        "username": "comptest", "password": "test123456", "name": "比赛测试",
    })
    token = resp.json()["token"]
    club = client.post("/api/v1/clubs", json={"name": "测试俱乐部"},
                       headers={"Authorization": f"Bearer {token}"}).json()
    return token, club


def add_players(client, token, club_id, count=8):
    """辅助函数：批量创建球员并加入俱乐部"""
    pids = []
    for i in range(count):
        resp = client.post("/api/v1/players", json={"name": f"球员{i+1}"},
                           headers={"Authorization": f"Bearer {token}"})
        pid = resp.json()["id"]
        client.post(f"/api/v1/clubs/{club_id}/join",
                    headers={"Authorization": f"Bearer {token}"})
        pids.append(pid)
    return pids


def test_create_eight_player_competition(client):
    """测试创建八人转比赛：应该生成7轮对阵"""
    token, club = register_and_create_club(client)
    add_players(client, token, club["id"])
    resp = client.post("/api/v1/competitions", json={
        "name": "周日八人转",
        "club_id": club["id"],
        "format": "eight_player_rotation",
        "courts": 2,
        "player_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "周日八人转"
    assert len(data["rounds"]) == 7
    assert data["status"] == "pending"


def test_start_competition(client):
    """测试开始比赛：状态变为 in_progress"""
    token, club = register_and_create_club(client)
    add_players(client, token, club["id"])
    comp = client.post("/api/v1/competitions", json={
        "name": "周日八人转", "club_id": club["id"],
        "format": "eight_player_rotation", "courts": 2,
        "player_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    }, headers={"Authorization": f"Bearer {token}"}).json()

    resp = client.patch(f"/api/v1/competitions/{comp['id']}/start",
                        headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_record_score(client):
    """测试录比分：应该成功记录并返回比分"""
    token, club = register_and_create_club(client)
    add_players(client, token, club["id"])
    comp = client.post("/api/v1/competitions", json={
        "name": "周日八人转", "club_id": club["id"],
        "format": "eight_player_rotation", "courts": 2,
        "player_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    }, headers={"Authorization": f"Bearer {token}"}).json()
    client.patch(f"/api/v1/competitions/{comp['id']}/start",
                 headers={"Authorization": f"Bearer {token}"})

    match_id = comp["rounds"][0]["matches"][0]["id"]
    resp = client.post(f"/api/v1/matches/{match_id}/score", json={
        "score_a": 21, "score_b": 15,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["score_a"] == 21
    assert resp.json()["score_b"] == 15


def test_duplicate_score_rejected(client):
    """测试重复录比分：应该被拒绝"""
    token, club = register_and_create_club(client)
    add_players(client, token, club["id"])
    comp = client.post("/api/v1/competitions", json={
        "name": "周日八人转", "club_id": club["id"],
        "format": "eight_player_rotation", "courts": 2,
        "player_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    }, headers={"Authorization": f"Bearer {token}"}).json()
    client.patch(f"/api/v1/competitions/{comp['id']}/start",
                 headers={"Authorization": f"Bearer {token}"})

    match_id = comp["rounds"][0]["matches"][0]["id"]
    client.post(f"/api/v1/matches/{match_id}/score", json={
        "score_a": 21, "score_b": 15,
    }, headers={"Authorization": f"Bearer {token}"})
    resp = client.post(f"/api/v1/matches/{match_id}/score", json={
        "score_a": 19, "score_b": 21,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd backend && pytest tests/test_competitions.py -v
```
预期：4 个测试全部失败（404）。

- [ ] **步骤 3：创建 schemas — app/schemas/competition.py**

```python
from datetime import datetime
from pydantic import BaseModel, Field


class CreateCompetitionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    club_id: int
    format: str = "eight_player_rotation"
    courts: int = Field(default=2, ge=1, le=4)
    player_ids: list[int] = Field(min_length=2)
    scheduled_at: datetime | None = None


class ScoreRequest(BaseModel):
    score_a: int = Field(ge=0, le=30)
    score_b: int = Field(ge=0, le=30)


class MatchResponse(BaseModel):
    id: int
    round_id: int
    court: int
    team_a: list[int]
    team_b: list[int]
    score_a: int | None
    score_b: int | None

    class Config:
        from_attributes = True


class RoundResponse(BaseModel):
    id: int
    competition_id: int
    round_number: int
    matches: list[MatchResponse]

    class Config:
        from_attributes = True


class CompetitionResponse(BaseModel):
    id: int
    name: str
    club_id: int
    format: str
    status: str
    courts: int
    scheduled_at: datetime | None
    players: list[dict]
    rounds: list[RoundResponse]

    class Config:
        from_attributes = True
```

- [ ] **步骤 4：创建服务 — app/services/competition_service.py**

```python
from sqlalchemy.orm import Session, joinedload

from app.models.competition import Competition, CompetitionPlayer, Match, Round
from app.models.player import Player
from app.services.format_engine.eight_player import generate_eight_player_rotation


def create_competition(
    db: Session, name: str, club_id: int, format: str,
    courts: int, player_ids: list[int], scheduled_at,
) -> Competition:
    comp = Competition(
        name=name, club_id=club_id, format=format,
        courts=courts, scheduled_at=scheduled_at, status="pending",
    )
    db.add(comp)
    db.flush()

    for pid in player_ids:
        db.add(CompetitionPlayer(competition_id=comp.id, player_id=pid))

    rounds_data = generate_eight_player_rotation(player_ids, courts)
    for rnd_matches in rounds_data:
        rnd = Round(competition_id=comp.id, round_number=rnd_matches[0]["round_number"])
        db.add(rnd)
        db.flush()
        for m in rnd_matches:
            db.add(Match(
                round_id=rnd.id, court=m["court"],
                team_a=m["team_a"], team_b=m["team_b"],
            ))

    db.commit()
    return _load_competition(db, comp.id)


def start_competition(db: Session, comp_id: int) -> Competition:
    comp = _get_or_404(db, comp_id)
    if comp.status != "pending":
        raise ValueError("比赛已经开始或已结束")
    comp.status = "in_progress"
    db.commit()
    return _load_competition(db, comp_id)


def record_score(db: Session, match_id: int, score_a: int, score_b: int) -> Match:
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise ValueError("对阵不存在")
    if match.score_a is not None:
        raise ValueError("该场比分已录入")
    match.score_a = score_a
    match.score_b = score_b
    db.commit()
    _update_player_stats(db, match)
    return match


def get_competition(db: Session, comp_id: int) -> Competition:
    return _load_competition(db, comp_id)


def _load_competition(db: Session, comp_id: int) -> Competition:
    comp = db.query(Competition).options(
        joinedload(Competition.rounds).joinedload(Round.matches),
        joinedload(Competition.competition_players).joinedload(CompetitionPlayer.player),
    ).filter(Competition.id == comp_id).first()
    if not comp:
        raise ValueError("比赛不存在")
    return comp


def _get_or_404(db: Session, comp_id: int) -> Competition:
    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    if not comp:
        raise ValueError("比赛不存在")
    return comp


def _update_player_stats(db: Session, match: Match):
    """录入比分后更新球员胜率统计"""
    if match.score_a is None:
        return
    team_a_ids = match.team_a
    team_b_ids = match.team_b
    a_won = match.score_a > match.score_b
    for pid in team_a_ids + team_b_ids:
        player = db.query(Player).filter(Player.id == pid).first()
        if player:
            player.total_matches = (player.total_matches or 0) + 1
            if (pid in team_a_ids and a_won) or (pid in team_b_ids and not a_won):
                player.wins = (player.wins or 0) + 1
            player.win_rate = player.wins / player.total_matches if player.total_matches > 0 else 0
            db.add(player)
    db.commit()
```

- [ ] **步骤 5：创建路由 — app/routers/competitions.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.competition import (
    CompetitionResponse, CreateCompetitionRequest, MatchResponse, ScoreRequest,
)
from app.services import competition_service

router = APIRouter(prefix="/api/v1", tags=["competitions"])


@router.post("/competitions", response_model=CompetitionResponse)
def create(req: CreateCompetitionRequest, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    try:
        return competition_service.create_competition(
            db, req.name, req.club_id, req.format,
            req.courts, req.player_ids, req.scheduled_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/competitions/{comp_id}", response_model=CompetitionResponse)
def get(comp_id: int, user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    try:
        return competition_service.get_competition(db, comp_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/competitions/{comp_id}/start", response_model=CompetitionResponse)
def start(comp_id: int, user: User = Depends(get_current_user),
          db: Session = Depends(get_db)):
    try:
        return competition_service.start_competition(db, comp_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/matches/{match_id}/score", response_model=MatchResponse)
def record_score(match_id: int, req: ScoreRequest,
                 user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    try:
        return competition_service.record_score(db, match_id, req.score_a, req.score_b)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **步骤 6：在 main.py 注册路由**

```python
from app.routers import auth, clubs, players, competitions
app.include_router(competitions.router)
```

- [ ] **步骤 7：运行测试**

```bash
cd backend && pytest tests/test_competitions.py -v
```
预期：4 个测试全部通过。

- [ ] **步骤 8：提交**

```bash
git add backend/app/schemas/competition.py backend/app/services/competition_service.py backend/app/routers/competitions.py backend/app/main.py backend/tests/test_competitions.py
git commit -m "feat: 实现比赛创建、开始、录比分功能"
```

---

### Task 8：排行榜服务

**要创建的文件：** `backend/app/services/leaderboard_service.py`, `backend/app/routers/leaderboard.py`, `backend/tests/test_leaderboard.py`

**产出：** 俱乐部排行榜接口，按胜率降序排列

- [ ] **步骤 1：先写测试 — backend/tests/test_leaderboard.py**

```python
from tests.test_competitions import register_and_create_club, add_players


def test_leaderboard(client):
    """测试排行榜：应该返回8名球员的数据"""
    token, club = register_and_create_club(client)
    add_players(client, token, club["id"])
    comp = client.post("/api/v1/competitions", json={
        "name": "周日八人转", "club_id": club["id"],
        "format": "eight_player_rotation", "courts": 2,
        "player_ids": [1, 2, 3, 4, 5, 6, 7, 8],
    }, headers={"Authorization": f"Bearer {token}"}).json()
    client.patch(f"/api/v1/competitions/{comp['id']}/start",
                 headers={"Authorization": f"Bearer {token}"})

    resp = client.get(f"/api/v1/leaderboard?club_id={club['id']}",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 8
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd backend && pytest tests/test_leaderboard.py -v
```
预期：失败（404）。

- [ ] **步骤 3：创建服务 — app/services/leaderboard_service.py**

```python
from sqlalchemy.orm import Session

from app.models.player import ClubMember, Player


def get_leaderboard(db: Session, club_id: int) -> list[dict]:
    player_ids = db.query(ClubMember.player_id).filter(ClubMember.club_id == club_id).distinct()
    players = db.query(Player).filter(Player.id.in_(player_ids)).order_by(
        Player.win_rate.desc(), Player.wins.desc()
    ).all()

    return [
        {
            "id": p.id, "name": p.name, "level": p.level,
            "win_rate": p.win_rate or 0,
            "total_matches": p.total_matches or 0,
            "wins": p.wins or 0,
        }
        for p in players
    ]
```

- [ ] **步骤 4：创建路由 — app/routers/leaderboard.py**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services import leaderboard_service

router = APIRouter(prefix="/api/v1", tags=["leaderboard"])


@router.get("/leaderboard")
def get_leaderboard(club_id: int = Query(...), user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return leaderboard_service.get_leaderboard(db, club_id)
```

- [ ] **步骤 5：在 main.py 注册路由**

```python
from app.routers import auth, clubs, players, competitions, leaderboard
app.include_router(leaderboard.router)
```

- [ ] **步骤 6：运行测试**

```bash
cd backend && pytest tests/test_leaderboard.py -v
```
预期：通过。

- [ ] **步骤 7：提交**

```bash
git add backend/app/services/leaderboard_service.py backend/app/routers/leaderboard.py backend/app/main.py backend/tests/test_leaderboard.py
git commit -m "feat: 实现俱乐部排行榜接口"
```

---

### Task 9：前端登录注册 + 路由守卫

**要创建的文件：** `frontend/src/api/auth.ts`, `frontend/src/hooks/useAuth.ts`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/RegisterPage.tsx`, `frontend/src/components/Layout.tsx`, `frontend/src/components/ProtectedRoute.tsx`

**产出：** 完整的登录注册页面，未登录自动跳转登录页

- [ ] **步骤 1：创建 auth API — frontend/src/api/auth.ts**

```typescript
import client from "./client";

export interface AuthResponse {
  token: string;
  user: { id: number; username: string; name: string };
}

export async function register(username: string, password: string, name: string): Promise<AuthResponse> {
  const { data } = await client.post("/auth/register", { username, password, name });
  return data;
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const { data } = await client.post("/auth/login", { username, password });
  return data;
}

export async function me() {
  const { data } = await client.get("/auth/me");
  return data;
}
```

- [ ] **步骤 2：创建 useAuth hook — frontend/src/hooks/useAuth.ts**

```typescript
import { useState, useEffect, createContext, useContext } from "react";
import * as authApi from "../api/auth";

interface AuthState {
  user: { id: number; username: string; name: string } | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, name: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);

export function useAuthProvider(): AuthState {
  const [user, setUser] = useState<AuthState["user"]>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      authApi.me().then(setUser).catch(() => localStorage.removeItem("token")).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  return {
    user, loading,
    login: async (username, password) => {
      const res = await authApi.login(username, password);
      localStorage.setItem("token", res.token);
      setUser(res.user);
    },
    register: async (username, password, name) => {
      const res = await authApi.register(username, password, name);
      localStorage.setItem("token", res.token);
      setUser(res.user);
    },
    logout: () => { localStorage.removeItem("token"); setUser(null); },
  };
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
```

- [ ] **步骤 3：创建 LoginPage — frontend/src/pages/LoginPage.tsx**

```tsx
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login(username, password);
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail || "登录失败");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold mb-6 text-center">登录</h1>
        {error && <div className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</div>}
        <input value={username} onChange={e => setUsername(e.target.value)}
               placeholder="用户名" className="w-full border p-2 rounded mb-3" required />
        <input type="password" value={password} onChange={e => setPassword(e.target.value)}
               placeholder="密码" className="w-full border p-2 rounded mb-4" required />
        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
          登录
        </button>
        <p className="text-center mt-4 text-sm text-gray-600">
          还没有账号？<Link to="/register" className="text-blue-600">注册</Link>
        </p>
      </form>
    </div>
  );
}
```

- [ ] **步骤 4：创建 RegisterPage — frontend/src/pages/RegisterPage.tsx**

```tsx
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function RegisterPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await register(username, password, name);
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail || "注册失败");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold mb-6 text-center">注册</h1>
        {error && <div className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</div>}
        <input value={name} onChange={e => setName(e.target.value)}
               placeholder="姓名" className="w-full border p-2 rounded mb-3" required />
        <input value={username} onChange={e => setUsername(e.target.value)}
               placeholder="用户名" className="w-full border p-2 rounded mb-3" required />
        <input type="password" value={password} onChange={e => setPassword(e.target.value)}
               placeholder="密码 (最少6位)" className="w-full border p-2 rounded mb-4" required />
        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
          注册
        </button>
        <p className="text-center mt-4 text-sm text-gray-600">
          已有账号？<Link to="/login" className="text-blue-600">登录</Link>
        </p>
      </form>
    </div>
  );
}
```

- [ ] **步骤 5：创建 ProtectedRoute — frontend/src/components/ProtectedRoute.tsx**

```tsx
import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-center">加载中...</div>;
  if (!user) return <Navigate to="/login" />;
  return <>{children}</>;
}
```

- [ ] **步骤 6：创建 Layout — frontend/src/components/Layout.tsx**

```tsx
import { Outlet, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm px-6 py-3 flex justify-between items-center">
        <Link to="/" className="text-xl font-bold text-blue-600">🏸 羽毛球</Link>
        <div className="flex items-center gap-4">
          <Link to="/leaderboard" className="text-gray-600 hover:text-blue-600">排行榜</Link>
          <Link to="/profile" className="text-gray-600 hover:text-blue-600">我的</Link>
          <span className="text-gray-600">{user?.name}</span>
          <button onClick={() => { logout(); navigate("/login"); }}
                  className="text-sm text-red-500 hover:underline">退出</button>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto p-4">
        <Outlet />
      </main>
    </div>
  );
}
```

- [ ] **步骤 7：更新 App.tsx**

```tsx
import { Routes, Route } from "react-router-dom";
import { useAuthProvider, AuthContext } from "./hooks/useAuth";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import Dashboard from "./pages/Dashboard";

export default function App() {
  const auth = useAuthProvider();

  return (
    <AuthContext.Provider value={auth}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route path="/" element={<Dashboard />} />
        </Route>
      </Routes>
    </AuthContext.Provider>
  );
}
```

- [ ] **步骤 8：验证**

启动后端 + 前端，打开 http://localhost:5173，确认自动跳转到登录页，注册后跳转到首页。

- [ ] **步骤 9：提交**

```bash
git add frontend/src/api/auth.ts frontend/src/hooks/useAuth.ts frontend/src/pages/LoginPage.tsx frontend/src/pages/RegisterPage.tsx frontend/src/components/Layout.tsx frontend/src/components/ProtectedRoute.tsx frontend/src/App.tsx
git commit -m "feat: 实现登录注册页面和路由守卫"
```

---

### Task 10：前端首页（仪表盘）+ 俱乐部页

**要创建的文件：** `frontend/src/api/clubs.ts`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/ClubPage.tsx`

**产出：** 首页显示俱乐部列表可创建，俱乐部页显示成员和创建比赛入口

- [ ] **步骤 1：创建 clubs API — frontend/src/api/clubs.ts**

```typescript
import client from "./client";
import type { Club, Player } from "../types";

export async function listClubs(): Promise<Club[]> {
  const { data } = await client.get("/clubs");
  return data;
}

export async function createClub(name: string): Promise<Club> {
  const { data } = await client.post("/clubs", { name });
  return data;
}

export async function getClubPlayers(clubId: number): Promise<Player[]> {
  const { data } = await client.get(`/clubs/${clubId}/players`);
  return data;
}
```

- [ ] **步骤 2：创建 Dashboard — frontend/src/pages/Dashboard.tsx**

```tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Club } from "../types";
import * as clubsApi from "../api/clubs";

export default function Dashboard() {
  const [clubs, setClubs] = useState<Club[]>([]);
  const [newName, setNewName] = useState("");

  const load = () => clubsApi.listClubs().then(setClubs);
  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await clubsApi.createClub(newName);
    setNewName("");
    load();
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleCreate} className="flex gap-2">
        <input value={newName} onChange={e => setNewName(e.target.value)}
               placeholder="新建俱乐部名称" className="border p-2 rounded flex-1" required />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">创建</button>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {clubs.map(club => (
          <Link key={club.id} to={`/clubs/${club.id}`}
                className="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
            <h2 className="text-lg font-semibold">{club.name}</h2>
          </Link>
        ))}
        {clubs.length === 0 && <p className="text-gray-500">暂无俱乐部，创建一个吧</p>}
      </div>
    </div>
  );
}
```

- [ ] **步骤 3：创建 ClubPage — frontend/src/pages/ClubPage.tsx**

```tsx
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import type { Player } from "../types";
import * as clubsApi from "../api/clubs";

export default function ClubPage() {
  const { id } = useParams<{ id: string }>();
  const [players, setPlayers] = useState<Player[]>([]);

  useEffect(() => {
    clubsApi.getClubPlayers(Number(id)).then(setPlayers);
  }, [id]);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">俱乐部成员</h1>
        <Link to={`/clubs/${id}/create-competition`}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">创建比赛</Link>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {players.map(p => (
          <div key={p.id} className="bg-white p-4 rounded shadow flex justify-between items-center">
            <span className="font-medium">{p.name}</span>
            <span className="text-sm text-gray-500">Lv.{p.level}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **步骤 4：更新 App.tsx 路由**

加上：
```tsx
import ClubPage from "./pages/ClubPage";
// 在受保护路由组里加上：
<Route path="/clubs/:id" element={<ClubPage />} />
```

- [ ] **步骤 5：手动验证**

启动项目，创建俱乐部，点进去看成员列表。

- [ ] **步骤 6：提交**

```bash
git add frontend/src/api/clubs.ts frontend/src/pages/Dashboard.tsx frontend/src/pages/ClubPage.tsx frontend/src/App.tsx
git commit -m "feat: 实现首页仪表盘和俱乐部详情页"
```

---

### Task 11：前端比赛创建 + 比赛看板

**要创建的文件：** `frontend/src/api/competitions.ts`, `frontend/src/hooks/useCompetition.ts`, `frontend/src/pages/CreateCompetition.tsx`, `frontend/src/pages/CompetitionBoard.tsx`

**产出：** 创建八人转比赛页面（选人 + 配置），比赛看板（对阵表 + 录比分弹窗）

- [ ] **步骤 1：创建 competitions API — frontend/src/api/competitions.ts**

```typescript
import client from "./client";
import type { Competition } from "../types";

export async function createCompetition(req: {
  name: string; club_id: number; format: string; courts: number; player_ids: number[];
}): Promise<Competition> {
  const { data } = await client.post("/competitions", req);
  return data;
}

export async function getCompetition(id: number): Promise<Competition> {
  const { data } = await client.get(`/competitions/${id}`);
  return data;
}

export async function startCompetition(id: number): Promise<Competition> {
  const { data } = await client.patch(`/competitions/${id}/start`);
  return data;
}

export async function recordScore(matchId: number, scoreA: number, scoreB: number) {
  const { data } = await client.post(`/matches/${matchId}/score`, { score_a: scoreA, score_b: scoreB });
  return data;
}
```

- [ ] **步骤 2：创建 useCompetition hook — frontend/src/hooks/useCompetition.ts**

```typescript
import { useState, useEffect, useCallback } from "react";
import type { Competition } from "../types";
import * as compApi from "../api/competitions";

export function useCompetition(id: number | undefined) {
  const [comp, setComp] = useState<Competition | null>(null);

  const refresh = useCallback(() => {
    if (id) compApi.getCompetition(id).then(setComp);
  }, [id]);

  useEffect(() => { refresh(); }, [refresh]);

  return { comp, refresh };
}
```

- [ ] **步骤 3：创建 CreateCompetition — frontend/src/pages/CreateCompetition.tsx**

```tsx
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type { Player } from "../types";
import * as clubsApi from "../api/clubs";
import * as compApi from "../api/competitions";

export default function CreateCompetition() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [players, setPlayers] = useState<Player[]>([]);
  const [name, setName] = useState("");
  const [courts, setCourts] = useState(2);
  const [selected, setSelected] = useState<number[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    clubsApi.getClubPlayers(Number(id)).then(setPlayers);
  }, [id]);

  const togglePlayer = (pid: number) => {
    setSelected(prev => prev.includes(pid) ? prev.filter(p => p !== pid) : [...prev, pid]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (selected.length !== 8) { setError("八人转需要恰好 8 名球员"); return; }
    try {
      const comp = await compApi.createCompetition({
        name, club_id: Number(id), format: "eight_player_rotation", courts, player_ids: selected,
      });
      navigate(`/competitions/${comp.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "创建失败");
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">创建八人转</h1>
      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow space-y-4">
        {error && <div className="bg-red-100 text-red-700 p-3 rounded">{error}</div>}
        <div>
          <label className="block text-sm font-medium mb-1">比赛名称</label>
          <input value={name} onChange={e => setName(e.target.value)}
                 className="w-full border p-2 rounded" placeholder="例如：周日下午八人转" required />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">场地数</label>
          <select value={courts} onChange={e => setCourts(Number(e.target.value))}
                  className="w-full border p-2 rounded">
            <option value={2}>2 场地</option>
            <option value={4}>4 场地</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">选择球员 (已选 {selected.length}/8)</label>
          <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto">
            {players.map(p => (
              <button key={p.id} type="button" onClick={() => togglePlayer(p.id)}
                className={`p-2 rounded text-left ${selected.includes(p.id) ? "bg-blue-100 border-blue-500 border" : "border bg-gray-50"}`}>
                {p.name} <span className="text-gray-400 text-sm">Lv.{p.level}</span>
              </button>
            ))}
          </div>
        </div>
        <button type="submit" className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700">
          生成对阵表
        </button>
      </form>
    </div>
  );
}
```

- [ ] **步骤 4：创建 CompetitionBoard — frontend/src/pages/CompetitionBoard.tsx**

```tsx
import { useParams } from "react-router-dom";
import { useState } from "react";
import { useCompetition } from "../hooks/useCompetition";
import * as compApi from "../api/competitions";

export default function CompetitionBoard() {
  const { id } = useParams<{ id: string }>();
  const { comp, refresh } = useCompetition(Number(id));
  const [scoring, setScoring] = useState<{ matchId: number; scoreA: string; scoreB: string } | null>(null);

  if (!comp) return <div className="p-8 text-center">加载中...</div>;

  const handleStart = async () => {
    await compApi.startCompetition(comp.id);
    refresh();
  };

  const handleScore = async () => {
    if (!scoring) return;
    await compApi.recordScore(scoring.matchId, Number(scoring.scoreA), Number(scoring.scoreB));
    setScoring(null);
    refresh();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">{comp.name}</h1>
        <div className="flex gap-3 items-center">
          <span className={`px-3 py-1 rounded text-sm ${comp.status === "in_progress" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"}`}>
            {comp.status === "pending" ? "待开始" : comp.status === "in_progress" ? "进行中" : "已结束"}
          </span>
          {comp.status === "pending" && (
            <button onClick={handleStart} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">开始比赛</button>
          )}
        </div>
      </div>

      {comp.rounds.map(rnd => (
        <div key={rnd.id} className="bg-white rounded-lg shadow overflow-hidden">
          <h2 className="bg-gray-100 px-4 py-2 font-semibold">第 {rnd.round_number} 轮</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-gray-200">
            {rnd.matches.map(m => (
              <div key={m.id} className="bg-white p-4">
                <div className="text-sm text-gray-500 mb-2">场地 {m.court}</div>
                <div className="flex justify-between items-center">
                  <div className="flex-1 text-center">
                    <div>球员 {m.team_a.join(" / ")}</div>
                    <div className="text-2xl font-mono">{m.score_a ?? "-"}</div>
                  </div>
                  <span className="px-3 text-gray-400 font-bold">VS</span>
                  <div className="flex-1 text-center">
                    <div>球员 {m.team_b.join(" / ")}</div>
                    <div className="text-2xl font-mono">{m.score_b ?? "-"}</div>
                  </div>
                </div>
                {comp.status === "in_progress" && m.score_a === null && (
                  <button onClick={() => setScoring({ matchId: m.id, scoreA: "", scoreB: "" })}
                          className="mt-3 w-full bg-gray-100 py-1 rounded text-sm hover:bg-gray-200">录入比分</button>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* 录制比分弹窗 */}
      {scoring && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl w-80 space-y-4">
            <h3 className="font-bold text-lg">录入比分</h3>
            <div className="flex gap-4 items-center">
              <input value={scoring.scoreA} onChange={e => setScoring({ ...scoring, scoreA: e.target.value })}
                     className="w-20 border p-2 rounded text-center text-xl" placeholder="A队" />
              <span className="text-gray-400">:</span>
              <input value={scoring.scoreB} onChange={e => setScoring({ ...scoring, scoreB: e.target.value })}
                     className="w-20 border p-2 rounded text-center text-xl" placeholder="B队" />
            </div>
            <div className="flex gap-2">
              <button onClick={handleScore} className="flex-1 bg-blue-600 text-white py-2 rounded">确认</button>
              <button onClick={() => setScoring(null)} className="flex-1 bg-gray-200 py-2 rounded">取消</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **步骤 5：更新 App.tsx 路由**

```tsx
import CreateCompetition from "./pages/CreateCompetition";
import CompetitionBoard from "./pages/CompetitionBoard";
// 加上路由：
<Route path="/clubs/:id/create-competition" element={<CreateCompetition />} />
<Route path="/competitions/:id" element={<CompetitionBoard />} />
```

- [ ] **步骤 6：提交**

```bash
git add frontend/src/api/competitions.ts frontend/src/hooks/useCompetition.ts frontend/src/pages/CreateCompetition.tsx frontend/src/pages/CompetitionBoard.tsx frontend/src/App.tsx
git commit -m "feat: 实现比赛创建页面和比赛看板（含比分录入）"
```

---

### Task 12：前端个人主页 + 排行榜

**要创建的文件：** `frontend/src/api/leaderboard.ts`, `frontend/src/pages/ProfilePage.tsx`, `frontend/src/pages/LeaderboardPage.tsx`

**产出：** 个人主页，俱乐部排行榜

- [ ] **步骤 1：创建 leaderboard API — frontend/src/api/leaderboard.ts**

```typescript
import client from "./client";

export interface LeaderboardEntry {
  id: number;
  name: string;
  level: number;
  win_rate: number;
  total_matches: number;
  wins: number;
}

export async function getLeaderboard(clubId: number): Promise<LeaderboardEntry[]> {
  const { data } = await client.get(`/leaderboard?club_id=${clubId}`);
  return data;
}
```

- [ ] **步骤 2：创建 ProfilePage**

```tsx
import { useAuth } from "../hooks/useAuth";

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">个人主页</h1>
      <div className="bg-white p-6 rounded-lg shadow space-y-3">
        <div className="flex justify-between"><span className="text-gray-500">姓名</span><span className="font-medium">{user?.name}</span></div>
        <div className="flex justify-between"><span className="text-gray-500">用户名</span><span>{user?.username}</span></div>
      </div>
    </div>
  );
}
```

- [ ] **步骤 3：创建 LeaderboardPage**

```tsx
import { useEffect, useState } from "react";
import type { Club } from "../types";
import type { LeaderboardEntry } from "../api/leaderboard";
import * as clubsApi from "../api/clubs";
import * as lbApi from "../api/leaderboard";

export default function LeaderboardPage() {
  const [clubs, setClubs] = useState<Club[]>([]);
  const [selectedClub, setSelectedClub] = useState<number | null>(null);
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);

  useEffect(() => { clubsApi.listClubs().then(setClubs); }, []);
  useEffect(() => {
    if (selectedClub) lbApi.getLeaderboard(selectedClub).then(setEntries);
  }, [selectedClub]);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">排行榜</h1>

      <div className="flex gap-2 flex-wrap">
        {clubs.map(c => (
          <button key={c.id} onClick={() => setSelectedClub(c.id)}
            className={`px-4 py-2 rounded ${selectedClub === c.id ? "bg-blue-600 text-white" : "bg-gray-200"}`}>
            {c.name}
          </button>
        ))}
      </div>

      {entries.length > 0 && (
        <table className="w-full bg-white rounded-lg shadow overflow-hidden">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">排名</th>
              <th className="px-4 py-3 text-left text-sm font-medium">球员</th>
              <th className="px-4 py-3 text-right text-sm font-medium">胜率</th>
              <th className="px-4 py-3 text-right text-sm font-medium">胜场</th>
              <th className="px-4 py-3 text-right text-sm font-medium">总局数</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e, i) => (
              <tr key={e.id} className="border-t">
                <td className="px-4 py-3">{i + 1}</td>
                <td className="px-4 py-3 font-medium">{e.name}</td>
                <td className="px-4 py-3 text-right">{(e.win_rate * 100).toFixed(1)}%</td>
                <td className="px-4 py-3 text-right">{e.wins}</td>
                <td className="px-4 py-3 text-right">{e.total_matches}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

- [ ] **步骤 4：更新 App.tsx 路由**

```tsx
import ProfilePage from "./pages/ProfilePage";
import LeaderboardPage from "./pages/LeaderboardPage";
// 加上：
<Route path="/profile" element={<ProfilePage />} />
<Route path="/leaderboard" element={<LeaderboardPage />} />
```

- [ ] **步骤 5：提交**

```bash
git add frontend/src/api/leaderboard.ts frontend/src/pages/ProfilePage.tsx frontend/src/pages/LeaderboardPage.tsx frontend/src/App.tsx
git commit -m "feat: 实现个人主页和排行榜"
```

---

### Task 13：Docker 部署 + Agent 占位

**要创建的文件：** `frontend/src/components/AgentPanel.tsx`, `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `backend/.env`

**产出：** docker-compose 一键启动前后端

- [ ] **步骤 1：创建 AgentPanel 占位组件**

```tsx
export default function AgentPanel() {
  // 第二期：这里放 Agent 对话面板
  return null;
}
```

- [ ] **步骤 2：创建 backend/Dockerfile**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
RUN mkdir -p /app/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **步骤 3：创建 frontend/Dockerfile**

```dockerfile
FROM node:20-alpine as build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

- [ ] **步骤 4：创建 frontend/nginx.conf**

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri /index.html;
    }
}
```

- [ ] **步骤 5：创建 docker-compose.yml**

```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/badminton.db
      - SECRET_KEY=${SECRET_KEY:-dev-secret-change-in-production}
    volumes:
      - ./data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

- [ ] **步骤 6：创建 backend/.env**

```
DATABASE_URL=sqlite:///./data/badminton.db
SECRET_KEY=dev-secret-change-in-production
```

- [ ] **步骤 7：集成测试**

```bash
docker compose up --build -d
curl http://localhost:8000/api/v1/health
curl http://localhost/
docker compose down
```
预期：后端返回 `{"status": "ok"}`，前端返回 HTML 页面。

- [ ] **步骤 8：提交**

```bash
git add frontend/src/components/AgentPanel.tsx docker-compose.yml backend/Dockerfile frontend/Dockerfile frontend/nginx.conf backend/.env
git commit -m "feat: 添加 Docker 部署配置和 Agent 占位组件"
```

---

## 第二期计划（Agent 集成）

第一期完成后，第二期叠加以下功能（详细计划届时再展开）：

- **任务 14：** Agent 基础架构 — LangGraph agent 搭建，Tool 定义
- **任务 15：** Agent SSE 流式 — Agent 对话接口，流式输出
- **任务 16：** RAG 集成 — ChromaDB 向量检索历史战绩
- **任务 17：** 智能分组 — Agent 根据球员水平推荐分组方案
- **任务 18：** 赛后分析 — Agent 自动生成比赛统计报告
- **任务 19：** 人工确认 — LangGraph interrupt 节点，关键操作等用户确认
- **任务 20：** 前端 Agent 对话面板 — 浮动聊天窗口 + widget 渲染
