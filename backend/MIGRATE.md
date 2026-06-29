# 快速切换到PostgreSQL

## 方案A：全新开始（推荐）

适合测试环境或可以接受数据重置的场景。

### 步骤

1. **安装PostgreSQL**
   - Windows: 下载安装包 https://www.postgresql.org/download/windows/
   - 安装时设置密码（记住它！）
   - 默认端口5432

2. **创建数据库**
   ```bash
   # 使用psql或DBeaver创建数据库
   CREATE DATABASE badminton;
   CREATE USER badminton WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE badminton TO badminton;
   ```

3. **修改 .env**
   ```env
   DATABASE_URL=postgresql://badminton:your_password@localhost:5432/badminton
   ```

4. **安装依赖**
   ```bash
   pip install psycopg2-binary
   ```

5. **启动后端**
   ```bash
   python -m uvicorn app.main:app
   ```
   SQLAlchemy会自动创建所有表！

6. **DBeaver查看**
   - 新建连接 → PostgreSQL
   - 主机: localhost, 端口: 5432
   - 数据库: badminton
   - 用户名: badminton, 密码: your_password
   - 测试连接 → 完成！

---

## 方案B：保留现有数据

适合已有数据需要保留的场景。

### 步骤

1-4步同方案A

5. **运行迁移脚本**
   ```bash
   # 先修改.env指向PostgreSQL
   # 然后运行
   python scripts/migrate_to_postgres.py
   ```

6. **启动后端**
   ```bash
   python -m uvicorn app.main:app
   ```

---

## 常见问题

### Q: DBeaver连接失败？
- 检查PostgreSQL服务是否运行（Windows服务管理器）
- 检查5432端口是否被占用
- 检查防火墙
- 检查用户名密码

### Q: 需要改代码吗？
**不需要！** SQLAlchemy完全兼容，自动适配。

### Q: SQLite和PostgreSQL能同时用吗？
可以，修改DATABASE_URL随时切换。

### Q: 性能提升多少？
- 单用户：差不多
- 10+并发：PostgreSQL明显更快
- 100+并发：SQLite会锁死，PostgreSQL正常

### Q: 云端部署用什么？
- 阿里云/腾讯云: PostgreSQL托管服务
- AWS: RDS PostgreSQL
- Docker: postgres:16-alpine镜像
