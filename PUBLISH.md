# Docker 镜像发布指南

本文档说明如何构建和发布 Copy Video 的 Docker 镜像。

## 准备工作

### 1. 注册 Docker Hub 账号

访问 https://hub.docker.com/ 注册账号

### 2. 登录 Docker Hub

```bash
docker login
```

## 构建和推送镜像

### 方法一：使用脚本（推荐）

```bash
# 给脚本执行权限
chmod +x build-push.sh

# 构建并推送镜像（默认 latest 标签）
./build-push.sh

# 构建并推送指定版本
./build-push.sh v1.0.0
```

### 方法二：手动构建

#### 后端镜像

```bash
# 构建后端镜像
docker build -t your-username/copy-video-backend:latest ./backend

# 推送后端镜像
docker push your-username/copy-video-backend:latest

# 构建带版本标签的镜像
docker build -t your-username/copy-video-backend:v1.0.0 ./backend
docker push your-username/copy-video-backend:v1.0.0
```

#### 前端镜像

```bash
# 构建前端镜像
docker build -t your-username/copy-video-frontend:latest ./frontend

# 推送前端镜像
docker push your-username/copy-video-frontend:latest

# 构建带版本标签的镜像
docker build -t your-username/copy-video-frontend:v1.0.0 ./frontend
docker push your-username/copy-video-frontend:v1.0.0
```

## 修改配置

### 1. 修改 build-push.sh

```bash
# 修改为你的 Docker Hub 用户名
REGISTRY="docker.io/your-username"
```

### 2. 修改 docker-compose.prod.yml

```yaml
services:
  backend:
    image: your-username/copy-video-backend:latest

  frontend:
    image: your-username/copy-video-frontend:latest
```

## 发布流程

### 首次发布

```bash
# 1. 修改脚本中的用户名
vim build-push.sh

# 2. 构建并推送镜像
./build-push.sh

# 3. 更新 docker-compose.prod.yml
vim docker-compose.prod.yml

# 4. 提交到代码仓库
git add .
git commit -m "Release v1.0.0"
git tag v1.0.0
git push
```

### 版本更新

```bash
# 1. 修改版本号
./build-push.sh v1.1.0

# 2. 更新文档中的版本号
vim README.md

# 3. 提交
git tag v1.1.0
git push --tags
```

## 用户使用方式

### 方式一：使用预构建镜像（推荐）

用户提供 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  backend:
    image: your-username/copy-video-backend:latest
    volumes:
      - ./data/workspace:/app/workspace
      - ./data/db:/app/data
    restart: unless-stopped

  frontend:
    image: your-username/copy-video-frontend:latest
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

用户只需要：

```bash
# 下载配置文件
wget https://raw.githubusercontent.com/your-repo/copy-video/main/docker-compose.yml

# 启动
docker-compose up -d
```

### 方式二：单文件部署

创建一键部署脚本 `deploy.sh`：

```bash
#!/bin/bash
# Copy Video 一键部署脚本

IMAGE_PREFIX="your-username/copy-video"

docker run -d \
  --name copy-video \
  -p 8080:80 \
  -v $(pwd)/data:/app/data \
  -e TZ=Asia/Shanghai \
  $IMAGE_PREFIX-backend:latest

docker run -d \
  --name copy-video-frontend \
  --link copy-video:backend \
  $IMAGE_PREFIX-frontend:latest
```

## 多架构支持

### 使用 buildx 构建多架构镜像

```bash
# 创建 buildx builder
docker buildx create --name multiarch --use

# 启用 buildx
docker buildx inspect --bootstrap

# 构建并推送多架构镜像
docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-username/copy-video-backend:latest \
  --push ./backend

docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-username/copy-video-frontend:latest \
  --push ./frontend
```

## 镜像仓库选择

### Docker Hub（推荐）
- 地址：https://hub.docker.com/
- 免费账户有拉取限制
- 支持私有仓库

### 阿里云容器镜像服务
- 地址：https://cr.console.aliyun.com/
- 国内访问快
- 免费私有仓库

### GitHub Container Registry
- 地址：https://github.com/features/packages
- 与 GitHub 集成
- 免费公开仓库

## 自动化构建

### GitHub Actions 自动构建

创建 `.github/workflows/docker.yml`：

```yaml
name: Docker Image CI

on:
  push:
    branches: [ "main" ]
    tags: [ 'v*.*.*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Build backend
      run: docker build ./backend -t ${{ secrets.DOCKER_HUB_USERNAME }}/copy-video-backend:${{ github.ref_name }}

    - name: Build frontend
      run: docker build ./frontend -t ${{ secrets.DOCKER_HUB_USERNAME }}/copy-video-frontend:${{ github.ref_name }}

    - name: Login to Docker Hub
      run: echo "${{ secrets.DOCKER_HUB_TOKEN }}" | docker login -u "${{ secrets.DOCKER_HUB_USERNAME }}" --password-stdin

    - name: Push images
      run: |
        docker push ${{ secrets.DOCKER_HUB_USERNAME }}/copy-video-backend:${{ github.ref_name }}
        docker push ${{ secrets.DOCKER_HUB_USERNAME }}/copy-video-frontend:${{ github.ref_name }}
```

## 镜像大小优化

### 后端镜像优化

```dockerfile
# 使用更小的基础镜像
FROM python:3.11-alpine

# 只安装必要的依赖
RUN apk add --no-cache ffmpeg

# 合并 RUN 指令减少层数
RUN pip install --no-cache-dir fastapi uvicorn && \
    rm -rf /tmp/*
```

### 前端镜像优化

```dockerfile
# 使用多阶段构建
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

## 检查清单

发布前确认：

- [ ] 已修改 `REGISTRY` 为你的 Docker Hub 用户名
- [ ] 已更新 `docker-compose.prod.yml` 中的镜像地址
- [ ] 已测试镜像可以正常启动
- [ ] 已添加镜像标签和描述
- [ ] 已更新 README.md 中的拉取命令
