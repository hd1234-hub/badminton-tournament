# 部署指南

> **已有服务器、日常改代码后更新？** 请看 **[DEPLOY_UPDATE.md](./DEPLOY_UPDATE.md)**（推荐手动 3 步，含踩坑总结与故障恢复）。

## 方案对比

| 方案 | 适用场景 | 难度 | 成本(月) |
|-----|---------|------|---------|
| **Docker部署** ⭐推荐 | 有服务器 | 低 | 云服务器~50元 |
| **云托管平台** | 快速上线 | 最低 | ~100元起 |
| **手动部署** | 学习/定制 | 中 | 云服务器~50元 |

---

## 🚀 方案1: Docker部署（推荐）

### 你需要准备的
- 1台云服务器（阿里云/腾讯云/华为云，2核4G约50元/月）
- 1个域名（可选，约30元/年）

### 部署步骤

#### 1. 购买云服务器
- 阿里云: ecs.console.aliyun.com
- 腾讯云: console.cloud.tencent.com/cvm
- 选择 **CentOS 8** 或 **Ubuntu 22.04**
- 配置: 2核CPU 4G内存 即可

#### 2. 连接服务器
```bash
# Windows使用PowerShell或Xshell
ssh root@你的服务器IP
```

#### 3. 安装Docker
```bash
# 一键安装脚本
curl -fsSL https://get.docker.com | sh

# 启动Docker
systemctl start docker
systemctl enable docker
```

#### 4. 上传项目代码
```bash
# 在你的电脑上执行
scp -r 羽毛球agent赛事 root@你的服务器IP:/opt/
```

#### 5. 服务器上部署
```bash
cd /opt/羽毛球agent赛事

# 创建部署环境变量文件（仓库根目录）
cp .env.deploy.example .env.deploy

# 编辑配置文件
vi .env.deploy
# 修改: DB_PASSWORD, SECRET_KEY, ANTHROPIC_AUTH_TOKEN, CORS_ORIGINS

# 一键部署
./deploy.sh
```

#### 6. 访问系统
- 浏览器打开: `http://你的服务器IP`

---

## ☁️ 方案2: 云托管平台（最简单）

### 阿里云/腾讯云托管

1. **注册账号**
   - 阿里云: https://www.aliyun.com
   - 腾讯云: https://cloud.tencent.com

2. **开通服务**
   - 搜索"容器服务"或"Serverless"
   - 按量付费，无需准备服务器

3. **上传代码**
   - 支持GitHub直接导入
   - 自动构建部署

4. **绑定域名**
   - 平台提供临时域名
   - 可以绑定自己的域名

### 费用估算
- 低流量: ~30-50元/月
- 中等流量: ~100-200元/月
- 自动扩缩容，无需维护服务器

---

## 🔧 方案3: 手动部署（需要更多维护）

### 适用场景
- 需要深度定制
- 学习Linux运维
- 已有服务器资源

### 流程
```
1. 购买服务器
2. 安装PostgreSQL
3. 安装Python环境
4. 上传代码
5. 配置Nginx反向代理
6. 配置HTTPS证书
7. 配置进程管理（systemd/supervisor）
8. 配置日志轮转
```

**我可以帮你写好所有配置文件**，你只需要复制粘贴执行。

---

## 📊 部署后维护

### 查看日志
```bash
docker compose --env-file .env.deploy logs -f backend   # 后端日志
docker compose --env-file .env.deploy logs -f frontend  # 前端日志
docker compose --env-file .env.deploy logs -f db        # 数据库日志
```

### 备份数据
```bash
# 自动备份脚本
docker exec badminton-db pg_dump -U badminton badminton > backup_$(date +%Y%m%d).sql
```

### 更新代码（日常增量）

**详见 [DEPLOY_UPDATE.md](./DEPLOY_UPDATE.md)**，推荐流程：

1. 本机 `tar` 打包 + `scp` 上传  
2. OrcaTerm 解压（保留 `.env.deploy`）  
3. `docker compose --env-file .env.deploy up -d --build`  
4. `curl` 健康检查确认 `{"status":"ok"}`  

可选：`.\update-deploy.ps1`（Windows 一键，中文路径下可能有问题）

### 查看日志

| 项目 | 费用(月) | 说明 |
|-----|---------|-----|
| 云服务器 | 50元 | 2核4G，阿里云/腾讯云 |
| 域名 | 3元 | 30元/年 |
| AI API | 不定 | 按调用量，20次/分钟约￥50-100/月 |
| **总计** | **~100元/月** | 初期可更低 |

---

## ❓ 常见问题

### Q: 我没有服务器怎么办？
**A**: 
- 使用**云托管平台**（方案2），无需服务器
- 或我帮你申请**免费试用**（阿里云/腾讯云都有新用户免费套餐）

### Q: Docker是什么？需要学吗？
**A**:
- **不需要深入学**！我已经写好了所有配置
- 你只需要运行 `docker-compose up -d`
- Docker让部署标准化，避免"在我电脑上能跑"的问题

### Q: 域名必须买吗？
**A**:
- **测试阶段**: 不需要，直接用IP访问
- **正式上线**: 建议购买，更专业
- 域名约30元/年，很便宜

### Q: 数据安全吗？
**A**:
- 代码中已配置自动备份
- PostgreSQL数据持久化在Docker Volume
- 定期导出备份到本地

### Q: 能支持多少人同时用？
**A**: 2核4G配置大概能支持:
- 在线用户: 100-500人
- 并发请求: 50-100/秒
- 如果需要更大并发，可以升级配置或加负载均衡

### Q: 增量更新失败 / 后端 Restarting？
**A**: 见 [DEPLOY_UPDATE.md](./DEPLOY_UPDATE.md) 第五节「中断 / 失败恢复」。

---

## 💰 费用明细（云服务器方案）
