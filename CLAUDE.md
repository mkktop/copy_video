# Copy Video - 视频转码工具

通过 FFmpeg 复制流并修改元信息，改变视频文件哈希值的 Web 应用。

## 常用命令

### 开发环境

```bash
# 后端开发
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端开发
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
# 本地构建并启动
docker-compose up -d --build

# 使用预构建镜像
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 构建多架构镜像

```bash
# 使用 buildx 构建并推送（需要先登录 Docker Hub）
./buildx-push.sh
```

## 架构概览（单镜像版）

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker 容器 (:80)                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 Supervisor                           │    │
│  │         ┌──────────────┬──────────────┐             │    │
│  │         │              │              │             │    │
│  │         ▼              ▼              │             │    │
│  │  ┌──────────┐   ┌──────────┐         │             │    │
│  │  │  Nginx   │   │ FastAPI  │         │             │    │
│  │  │  (:80)   │──▶│ (:8000)  │         │             │    │
│  │  │ 静态文件  │   │ + FFmpeg │         │             │    │
│  │  └──────────┘   └──────────┘         │             │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│               ┌──────────▼──────────┐                       │
│               │   /app/workspace    │                       │
│               │   ├── input/ (输入)  │                       │
│               │   └── output/(输出)  │                       │
│               └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## 后端结构

```
backend/
├── app/
│   ├── main.py          # FastAPI 入口，CORS 配置，路由注册
│   ├── config.py        # 配置常量（路径、FFmpeg 设置）
│   ├── api/
│   │   ├── files.py     # 文件浏览 API
│   │   ├── transcode.py # 转码 API（SSE 进度流）
│   │   └── settings.py  # 设置 API（调度器控制）
│   ├── models/
│   │   ├── task.py      # 任务模型
│   │   └── settings.py  # 设置模型
│   ├── services/
│   │   ├── ffmpeg.py    # FFmpeg 转码逻辑（核心）
│   │   ├── file_service.py  # 文件扫描
│   │   ├── settings_service.py  # 配置持久化
│   │   └── scheduler.py # 自动扫描调度器
│   └── db/
│       └── database.py  # SQLite 数据库操作
└── Dockerfile
```

## 前端结构

```
frontend/
├── src/
│   ├── main.ts          # Vue 入口，Element Plus 注册
│   ├── App.vue          # 根组件（页面切换）
│   ├── api/
│   │   └── client.ts    # Axios 客户端，所有 API 调用
│   ├── views/
│   │   ├── Home.vue     # 主页面（文件浏览 + 转码面板）
│   │   └── Settings.vue # 设置页面
│   └── components/
│       ├── FileBrowser.vue     # 文件列表组件
│       ├── TranscodePanel.vue  # 转码控制面板
│       ├── MetadataConfig.vue  # 元数据配置表单
│       └── TaskHistory.vue     # 任务历史表格
├── vite.config.js       # Vite 配置（含 @ 别名）
└── Dockerfile
```

## 关键实现细节

### FFmpeg 转码命令

```bash
ffmpeg -i input.mp4 \
  -map 0 \              # 映射所有流（视频、音频、字幕）
  -c copy \             # 复制流，不重新编码
  -metadata title=... \ # 修改元数据
  -metadata encoder=CopyVideo-UUID \
  -movflags +faststart \# 重新组织容器
  output.mp4
```

### SSE 进度流

转码进度通过 Server-Sent Events 实时推送：
- 前端：`EventSource` 或 `fetch` + `ReadableStream`
- 后端：`StreamingResponse` + `text/event-stream`

### 配置持久化

设置保存在 `/app/data/settings.json`，包括：
- 输出目录
- 转码后是否删除源文件
- 自动扫描配置（间隔、目录）
- 默认元数据

## 端口

| 服务 | 容器端口 | 宿主端口 |
|-----|---------|---------|
| 单镜像服务 | 80 | 3799 |

## 支持的视频格式

`.mp4`, `.mkv`, `.avi`, `.mov`, `.flv`, `.wmv`, `.webm`, `.m4v`
