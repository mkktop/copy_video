<template>
  <div class="home-view">
    <el-row :gutter="20">
      <!-- File Browser Section -->
      <el-col :span="12">
        <el-card class="file-browser-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Folder /></el-icon> 文件浏览器</span>
              <el-breadcrumb separator="/">
                <el-breadcrumb-item @click="navigateTo('.', -1)">根目录</el-breadcrumb-item>
                <el-breadcrumb-item
                  v-for="(part, index) in pathParts"
                  :key="index"
                  @click="navigateTo(part, index)"
                >
                  {{ part }}
                </el-breadcrumb-item>
              </el-breadcrumb>
            </div>
          </template>

          <FileBrowser
            :current-path="currentPath"
            :files="currentFiles"
            :loading="loadingFiles"
            :selected-files="selectedFiles"
            @navigate="handleNavigate"
            @select-file="handleSelectFile"
            @refresh="loadFiles"
          />
        </el-card>
      </el-col>

      <!-- Transcode Panel Section -->
      <el-col :span="12">
        <el-card class="transcode-card">
          <template #header>
            <span><el-icon><Operation /></el-icon> 转码面板</span>
          </template>

          <TranscodePanel
            :selected-files="selectedFiles"
            :current-path="currentPath"
            :tasks="tasks"
            @transcode="handleTranscode"
            @cancel-task="handleCancelTask"
            @refresh-tasks="loadTasks"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- Task History Dialog -->
    <el-dialog v-model="showHistory" title="转码历史" width="800px">
      <TaskHistory :tasks="allTasks" @refresh="loadAllTasks" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Folder, Operation } from '@element-plus/icons-vue'
import FileBrowser from '@/components/FileBrowser.vue'
import TranscodePanel from '@/components/TranscodePanel.vue'
import TaskHistory from '@/components/TaskHistory.vue'
import api, { type FileInfo, type Task } from '@/api/client'

const currentPath = ref('.')
const currentFiles = ref<FileInfo[]>([])
const loadingFiles = ref(false)
const selectedFiles = ref<Set<string>>(new Set())
const tasks = ref<Task[]>([])
const allTasks = ref<Task[]>([])
const showHistory = ref(false)

const pathParts = computed(() => {
  if (currentPath.value === '.') return []
  return currentPath.value.split('/')
})

// Load files from server
const loadFiles = async () => {
  loadingFiles.value = true
  try {
    const response = await api.browseFiles(currentPath.value)
    currentFiles.value = response.data.files
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载文件失败')
  } finally {
    loadingFiles.value = false
  }
}

// Navigate to directory
const handleNavigate = (path: string) => {
  if (path === '..') {
    const parts = currentPath.value.split('/')
    parts.pop()
    currentPath.value = parts.join('/') || '.'
  } else {
    currentPath.value = path
  }
  selectedFiles.value.clear()
  loadFiles()
}

const navigateTo = (path: string, index: number) => {
  if (path === '.') {
    currentPath.value = '.'
  } else {
    // Navigate to specific path segment
    const parts = currentPath.value.split('/')
    currentPath.value = parts.slice(0, index + 1).join('/')
  }
  selectedFiles.value.clear()
  loadFiles()
}

// Handle file selection
const handleSelectFile = (file: FileInfo, selected: boolean) => {
  if (selected) {
    selectedFiles.value.add(file.path)
  } else {
    selectedFiles.value.delete(file.path)
  }
}

// Handle transcode request
const handleTranscode = async (config: { outputDir: string; metadata?: any }) => {
  if (selectedFiles.value.size === 0) {
    ElMessage.warning('请先选择要转码的视频文件')
    return
  }

  for (const inputFile of selectedFiles.value) {
    try {
      const requestData: any = {
        input_path: inputFile,
        output_dir: config.outputDir
      }

      // Add metadata if provided
      if (config.metadata) {
        requestData.metadata = config.metadata
      }

      const response = await api.startTranscode(requestData)

      const newTask = response.data
      tasks.value.unshift(newTask)
      ElMessage.success(`已添加转码任务: ${newTask.input_path}`)

      // Start monitoring progress
      monitorTask(newTask.id)
    } catch (error: any) {
      ElMessage.error(`添加任务失败: ${error.response?.data?.detail || error.message}`)
    }
  }

  selectedFiles.value.clear()
  await loadAllTasks()
}

// Monitor task progress
const monitorTask = async (taskId: number) => {
  try {
    const response = await api.getTranscodeProgress(taskId)
    const reader = new Response(response.data).body?.getReader()

    if (!reader) return

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            updateTaskProgress(taskId, data)
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  } catch (error) {
    console.error('Progress monitoring error:', error)
  }
}

const updateTaskProgress = (taskId: number, data: any) => {
  const taskIndex = tasks.value.findIndex(t => t.id === taskId)
  if (taskIndex !== -1) {
    if (data.task) {
      tasks.value[taskIndex] = data.task
    } else if (data.progress !== undefined) {
      tasks.value[taskIndex].progress = data.progress
      tasks.value[taskIndex].status = data.status === 'processing' ? 'processing' : tasks.value[taskIndex].status
    }

    if (data.status === 'done' || data.status === 'error' || data.status === 'completed') {
      loadTasks()
    }
  }
}

// Cancel task
const handleCancelTask = async (taskId: number) => {
  try {
    await api.cancelTask(taskId)
    ElMessage.success('任务已取消')
    await loadTasks()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '取消任务失败')
  }
}

// Load tasks
const loadTasks = async () => {
  try {
    const response = await api.getTasks(10)
    tasks.value = response.data
  } catch (error: any) {
    console.error('Load tasks error:', error)
  }
}

const loadAllTasks = async () => {
  try {
    const response = await api.getTasks(100)
    allTasks.value = response.data
  } catch (error: any) {
    console.error('Load all tasks error:', error)
  }
}

onMounted(() => {
  loadFiles()
  loadTasks()
  loadAllTasks()
})
</script>

<style scoped>
.home-view {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.file-browser-card,
.transcode-card {
  height: calc(100vh - 180px);
}

.file-browser-card :deep(.el-card__body),
.transcode-card :deep(.el-card__body) {
  height: calc(100% - 60px);
  overflow-y: auto;
}

:deep(.el-breadcrumb__item) {
  cursor: pointer;
}

:deep(.el-breadcrumb__item:hover .el-breadcrumb__inner) {
  color: #409eff;
}
</style>
