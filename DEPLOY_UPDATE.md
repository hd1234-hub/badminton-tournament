# 增量部署与运维手册

本文档记录**腾讯云生产环境**的日常更新步骤，以及踩坑经验。  
生产服务器信息请写在本地 `deploy.config.json`（从 `deploy.config.json.example` 复制，**不要提交到 Git**）。

> **推荐方式：手动 3 步（最快、最稳）**  
> 一键脚本 `update-deploy.ps1` 可用，但在 Windows 中文路径下容易出问题，见下文「踩坑总结」。

---

## 一、日常增量更新（改完代码后）

### 第 1 步：本机 PowerShell（在桌面目录）

```powershell
cd C:\path\to\badminton-tournament

tar --exclude="./frontend/node_modules" `
    --exclude="./backend/data" `
    --exclude="./.git" `
    --exclude="./.env.deploy" `
    -cf badminton-deploy.tar .

scp badminton-deploy.tar ubuntu@YOUR_SERVER_IP:~/badminton-tournament/
```

输入服务器密码，等待上传完成。

### 第 2 步：服务器终端（或 `ssh ubuntu@YOUR_SERVER_IP`）

```bash
cd ~/badminton-tournament

# 保护服务器已有配置（不要覆盖 .env.deploy）
cp .env.deploy /tmp/.env.deploy.bak
tar -xf badminton-deploy.tar --strip-components=1
cp /tmp/.env.deploy.bak .env.deploy

# 增量构建（使用 Docker 缓存，约 2～5 分钟）
docker compose --env-file .env.deploy up -d --build
```

### 第 3 步：验证部署成功

```bash
curl -s http://127.0.0.1:8000/api/v1/health
docker compose --env-file .env.deploy ps
```

**必须满足：**

| 检查项 | 期望结果 |
|--------|----------|
| health | `{"status":"ok"}` |
| badminton-api | **Up**（不是 Restarting） |
| badminton-web | Up |
| badminton-db | Up (healthy) |

浏览器打开 **http://YOUR_SERVER_IP**（或你的域名），必要时 **Ctrl+F5** 强制刷新。

---

## 二、只改了单个文件时

例如只改了 `docker-compose.yml`：

```powershell
scp docker-compose.yml ubuntu@YOUR_SERVER_IP:~/badminton-tournament/
```

```bash
cd ~/badminton-tournament
docker compose --env-file .env.deploy up -d --build
```

---

## 三、首次部署（新服务器）

```bash
cd ~/badminton-tournament
cp .env.deploy.example .env.deploy
nano .env.deploy   # 填写 DB_PASSWORD、SECRET_KEY、ANTHROPIC_*、CORS_ORIGINS
chmod +x deploy.sh
./deploy.sh
```

`.env.deploy` 最少要改：

```env
DB_PASSWORD=强密码
SECRET_KEY=随机字符串
CORS_ORIGINS=http://你的服务器IP
ANTHROPIC_AUTH_TOKEN=你的API密钥
ANTHROPIC_BASE_URL=
ANTHROPIC_MODEL=deepseek-v4-pro
ADMIN_USERNAMES=your_admin_username
```

腾讯云防火墙放行：**22、80**（HTTPS 以后加 443）。

---

## 四、部署脚本（可选，非首选）

| 文件 | 用途 |
|------|------|
| `update-deploy.ps1` | Windows 一键调用 Python 部署 |
| `deploy_update.py` | 读 `deploy.config.json`，处理 UTF-8 中文路径 |
| `deploy-remote.sh` | 服务器端解压、备份、构建 |
| `deploy.sh` | 服务器首次全量部署 |

```powershell
cd C:\path\to\badminton-tournament
.\update-deploy.ps1
```

**注意：** PowerShell 5 对中文路径/脚本编码支持差，若报错请改用手动流程（第一节）。

---

## 五、中断 / 失败恢复

### PowerShell 脚本中途 Ctrl+C

数据库和 `.env.deploy` **不会丢**。在 OrcaTerm 执行：

