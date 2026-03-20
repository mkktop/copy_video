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

## 技术栈

- **后端**: FastAPI + Python 3.11 + FFmpeg
- **前端**: Vue.js 3 + Element Plus + Vite
- **部署**: Docker + Docker Compose + Nginx
- **支持**: Linux (x86/ARM), Windows, macOS

## 快速开始

### 方式一：使用预构建镜像（推荐）

直接拉取 GitHub Container Registry 的镜像，无需本地编译：

```bash
# 1. 下载配置文件
wget https://raw.githubusercontent.com/YOUR_USERNAME/copy-video/main/docker-compose.standalone.yml -O docker-compose.yml
wget https://raw.githubusercontent.com/YOUR_USERNAME/copy-video/main/nginx.conf

# 2. 编辑 docker-compose.yml，将 YOUR_USERNAME 替换为实际的 GitHub 用户名
sed -i 's/YOUR_USERNAME/your-actual-username/g' docker-compose.yml

# 3. 启动服务
docker-compose up -d

# 4. 访问 http://localhost:3799
```

### 方式二：本地构建

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/copy-video.git
cd copy-video

# 启动服务（自动构建镜像）
docker-compose up -d --build
```

## 自动构建（GitHub Actions）

本项目已配置 GitHub Actions，推送到 GitHub 后会自动构建多架构 Docker 镜像：

- **触发条件**：推送到 `main`/`master` 分支，或创建 `v*` 标签
- **支持架构**：`linux/amd64` + `linux/arm64`
- **镜像仓库**：GitHub Container Registry (ghcr.io)
- **镜像地址**：
  - 后端: `ghcr.io/YOUR_USERNAME/copy-video/backend:latest`
  - 前端: `ghcr.io/YOUR_USERNAME/copy-video/frontend:latest`

### 启用自动构建

1. 将代码推送到 GitHub
2. 进入仓库 Settings → Actions → General
3. 确保 "Workflow permissions" 设置为 "Read and write permissions"
4. 推送代码后自动触发构建

### 拉取镜像

```bash
# 登录 GitHub Container Registry（首次需要）
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# 拉取镜像
docker pull ghcr.io/YOUR_USERNAME/copy-video/backend:latest
docker pull ghcr.io/YOUR_USERNAME/copy-video/frontend:latest
```

### 1. 准备视频文件

将需要转码的视频文件放入 `data/workspace` 目录：

```bash
# 创建目录
mkdir -p data/workspace/input

