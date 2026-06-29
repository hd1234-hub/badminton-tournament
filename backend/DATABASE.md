# 数据库配置指南

## SQLite（开发环境）

默认配置，无需额外安装。

```env
DATABASE_URL=sqlite:///./data/badminton.db
```

## PostgreSQL（生产环境）

### 1. 安装PostgreSQL

**Windows**: 
- 下载: https://www.postgresql.org/download/windows/
- 安装时记住设置的密码
- 默认端口: 5432

**Docker**:
```bash
docker run -d \
  --name badminton-db \
  -e POSTGRES_USER=badminton \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=badminton \
  -p 5432:5432 \
  postgres:16-alpine
```

### 2. 修改环境变量

```env
# 修改数据库连接
DATABASE_URL=postgresql://badminton:your_password@localhost:5432/badminton

# 保持其他配置不变
SECRET_KEY=your_random_key_here
ANTHROPIC_AUTH_TOKEN=sk-xxx
...
```

### 3. 安装依赖

```bash
pip install psycopg2-binary alembic
```

### 4. 自动迁移

SQLAlchemy会自动创建表结构，无需手动操作！

启动后端时会自动执行：
```
INFO | 服务启动，初始化数据库...
INFO | 数据库初始化完成
```

### 5. 使用DBeaver查看数据

1. **打开DBeaver** → 新建连接 → 选择 PostgreSQL

2. **填写连接信息**:
   - 主机: `localhost`
   - 端口: `5432`
   - 数据库: `badminton`
   - 用户名: `badminton`
   - 密码: `your_password`

3. **测试连接** → 确定

4. **查看表结构**:
   - 展开 `badminton` → `Schemas` → `public` → `Tables`
   - 右键表 → 查看数据
   - 常用表：
     - `users` - 用户信息
     - `clubs` - 俱乐部
     - `competitions` - 比赛
     - `matches` - 对阵
     - `agent_conversations` - AI对话记录

### 6. 数据库备份

```bash
# 导出
pg_dump -h localhost -U badminton badminton > backup.sql

# 导入
psql -h localhost -U badminton badminton < backup.sql
```

## 从SQLite迁移到PostgreSQL

### 方法1: 重新创建数据（推荐）
直接切换数据库，数据重新开始。

### 方法2: 数据迁移脚本

```bash
# 1. 导出SQLite数据
python scripts/migrate_to_postgres.py

# 2. 切换到PostgreSQL
# 修改 .env 的 DATABASE_URL

# 3. 启动服务，数据自动导入
python -m uvicorn app.main:app
```

## 性能对比

| 场景 | SQLite | PostgreSQL |
|------|--------|------------|
| 单用户 | ✅ 很快 | ✅ 很快 |
| 100并发 | ❌ 锁等待 | ✅ 没问题 |
| 大数据量 | ⚠️ 变慢 | ✅ 索引优化 |
| 分布式部署 | ❌ 不支持 | ✅ 支持 |
| 数据备份 | 复制文件 | 专业工具 |

## 故障排查

### 连接失败
```
Error: connection refused
```
- 检查PostgreSQL服务是否启动
- 检查端口5432是否被占用
- 检查防火墙设置

### 权限错误
```
Error: permission denied for table
```
- 检查用户名密码
- 检查数据库权限: `GRANT ALL PRIVILEGES ON DATABASE badminton TO badminton;`

### 编码问题
```
Error: character encoding
```
- PostgreSQL默认UTF-8，无需额外配置
- SQLite迁移时注意中文编码
