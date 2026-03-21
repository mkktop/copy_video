#!/bin/bash
# 多架构单镜像构建和推送脚本
# 支持 x86_64 和 ARM64

set -e

# 配置
REGISTRY="docker.io/mkktop"  # 修改为你的 Docker Hub 用户名
IMAGE_NAME="copy-video"
VERSION="${1:-latest}"
PLATFORMS="linux/amd64,linux/arm64"

echo "================================"
echo "多架构单镜像构建脚本"
echo "================================"
echo "Registry: $REGISTRY"
echo "Image: $IMAGE_NAME"
echo "Version: $VERSION"
echo "Platforms: $PLATFORMS"
echo ""

# 检查 Docker buildx
echo "检查 Docker buildx..."
if ! docker buildx version &> /dev/null; then
    echo "错误: 需要 Docker buildx 支持"
    echo "请升级 Docker 到最新版本"
    exit 1
fi

# 创建 builder（如果不存在）
echo "创建 builder..."
docker buildx create --name multiarch-builder --use 2>/dev/null || true
docker buildx inspect --bootstrap

# 登录检查
echo "检查登录状态..."
if ! docker info | grep -q "Username"; then
    echo "请先登录 Docker Hub:"
    docker login
fi

# 构建单镜像
echo ""
echo "================================"
echo "构建单镜像（前端+后端）..."
echo "================================"

docker buildx build \
  --platform $PLATFORMS \
  -t $REGISTRY/$IMAGE_NAME:$VERSION \
  -t ghcr.io/mkktop/$IMAGE_NAME:$VERSION \
  --push \
  .

# 添加 latest 标签
if [ "$VERSION" != "latest" ]; then
    docker buildx build \
      --platform $PLATFORMS \
      -t $REGISTRY/$IMAGE_NAME:latest \
      -t ghcr.io/mkktop/$IMAGE_NAME:latest \
      --push \
      .
fi

echo ""
echo "================================"
echo "多架构镜像构建完成！"
echo "================================"
echo ""
echo "支持的架构:"
echo "  - linux/amd64  (x86_64)"
echo "  - linux/arm64  (ARM64/aarch64)"
echo ""
echo "镜像列表:"
echo "  - $REGISTRY/$IMAGE_NAME:$VERSION"
echo "  - ghcr.io/mkktop/$IMAGE_NAME:$VERSION"
echo ""
echo "现在可以在以下平台使用:"
echo "  - Windows PC (x86_64)"
echo "  - Linux 服务器 (x86_64)"
echo "  - ARM NAS (ARM64)"
echo "  - 树莓派 (ARM64)"
echo "  - 苹果 Mac M1/M2 (ARM64)"