# 复制视频文件到输入目录
cp /path/to/your/videos/* data/workspace/input/
```

### 2. 访问Web界面

打开浏览器访问: http://localhost:3799

> **NAS 用户**：请查看 [NAS 部署指南](NAS_DEPLOYMENT.md) 获取详细说明
>
> **镜像发布**：请查看 [发布指南](PUBLISH.md) 了解如何构建和发布镜像

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
├── data/               # 数据目录
│   ├── workspace/      # 视频文件工作区
│   └── db/            # SQLite数据库
├── docker-compose.yml  # Docker编排
└── nginx.conf         # Nginx配置
```

## 使用说明

### 设置页面（新增）

点击顶部导航的"设置"按钮进入设置页面，可配置以下内容：

#### 基本设置
- **输出目录**：设置默认转码输出目录
- **转码后删除源文件**：转码成功后自动删除源视频文件

#### 自动扫描（新增）
- **启用自动扫描**：开启后系统会定期扫描指定目录
- **扫描间隔**：设置扫描间隔时间（秒），建议3600秒（1小时）
- **扫描目录**：设置要自动扫描的输入目录
- **调度器控制**：可手动启动/停止调度器，或立即触发扫描
- **扫描历史**：显示已扫描的文件数量，可清空历史重新扫描

#### 默认元数据（新增）
设置默认的元数据配置，所有转码任务将使用这些配置：
- 标题、作者、专辑、年份、备注、简介、版权、类型
- 留空则自动生成随机值

### 文件浏览器

1. 左侧文件浏览器可浏览 `data/workspace` 目录
2. 点击文件夹名称进入目录
3. 勾选视频文件进行选择（支持多选）
4. 支持 .mp4, .mkv, .avi, .mov, .flv 等格式

### 转码操作

#### 手动转码
1. 在文件浏览器中选择要转码的视频
2. 右侧转码面板设置：
   - 输出目录（使用保存的默认值）
   - 是否使用自定义元数据
3. 点击"开始转码"按钮
4. 实时查看转码进度
5. 转码完成后文件保存在输出目录

#### 自动转码（新增）
1. 在设置页面启用自动扫描
2. 配置扫描目录和间隔
3. 将视频文件放入扫描目录
4. 系统自动检测新文件并转码
5. 如启用"转码后删除源文件"，成功转码后会自动删除源文件

### 查看输出文件

```bash
# 输出文件位于容器内的 /app/workspace/output
# 映射到主机的 data/workspace/output 目录
ls data/workspace/output/
```

## 转码原理

程序通过以下方式改变文件哈希值：

1. **修改元数据**: 添加随机UUID或自定义元数据
2. **重组容器**: 使用`-movflags +faststart`重新组织MP4容器
3. **复制流**: 使用`-c copy`不重新编码，保持原画质

### 元数据字段

支持的元数据字段（可自定义或留空自动生成）：

| 字段 | 说明 | FFmpeg对应 |
|------|------|-----------|
| title | 视频标题 | metadata title |
| author | 作者 | metadata artist |
| album | 专辑 | metadata album |
| year | 年份 | metadata date |
| comment | 备注 | metadata comment |
| description | 简介 | metadata description |
| copyright | 版权 | metadata copyright |
| genre | 类型 | metadata genre |
| custom | 自定义键值对 | metadata key=value |

转码命令示例：
```bash
ffmpeg -i input.mp4 -c copy \
       -metadata title="我的标题" \
       -metadata author="作者名" \
       -metadata comment="转码版本" \
       -metadata encoder="CopyVideo-xxxxx" \
       -metadata transcoded_at="2024-xx-xx" \
       -movflags +faststart output.mp4
```

## 配置说明

### 修改工作目录

编辑 `docker-compose.yml`:

```yaml
services:
  backend:
    volumes:
      - /your/custom/path:/app/workspace  # 修改这里
```

### 修改端口

默认端口为 **3799**，可在 `docker-compose.yml` 中修改：

```yaml
services:
  nginx:
    ports:
      - "9000:80"  # 改为其他端口
```

## API文档

启动服务后访问 http://localhost/api/docs 查看完整API文档。

### 主要端点

#### 文件操作
- `GET /api/files/browse` - 浏览文件
- `GET /api/files/validate-path` - 验证路径有效性

#### 转码操作
- `POST /api/transcode/start` - 开始转码
- `GET /api/transcode/tasks` - 获取任务列表
- `GET /api/transcode/tasks/{id}` - 获取单个任务
- `GET /api/transcode/progress/{id}` - 获取转码进度（SSE）
- `DELETE /api/transcode/tasks/{id}` - 取消任务

#### 设置操作（新增）
- `GET /api/settings/` - 获取设置
- `POST /api/settings/` - 保存设置
- `GET /api/settings/scheduler/status` - 获取调度器状态
- `POST /api/settings/scheduler/start` - 启动调度器
- `POST /api/settings/scheduler/stop` - 停止调度器
- `POST /api/settings/scheduler/scan-now` - 立即扫描
- `DELETE /api/settings/scan-history` - 清空扫描历史

## 故障排除

### 服务无法启动

```bash
# 查看服务状态
docker-compose ps

# 查看错误日志
docker-compose logs backend
docker-compose logs frontend
```

### FFmpeg错误

```bash
# 进入后端容器检查FFmpeg
docker exec -it copy-video-backend bash
ffmpeg -version
```

### 文件权限问题

```bash
# 确保data目录有写权限
chmod -R 755 data/
```

## 开发说明

### 本地开发后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 本地开发前端

```bash
cd frontend
npm install
npm run dev
```

## 许可证

MIT License
