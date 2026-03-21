# Copy Video - 视频转码工具

基于Docker部署的视频转码Web应用，通过FFmpeg复制流并修改元信息，改变视频文件哈希值，使网盘认为是新文件。

## 功能特点

- **Web UI界面** - 简洁直观的Vue.js 3前端界面
- **文件浏览** - 可浏览任意目录，选择视频文件
- **批量转码** - 支持同时转码多个视频文件
- **实时进度** - SSE实时显示转码进度
- **无损转码** - 使用`-c copy`复制流，不重新编码
- **哈希修改** - 修改元数据和容器参数改变文件哈希值
- **自定义元数据** - 支持自定义标题、作者、简介等元数据
- **配置持久化** - 设置自动保存，重启后保持
- **自动扫描** - 定时扫描目录自动转码新文件
- **源文件管理** - 转码后可选择删除源文件
- **多平台支持** - 支持 x86/ARM 架构，可在 NAS 上运行
- **单镜像部署** - 前后端合并为单一Docker镜像，部署更简单

## 技术栈

- **后端**: FastAPI + Python 3.11 + FFmpeg
- **前端**: Vue.js 3 + Element Plus + Vite
- **部署**: Docker + Docker Compose + Nginx + Supervisor
- **支持**: Linux (x86/ARM), Windows, macOS

## 快速开始

### 方式一：使用预构建镜像（推荐）

```bash
# 1. 下载配置文件
wget https://raw.githubusercontent.com/mkktop/copy-video/main/docker-compose.yml

# 2. 启动服务
docker-compose up -d

# 3. 访问 http://localhost:3799
```

### 方式二：本地构建

```bash
# 克隆项目
git clone https://github.com/mkktop/copy-video.git
cd copy-video

# 构建并启动
docker-compose up -d --build

# 访问 http://localhost:3799
```

## 自动构建（GitHub Actions）

本项目已配置 GitHub Actions，推送到 GitHub 后会自动构建多架构 Docker 镜像：

- **触发条件**：推送到 `main`/`master` 分支，或创建 `v*` 标签
- **支持架构**：`linux/amd64` + `linux/arm64`
- **镜像仓库**：
  - Docker Hub: `mkktop/copy-video:latest`
  - GitHub: `ghcr.io/mkktop/copy-video:latest`

### 启用自动构建

1. 将代码推送到 GitHub
2. 进入仓库 Settings → Actions → General
3. 确保 "Workflow permissions" 设置为 "Read and write permissions"
4. 推送代码后自动触发构建

### 配置 Docker Hub（可选）

如需推送到 Docker Hub，在仓库 Settings → Secrets 添加：
- `DOCKERHUB_USERNAME` - Docker Hub 用户名
- `DOCKERHUB_TOKEN` - Docker Hub Access Token

## 目录结构

```
copy_video/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── main.py      # FastAPI入口
│   │   ├── api/         # API路由
│   │   ├── services/    # FFmpeg服务
│   │   └── db/          # 数据库
│   └── Dockerfile
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── views/      # 页面组件
│   │   ├── components/ # UI组件
│   │   └── api/        # API客户端
│   └── Dockerfile
├── nginx/               # Nginx配置
├── data/               # 数据目录
│   ├── workspace/      # 视频文件工作区
│   └── settings.json   # 配置文件
├── Dockerfile          # 单镜像构建文件
├── supervisord.conf    # 进程管理配置
├── docker-compose.yml  # Docker 部署配置
└── .github/workflows/  # GitHub Actions
```

## 使用说明

### 准备视频文件

```bash
# 创建目录
mkdir -p data/workspace/input

# 复制视频文件到输入目录
cp /path/to/your/videos/* data/workspace/input/
```

### 设置页面

点击顶部导航的"设置"按钮进入设置页面：

- **输出目录**：设置默认转码输出目录
- **转码后删除源文件**：转码成功后自动删除源视频文件
- **自动扫描**：定期扫描指定目录自动转码
- **默认元数据**：设置默认的元数据配置

### 文件浏览器

1. 左侧文件浏览器可浏览 `data/workspace` 目录
2. 点击文件夹名称进入目录
3. 勾选视频文件进行选择（支持多选）
4. 支持 .mp4, .mkv, .avi, .mov, .flv 等格式

### 转码操作

1. 在文件浏览器中选择要转码的视频
2. 右侧转码面板设置输出目录和元数据
3. 点击"开始转码"按钮
4. 实时查看转码进度
5. 转码完成后文件保存在输出目录

## 转码原理

程序通过以下方式改变文件哈希值：

1. **修改元数据**: 添加随机UUID或自定义元数据
2. **重组容器**: 使用`-movflags +faststart`重新组织MP4容器
3. **复制流**: 使用`-c copy`不重新编码，保持原画质

```bash
ffmpeg -i input.mp4 -map 0 -c copy \
       -metadata title="我的标题" \
       -metadata encoder="CopyVideo-xxxxx" \
       -movflags +faststart output.mp4
```

## API文档

启动服务后访问 http://localhost:3799/api/docs 查看完整API文档。

## 故障排除

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 进入容器检查
docker exec -it copy-video bash
ffmpeg -version
```

## 许可证

MIT License
