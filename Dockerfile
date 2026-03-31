# 多阶段构建 - 单镜像版本

# 阶段1: 构建前端
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# 阶段2: 最终镜像
FROM python:3.11-slim

# 安装 FFmpeg、Nginx、Supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && adduser --system --no-create-home --group nginx || true

# 设置工作目录
WORKDIR /app

# 复制后端依赖并安装
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/app ./app

# 从构建阶段复制前端产物
COPY --from=frontend-builder /app/frontend/dist /var/www/html

# 复制 Nginx 配置
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# 复制 Supervisor 配置
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 创建数据和日志目录
RUN mkdir -p /app/data /app/workspace/input /app/workspace/output \
    && mkdir -p /var/log/supervisor \
    && mkdir -p /var/log/nginx \
    && chown -R nginx:nginx /var/log/nginx

# 暴露端口
EXPOSE 80

# 使用 Supervisor 启动多进程
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
