#!/bin/bash
# Copy Video 快速部署脚本
# 适用于 ARM Linux NAS

set -e

echo "================================"
echo "Copy Video 视频转码工具 - 部署脚本"
echo "================================"
echo ""

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker
echo "检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker 未安装，请先安装 Docker${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker 已安装${NC}"

# 检查 Docker Compose
echo "检查 Docker Compose..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}Docker Compose 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose 已安装${NC}"

# 获取当前目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 创建必要的目录
echo "创建数据目录..."
mkdir -p data/workspace/input
mkdir -p data/workspace/output
mkdir -p data/db
echo -e "${GREEN}✓ 目录创建完成${NC}"

# 检测架构
ARCH=$(uname -m)
echo "检测系统架构: $ARCH"
if [[ $ARCH == "aarch64"* ]] || [[ $ARCH == "armv8"* ]]; then
    echo -e "${GREEN}ARM64 架构 detected${NC}"
elif [[ $ARCH == "armv7"* ]]; then
    echo -e "${GREEN}ARMv7 架构 detected${NC}"
elif [[ $ARCH == "x86_64"* ]]; then
    echo -e "${GREEN}x86_64 架构 detected${NC}"
else
    echo -e "${YELLOW}未知架构: $ARCH，可能会遇到问题${NC}"
fi

# 询问端口配置
read -p "是否使用默认端口 8080？(y/n，默认 y): " USE_DEFAULT_PORT
USE_DEFAULT_PORT=${USE_DEFAULT_PORT:-y}

if [[ $USE_DEFAULT_PORT != "y"* ]]; then
    read -p "请输入端口号: " CUSTOM_PORT
    sed -i "s/8080:80/$CUSTOM_PORT:80/g" docker-compose.yml
    echo -e "${GREEN}✓ 端口已设置为 $CUSTOM_PORT${NC}"
fi

# 询问是否挂载外部视频目录
read -p "是否挂载外部视频目录？(y/n，默认 n): " MOUNT_EXTERNAL
MOUNT_EXTERNAL=${MOUNT_EXTERNAL:-n}

if [[ $MOUNT_EXTERNAL == "y"* ]]; then
    read -p "请输入视频目录的完整路径: " VIDEO_PATH
    if [[ -d "$VIDEO_PATH" ]]; then
        # 添加挂载到 docker-compose.yml
        sed -i "/volumes:/a\      - $VIDEO_PATH:/app/workspace/input" docker-compose.yml
        echo -e "${GREEN}✓ 已添加目录挂载: $VIDEO_PATH${NC}"
    else
        echo -e "${YELLOW}目录不存在，跳过挂载${NC}"
    fi
fi

# 构建并启动
echo ""
echo "开始构建镜像（首次运行需要几分钟）..."
if docker compose version &> /dev/null; then
    docker compose build
    docker compose up -d
else
    docker-compose build
    docker-compose up -d
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "访问地址: http://localhost:8080"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  重启服务: docker-compose restart"
echo "  停止服务: docker-compose stop"
echo ""
echo "详细文档请查看 README.md 和 NAS_DEPLOYMENT.md"
