#!/bin/bash
# 生产部署脚本
# 使用方法: ./deploy.sh

set -e

ENV_FILE=".env.deploy"

echo "🏸 羽毛球赛事系统部署脚本"
echo "==========================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ 请先安装 Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  未找到 $ENV_FILE，从示例创建..."
    cp .env.deploy.example "$ENV_FILE"
    echo "📝 请编辑 $ENV_FILE，设置实际的环境变量后再运行"
    echo "   特别需要修改: DB_PASSWORD, SECRET_KEY, ANTHROPIC_AUTH_TOKEN, CORS_ORIGINS"
    exit 1
fi

# 生成随机密钥（如果没有设置）
if grep -q "change_this_to_64_character_random_string" "$ENV_FILE"; then
    echo "🔑 生成随机密钥..."
    NEW_KEY=$(openssl rand -hex 32)
    sed -i "s/change_this_to_64_character_random_string/$NEW_KEY/g" "$ENV_FILE"
    echo "   已自动生成SECRET_KEY"
fi

if grep -q "change_me_very_strong_password" "$ENV_FILE"; then
    echo "⚠️  请修改 $ENV_FILE 中的数据库密码!"
    echo "   当前使用的是默认密码，不安全"
fi

echo ""
echo "🚀 开始部署..."

mkdir -p backups
if docker ps --format '{{.Names}}' | grep -qx badminton-db; then
    BACKUP_FILE="backups/badminton-$(date +%Y%m%d-%H%M%S).sql"
    echo "💾 备份数据库到 $BACKUP_FILE ..."
    docker exec badminton-db pg_dump -U badminton badminton > "$BACKUP_FILE" || echo "⚠️  备份失败，继续部署"
fi

# 构建并启动服务
echo "📦 构建Docker镜像..."
$COMPOSE_CMD --env-file "$ENV_FILE" build

echo "🚀 启动服务..."
$COMPOSE_CMD --env-file "$ENV_FILE" up -d

# 等待数据库就绪
echo "⏳ 等待数据库初始化..."
sleep 8

if curl -fsS "http://127.0.0.1:8000/api/v1/health" >/dev/null; then
    echo "✅ 后端健康检查通过"
else
    echo "⚠️  后端健康检查失败"
fi

# 检查服务状态
echo ""
echo "🔍 检查服务状态..."
$COMPOSE_CMD --env-file "$ENV_FILE" ps

echo ""
echo "✅ 部署完成!"
echo ""
echo "📱 访问地址:"
echo "   前端: http://localhost"
echo "   后端API: http://localhost:8000"
echo ""
echo "📊 常用命令:"
echo "   查看日志: $COMPOSE_CMD --env-file $ENV_FILE logs -f"
echo "   停止服务: $COMPOSE_CMD --env-file $ENV_FILE down"
echo "   重启服务: $COMPOSE_CMD --env-file $ENV_FILE restart"
echo "   更新代码: $COMPOSE_CMD --env-file $ENV_FILE up -d --build"
echo ""
echo "💾 数据备份:"
echo "   docker exec badminton-db pg_dump -U badminton badminton > backup.sql"
