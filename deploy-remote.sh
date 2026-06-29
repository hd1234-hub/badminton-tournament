#!/bin/bash
# 在服务器上执行：解压最新代码并重新构建 Docker 服务
set -e

ENV_FILE=".env.deploy"
ARCHIVE="badminton-deploy.tar"
BACKUP_DIR="backups"

echo "🏸 羽毛球赛事系统 - 远程更新部署"
echo "================================="

if ! command -v docker &> /dev/null; then
    echo "❌ 未安装 Docker"
    exit 1
fi

if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ 未安装 Docker Compose"
    exit 1
fi

if [ -f "$ARCHIVE" ]; then
    echo "📦 解压 $ARCHIVE ..."
    ENV_BACKUP=""
    if [ -f "$ENV_FILE" ]; then
        ENV_BACKUP="$(mktemp)"
        cp "$ENV_FILE" "$ENV_BACKUP"
    fi
    tar -xf "$ARCHIVE"
    if [ -n "$ENV_BACKUP" ] && [ -f "$ENV_BACKUP" ]; then
        cp "$ENV_BACKUP" "$ENV_FILE"
        rm -f "$ENV_BACKUP"
        echo "✅ 已保留服务器原有 .env.deploy"
    fi
fi

if [ ! -f "$ENV_FILE" ]; then
    if [ -f ".env.deploy.example" ]; then
        cp .env.deploy.example "$ENV_FILE"
        echo "⚠️  已从示例创建 $ENV_FILE，请先编辑后再部署"
        exit 1
    fi
    echo "❌ 缺少 $ENV_FILE"
    echo "   请在本机执行: scp .env.deploy ubuntu@服务器IP:~/羽毛球agent赛事/"
    exit 1
fi

chmod +x deploy.sh deploy-remote.sh backend/docker-entrypoint.sh 2>/dev/null || true

mkdir -p "$BACKUP_DIR"
if docker ps --format '{{.Names}}' | grep -qx badminton-db; then
    BACKUP_FILE="${BACKUP_DIR}/badminton-$(date +%Y%m%d-%H%M%S).sql"
    echo "💾 备份数据库到 $BACKUP_FILE ..."
    docker exec badminton-db pg_dump -U badminton badminton > "$BACKUP_FILE" || echo "⚠️  备份失败，继续部署"
fi

echo "🔨 构建并启动（使用 Docker 缓存，增量更新更快）..."
$COMPOSE_CMD --env-file "$ENV_FILE" up -d --build

echo "⏳ 等待服务就绪..."
sleep 8

echo "🔍 健康检查..."
if curl -fsS "http://127.0.0.1:8000/api/v1/health" >/dev/null; then
    echo "✅ 后端健康检查通过"
else
    echo "⚠️  后端健康检查失败，请查看日志:"
    echo "   $COMPOSE_CMD --env-file $ENV_FILE logs --tail=80 backend"
fi

if curl -fsS "http://127.0.0.1/" >/dev/null; then
    echo "✅ 前端访问正常"
else
    echo "⚠️  前端访问失败，请查看日志:"
    echo "   $COMPOSE_CMD --env-file $ENV_FILE logs --tail=80 frontend"
fi

echo ""
$COMPOSE_CMD --env-file "$ENV_FILE" ps
echo ""
echo "✅ 更新部署完成"
