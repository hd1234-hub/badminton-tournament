# 大厅比赛创建失败修复

## 问题
创建大厅比赛时传 `club_id: null`，后端返回错误。

## 原因
生产数据库 PostgreSQL 的 `competitions.club_id` 列可能仍是 `NOT NULL`，
Alembic 迁移 `f8a3b2c1d456_make_club_id_nullable.py` 未执行或执行失败。

## 修复步骤（腾讯云 OrcaTerm）

### 1. 查看后端日志确认错误

```bash
cd ~/badminton-tournament
docker compose --env-file .env.deploy logs --tail=50 backend
```

如果看到类似 `null value in column "club_id" violates not-null constraint`，
就是数据库约束问题。

### 2. 手动执行 Alembic 迁移

```bash
cd ~/badminton-tournament
docker compose --env-file .env.deploy run --rm backend python -m alembic upgrade head
```

### 3. 如果迁移失败，直接改数据库列

```bash
# 进入数据库容器
docker exec -it badminton-db psql -U badminton -d badminton

# 在 psql 里执行
ALTER TABLE competitions ALTER COLUMN club_id DROP NOT NULL;
\q
```

### 4. 重启后端

```bash
cd ~/badminton-tournament
docker compose --env-file .env.deploy restart backend
```

### 5. 验证

浏览器打开 `http://YOUR_SERVER_IP/create-lobby-competition`（或你的域名），
创建大厅比赛测试。

## 预防

确保 `backend/docker-entrypoint.sh` 里有：

```bash
echo "Running Alembic migrations..."
python -m alembic upgrade head
```

这样每次部署都会自动跑迁移。
