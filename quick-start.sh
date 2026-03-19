#!/bin/bash
# Copy Video 一键部署脚本
# 使用预构建镜像，无需本地编译

set -e

# 配置
IMAGE_PREFIX="your-username/copy-video"  # 替换为你的镜像前缀
VERSION="latest"
PORT="8080"

echo "================================"
echo "Copy Video 一键部署脚本"
echo "================================"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误: 未安装 Docker"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo "错误: 未安装 Docker Compose"
    exit 1
fi

# 创建目录
echo "创建数据目录..."
mkdir -p data/workspace/input
mkdir -p data/workspace/output
mkdir -p data/db

# 创建 docker-compose.yml
echo "创建 docker-compose.yml..."
cat > docker-compose.yml <<EOF
version: '3.8'

services:
  backend:
    image: ${IMAGE_PREFIX}-backend:${VERSION}
    container_name: copy-video-backend
    volumes:
      - ./data/workspace:/app/workspace
      - ./data/db:/app/data
    environment:
      - PYTHONUNBUFFERED=1
      - TZ=\${TZ:-Asia/Shanghai}
    restart: unless-stopped

  frontend:
    image: ${IMAGE_PREFIX}-frontend:${VERSION}
    container_name: copy-video-frontend
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: copy-video-nginx
    ports:
      - "${PORT}:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
EOF

# 创建 nginx.conf
echo "创建 nginx.conf..."
cat > nginx.conf <<'NGINX_CONF'
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:80;
}

server {
    listen 80;
    server_name localhost;
    client_max_body_size 1G;

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://backend/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
        proxy_connect_timeout 3600s;
    }

    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
NGINX_CONF

# 拉取镜像
echo ""
echo "拉取 Docker 镜像..."
if docker compose version &> /dev/null 2>&1; then
    docker compose pull
else
    docker-compose pull
fi

# 启动服务
echo ""
echo "启动服务..."
if docker compose version &> /dev/null 2>&1; then
    docker compose up -d
else
    docker-compose up -d
fi

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "检查服务状态..."
if docker compose version &> /dev/null 2>&1; then
    docker compose ps
else
    docker-compose ps
fi

echo ""
echo "================================"
echo "部署完成！"
echo "================================"
echo ""
echo "访问地址: http://localhost:${PORT}"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  重启服务: docker-compose restart"
echo "  停止服务: docker-compose stop"
echo "  删除服务: docker-compose down"
echo ""
echo "数据目录:"
echo "  视频工作区: ./data/workspace"
echo "  数据库: ./data/db"
echo ""
