# 数据库查看完全指南

## 方式1: DBeaver（推荐，功能最全）

### 下载安装
1. 访问: https://dbeaver.io/download/
2. 下载 Windows 版本 (Installer 或 zip)
3. 安装（免费社区版即可）

### 连接数据库

#### 如果是 Docker 启动的 PostgreSQL:
```
主机: localhost
端口: 5432
数据库: badminton
用户名: badminton
密码: badminton123
```

#### 如果是云服务器:
```
主机: 你的服务器IP 或 域名
端口: 5432
数据库: badminton
用户名: badminton
密码: 你设置的密码
```

### 步骤截图
```
1. 点击左上角 "新建连接" 按钮 (插头图标)
2. 选择 PostgreSQL → 下一步
3. 填写上面的连接信息
4. 点击 "测试连接" (应该显示成功)
5. 点击 "完成"
```

### 常用操作

#### 查看所有表
- 左侧导航栏展开: badminton → Schemas → public → Tables
- 右键 Tables → 刷新

#### 查看表数据
- 双击表名 (如 `users`)
- 或右键表 → 查看表

#### 执行SQL查询
- 点击顶部 SQL 按钮 (或 Ctrl+Enter)
- 输入: `SELECT * FROM users LIMIT 10;`
- 点击执行

#### 导出数据
- 右键表 → 导出数据
- 选择格式: CSV / SQL / JSON
- 选择导出位置

#### 修改数据
- 双击表查看数据
- 直接在表格中编辑
- 点击底部保存按钮 (Ctrl+S)

---

## 方式2: Web管理界面（无需安装）

如果使用 `docker-compose.dev.yml` 启动，会自动运行 pgAdmin:

```
访问: http://localhost:5050
用户名: admin@admin.com
密码: admin
```

### 添加服务器
```
1. 点击 "Add New Server"
2. General 标签: 名称随便写 (如 "羽毛球数据库")
3. Connection 标签:
   - Host: postgres (Docker内部网络名)
   - Port: 5432
   - Database: badminton
   - Username: badminton
   - Password: badminton123
4. 点击 Save
```

---

## 方式3: 命令行（最快）

### 进入数据库命令行
```bash
# Docker方式
docker exec -it badminton-postgres psql -U badminton

# 本地安装的PostgreSQL
psql -h localhost -U badminton -d badminton
```

### 常用命令
```sql
-- 查看所有表
\dt

-- 查看表结构
\d users

-- 查询数据
SELECT * FROM users LIMIT 10;

-- 统计记录数
SELECT COUNT(*) FROM competitions;

-- 退出
\q
```

---

## 核心表说明

| 表名 | 用途 | 关键字段 |
|-----|------|---------|
| `users` | 用户账号 | id, username, name |
| `clubs` | 俱乐部 | id, name, owner_id |
| `club_members` | 俱乐部成员关系 | club_id, player_id |
| `players` | 球员信息 | id, name, level |
| `competitions` | 比赛 | id, name, status, scheduled_at |
| `competition_players` | 比赛参赛球员 | competition_id, player_id |
| `rounds` | 比赛轮次 | id, competition_id, round_number |
| `matches` | 对阵 | id, round_id, team_a, team_b, score_a, score_b |
| `activities` | 活动/约球 | id, title, start_time |
| `activity_signups` | 活动报名 | activity_id, player_id |
| `notifications` | 通知 | id, user_id, title, message |
| `agent_conversations` | AI对话记录 | id, user_id, role, content |
| `predictions` | 毒奶预测 | id, match_id, predicted_winner |

---

## 常用查询示例

### 查看所有用户
```sql
SELECT id, username, name, created_at FROM users ORDER BY created_at DESC;
```

### 查看某俱乐部所有成员
```sql
SELECT p.name, p.level, cm.joined_at
FROM club_members cm
JOIN players p ON cm.player_id = p.id
WHERE cm.club_id = 1;
```

### 查看比赛统计
```sql
SELECT 
    c.name,
    c.status,
    COUNT(DISTINCT cp.player_id) as player_count,
    COUNT(DISTINCT m.id) as match_count
FROM competitions c
LEFT JOIN competition_players cp ON c.id = cp.competition_id
LEFT JOIN rounds r ON c.id = r.competition_id
LEFT JOIN matches m ON r.id = m.round_id
GROUP BY c.id;
```

### 查看AI对话记录
```sql
SELECT role, SUBSTRING(content, 1, 50) as content_preview, created_at
FROM agent_conversations
WHERE user_id = 1
ORDER BY created_at DESC
LIMIT 20;
```

---

## 数据备份

### 使用 DBeaver 备份
```
1. 右键数据库 → 导出数据
2. 选择 SQL 格式
3. 勾选 "导出到文件"
4. 选择保存位置
```

### 使用命令行备份
```bash
# Docker方式
docker exec badminton-postgres pg_dump -U badminton badminton > backup_$(date +%Y%m%d).sql

# 本地方式
pg_dump -h localhost -U badminton badminton > backup.sql
```

### 恢复数据
```bash
# Docker方式
docker exec -i badminton-postgres psql -U badminton < backup.sql
```

---

## 问题排查

### 连接失败
```
错误: connection refused
解决: 
1. 检查Docker是否运行: docker ps
2. 检查端口是否被占用: netstat -ano | findstr 5432
3. 重启数据库: docker restart badminton-postgres
```

### 忘记密码
```bash
# 进入Docker修改密码
docker exec -it badminton-postgres psql -U postgres
ALTER USER badminton WITH PASSWORD '新密码';
```

### 中文乱码
```
DBeaver → 右键连接 → 编辑连接 → 驱动属性
添加: characterEncoding = UTF8
```
