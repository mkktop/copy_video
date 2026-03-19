#!/bin/bash
# 镜像构建和推送脚本

set -e

# 配置镜像名称和标签
REGISTRY="docker.io/your-username"  # 修改为你的 Docker Hub 用户名
IMAGE_NAME="copy-video"
VERSION="${1:-latest}"

# 镜像列表
IMAGES=("backend" "frontend")

echo "================================"
echo "Copy Video 镜像构建脚本"
echo "================================"
echo "Registry: $REGISTRY"
echo "Version: $VERSION"
echo ""

# 检查是否已登录 Docker Hub
echo "检查 Docker 登录状态..."
if ! docker info | grep -q "Username"; then
    echo "请先登录 Docker Hub:"
    docker login
fi

# 构建并推送镜像
for SERVICE in "${IMAGES[@]}"; do
    echo ""
    echo "================================"
    echo "构建 $SERVICE 镜像..."
    echo "================================"

    IMAGE="$REGISTRY/$IMAGE_NAME-$SERVICE:$VERSION"

    # 构建
    docker build -t $IMAGE ./$SERVICE

    # 添加 latest 标签
    if [ "$VERSION" != "latest" ]; then
        docker tag $IMAGE "$REGISTRY/$IMAGE_NAME-$SERVICE:latest"
    fi

    # 推送
    echo "推送 $SERVICE 镜像..."
    docker push $IMAGE

    if [ "$VERSION" != "latest" ]; then
        docker push "$REGISTRY/$IMAGE_NAME-$SERVICE:latest"
    fi

    echo -e "✓ $SERVICE 镜像构建完成: $IMAGE"
done

echo ""
echo "================================"
echo "所有镜像构建完成！"
echo "================================"
echo ""
echo "镜像列表:"
for SERVICE in "${IMAGES[@]}"; do
    echo "  - $REGISTRY/$IMAGE_NAME-$SERVICE:$VERSION"
done
echo ""
echo "用户可以通过以下命令拉取:"
echo "  docker-compose pull"