```bash
cd ~/badminton-tournament
cp .env.deploy /tmp/.env.deploy.bak
tar -xf badminton-deploy.tar --strip-components=1
cp /tmp/.env.deploy.bak .env.deploy
docker compose --env-file .env.deploy up -d --build
```

若提示找不到 `badminton-deploy.tar`，回到本机重新 `scp` 上传后再解压。

### 前端正常、后端 Restarting

```bash
cd ~/badminton-tournament
docker compose --env-file .env.deploy logs --tail=80 backend
docker compose --env-file .env.deploy run --rm --no-deps backend python -m alembic stamp head
docker compose --env-file .env.deploy up -d --build backend
sleep 10
curl -s http://127.0.0.1:8000/api/v1/health
```

若仍失败，上传修复后的 entrypoint 并重建：

```powershell
scp backend/docker-entrypoint.sh ubuntu@YOUR_SERVER_IP:~/badminton-tournament/backend/
```

```bash
cd ~/badminton-tournament
docker compose --env-file .env.deploy up -d --build backend
```

---

## 六、常用运维命令

```bash
cd ~/badminton-tournament

# 查看状态
docker compose --env-file .env.deploy ps

# 查看日志
docker compose --env-file .env.deploy logs -f backend
docker compose --env-file .env.deploy logs -f frontend

# 备份数据库
mkdir -p backups
docker exec badminton-db pg_dump -U badminton badminton > backups/badminton-$(date +%Y%m%d).sql

# 重启单个服务
docker compose --env-file .env.deploy restart backend
```

---

## 七、踩坑总结（必读）

### 1. Windows + 中文路径

项目目录 `羽毛球agent赛事` 含中文。PowerShell 传 SSH 时可能乱码（如变成 `缇芥瘺鐞僡gent璧涗簨`），导致找不到 `.env.deploy`。

**对策：** 增量更新优先用 **桌面 tar + OrcaTerm**，或 `deploy_update.py`（读 UTF-8 的 `deploy.config.json`）。

### 2. 不要用 `--no-cache` 做日常更新

`build --no-cache` 会全量重装 apt/npm，需 15～30 分钟。  
日常更新用：

```bash
docker compose --env-file .env.deploy up -d --build
```

### 3. 不要覆盖 `.env.deploy`

服务器上的 API 密钥、数据库密码已配好。打包时排除 `.env.deploy`，解压前备份、解压后恢复。

### 4. 不要 `docker compose down -v`

`-v` 会删除 PostgreSQL 数据卷，**用户数据会丢**。

### 5. Alembic 与老数据库

生产库可能是 `create_all` 建的，没有完整 Alembic 历史。新版本 entrypoint 跑迁移失败会导致 backend 反复重启。  
`docker-entrypoint.sh` 已做容错：迁移失败时 `stamp head` 并继续启动。

### 6. 「部署完成」≠ 服务正常

脚本可能显示完成，但 `badminton-api` 仍 Restarting。**务必检查：**

```bash
curl -s http://127.0.0.1:8000/api/v1/health
docker compose --env-file .env.deploy ps
```

### 7. 前端能开、API 不能用

Nginx（80）正常只说明 frontend 容器 OK。登录、通知、AI 等依赖 backend（8000）。health 非 ok 时先查 backend 日志。

---

## 八、速查卡片

```
改代码
  → 桌面 tar 打包（排除 node_modules / data / .git / .env.deploy）
  → scp 到 ~/badminton-tournament/
  → OrcaTerm：备份 .env.deploy → 解压 → 恢复 .env.deploy
  → docker compose --env-file .env.deploy up -d --build
  → curl health 确认 ok
  → 浏览器 Ctrl+F5
```

---

## 相关文件

- `DEPLOY.md` — 首次部署、方案对比
- `deploy.config.json.example` — 服务器 IP、用户、远程路径模板（复制为本地 `deploy.config.json`）
- `.env.deploy.example` — 生产环境变量模板
- `backup-db.ps1` — 本机触发数据库备份（需 Docker 可访问 db 容器）
