# Badminton Tournament System

[![CI](https://github.com/hd1234-hub/badminton-tournament/actions/workflows/ci.yml/badge.svg)](https://github.com/hd1234-hub/badminton-tournament/actions/workflows/ci.yml)

开源羽毛球赛事管理系统，支持俱乐部赛事、公开大厅赛、多种赛制编排、实时计分看板、排行榜与 AI 助手。

[English](#english) | [中文](#中文)

---

## 中文

### 项目展示

#### 赛事大厅 / 首页

![赛事大厅](docs/images/dashboard.png)

> 更多截图（比赛看板、AI 助手等）可继续放入 `docs/images/` 并在本节补充展示。

### 功能亮点

- **俱乐部管理**：创建俱乐部、邀请成员、活动报名
- **赛事编排**：八人转、单打/双打轮转、淘汰赛等多种赛制
- **公开大厅赛**：无需绑定俱乐部即可发起公开报名比赛
- **比赛看板**：报名、开赛、计分、排名、分享卡片
- **排行榜**：俱乐部维度战绩统计
- **AI 助手**（可选）：自然语言创建比赛、查询赛况（需配置 Anthropic 兼容 API）
- **管理后台**：赛事与用户统计

### 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS |
| 后端 | FastAPI + SQLAlchemy + Alembic |
| 数据库 | PostgreSQL（生产）/ SQLite（测试） |
| 部署 | Docker Compose + Nginx |

### 快速开始（本地开发）

#### 1. 克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/badminton-tournament.git
cd badminton-tournament
```

#### 2. 启动数据库（Docker）

```bash
docker compose -f docker-compose.dev.yml up -d
```

PostgreSQL 默认：`badminton / badminton123 @ localhost:5432/badminton`  
可选 pgAdmin：http://localhost:5050

#### 3. 启动后端

```bash
cd backend
cp .env.example .env
# 编辑 .env：DATABASE_URL、SECRET_KEY、（可选）ANTHROPIC_AUTH_TOKEN

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

API 文档：http://localhost:8001/docs

#### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开：http://localhost:5175

### 生产部署（Docker）

```bash
cp .env.deploy.example .env.deploy
# 填写 DB_PASSWORD、SECRET_KEY、CORS_ORIGINS、ANTHROPIC_AUTH_TOKEN

docker compose up -d --build
```

详细说明见 [DEPLOY.md](./DEPLOY.md) 与 [DEPLOY_UPDATE.md](./DEPLOY_UPDATE.md)。

远程增量部署脚本需本地配置：

```bash
cp deploy.config.json.example deploy.config.json
# 填写你的服务器 IP、SSH 用户、远程路径
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | 数据库连接串 |
| `SECRET_KEY` | JWT 签名密钥（生产必填） |
| `CORS_ORIGINS` | 允许的前端域名，逗号分隔 |
| `ANTHROPIC_AUTH_TOKEN` | AI 功能 API Key（可选） |
| `ADMIN_USERNAMES` | 管理员用户名，逗号分隔 |
| `RUN_AUTO_MIGRATE` | 开发可 `true`；生产建议 `false` 并用 Alembic |

完整示例见 `backend/.env.example`、`.env.deploy.example`。

### 运行测试

```bash
cd backend
pytest
```

### 项目结构

```
├── backend/          # FastAPI 后端
│   ├── app/          # 路由、服务、模型
│   ├── alembic/      # 数据库迁移
│   └── tests/
├── frontend/         # React 前端（唯一源码入口）
├── docker-compose.yml
└── docker-compose.dev.yml
```

> 注意：仓库根目录若存在 `src/` 为历史副本，请以 `frontend/src/` 为准。

### 开源前自检

推送 GitHub 前请确认：

- [ ] 未提交 `.env`、`.env.deploy`、`deploy.config.json`
- [ ] 未提交 `*.db`、`node_modules`、`__pycache__`
- [ ] 文档与脚本中无真实服务器 IP、API Key
- [ ] 若密钥曾误提交，已在服务商处**轮换密钥**

详见 [SECURITY.md](./SECURITY.md)。

### 许可证

[MIT](./LICENSE)

---

## English

### Overview

Open-source badminton tournament platform with club management, public lobby competitions, format engines, live scoreboards, leaderboards, and an optional AI assistant.

### Quick Start

1. Start Postgres: `docker compose -f docker-compose.dev.yml up -d`
2. Backend: `cd backend && cp .env.example .env && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8001`
3. Frontend: `cd frontend && npm install && npm run dev`

### Production

Copy `.env.deploy.example` to `.env.deploy`, fill secrets, then `docker compose up -d --build`.

### License

MIT — see [LICENSE](./LICENSE).

### Security

Do not commit secrets. See [SECURITY.md](./SECURITY.md).
