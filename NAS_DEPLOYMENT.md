# NAS 部署指南 (ARM Linux)

本指南适用于在 ARM 架构的 NAS（如群晖 Synology、威联通 QNAP 等）上部署。

## 支持的 NAS 系统

- 群晖 (Synology) DSM 7.0+
- 威联通 (QNAP) QTS 4.0+
- 其他支持 Docker 的 Linux NAS

## 系统要求

- ARM 架构 (armv7, arm64)
- Docker 和 Docker Compose
- 最少 512MB RAM
- 至少 2GB 可用磁盘空间

## 快速部署

### 方法一：SSH 部署（推荐）

1. **通过 SSH 连接到 NAS**

```bash
ssh your-nas-user@nas-ip-address
```

2. **创建项目目录**

```bash
# 群晖
mkdir -p /volume1/docker/copy-video
cd /volume1/docker/copy-video

# 威联通
mkdir -p /share/CACHEDEV1_DATA/docker/copy-video
cd /share/CACHEDEV1_DATA/docker/copy-video
```

3. **下载项目文件**

将项目文件上传到 NAS，或使用 git：

```bash
# 如果 NAS 有 git
git clone https://github.com/your-repo/copy-video.git .

# 或使用 scp/sftp 从本地上传
```

4. **启动服务**

```bash
docker-compose up -d
```

### 方法二：群晖 Container Manager (DSM 7.2+)

1. 打开 **Container Manager**
2. 点击 **项目** → **新建**
3. 设置：
   - 项目名称：`copy-video`
   - 路径：选择项目文件夹
   - 来源：选择 `docker-compose.yml`
4. 点击 **完成**

### 方法三：威联通 Container Station

1. 打开 **Container Station**
2. 点击 **创建** → **应用程序**
3. 粘贴 `docker-compose.yml` 内容
4. 点击 **创建**

## 端口配置

默认使用 **3799** 端口

如需修改，编辑 `docker-compose.yml`：

```yaml
nginx:
  ports:
    - "9000:80"  # 改为其他端口
```

## 存储路径配置

### 群晖

```yaml
volumes:
  - /volume1/video/workspace:/app/workspace
  - /volume1/docker/copy-video/data:/app/data
```

### 威联通

```yaml
volumes:
  - /share/Multimedia/videos:/app/workspace
  - /share/CACHEDEV1_DATA/docker/copy-video:/app/data
```

## 目录挂载（重要）

编辑 `docker-compose.yml` 挂载你的视频目录：

```yaml
backend:
  volumes:
    - ./data/workspace:/app/workspace      # 工作区
    - /你的视频路径:/app/workspace/input   # 视频输入目录
    - ./data/db:/app/data                  # 数据库
```

## 访问地址

启动后访问：`http://nas-ip:3799`

## 性能优化

### ARM 设备性能较低

建议在设置中调整：

1. **降低转码并发**：一次只转码 1-2 个文件
2. **增加扫描间隔**：设置为 7200 秒（2小时）
3. **使用输出目录**：放在 SSD 上会更快

### 群晖优化

```bash
# 在 SSH 中运行，限制 CPU 使用
docker update --cpus="2.0" copy-video-backend
```

## 常见问题

### 1. 端口冲突

如果 3799 端口被占用，修改 `docker-compose.yml` 中的端口映射。

### 2. 权限问题

```bash
# 调整目录权限
chmod -R 755 /path/to/data/workspace
```

### 3. FFmpeg 速度慢

ARM 上 FFmpeg 转码速度较慢是正常的，使用 `-c copy` 模式不重新编码，速度较快。

### 4. 内存不足

```bash
# 限制容器内存
docker update --memory="512m" copy-video-backend
```

## 管理命令

```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose stop

# 更新项目
git pull
docker-compose up -d --build

# 清理重建
docker-compose down -v
docker-compose up -d
```

## 开机自启动

```bash
# 确保容器设置了自动重启
docker update --restart=unless-stopped copy-video-backend copy-video-frontend copy-video-nginx
```

## 硬件加速（高级）

如果你的 NAS 支持硬件转码（如 Intel QSV），可以修改 FFmpeg 命令使用硬件加速。

编辑 `backend/app/services/ffmpeg.py`，使用硬件加速编码器：

```python
# 使用 VAAPI (Intel)
cmd = [
    FFMPEG_PATH,
    "-vaapi_device", "/dev/dri/renderD128",
    "-i", str(input_path),
    "-c:v", "h264_vaapi",  # 硬件编码
    ...
]
```

## 备份建议

定期备份配置和数据库：

```bash
# 备份数据库
cp data/db/settings.json data/db/settings.json.backup

# 备份配置
tar czf backup.tar.gz docker-compose.yml nginx.conf data/db/
```
