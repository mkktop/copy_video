<template>
  <div class="transcode-panel">
    <!-- Output Configuration -->
    <div class="config-section">
      <h4><el-icon><Setting /></el-icon> 输出配置</h4>
      <el-form label-width="100px" size="small">
        <el-form-item label="输出目录">
          <el-input
            v-model="outputDir"
            placeholder="/app/workspace/output"
            clearable
          >
            <template #append>
              <el-button @click="useDefaultOutput">默认</el-button>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="useMetadata" @change="handleMetadataToggle">
            自定义元数据（用于改变文件哈希）
          </el-checkbox>
        </el-form-item>
      </el-form>
    </div>

    <!-- Metadata Configuration (collapsible) -->
    <el-collapse v-if="useMetadata" class="metadata-section">
      <el-collapse-item title="元数据配置" name="metadata">
        <MetadataConfig ref="metadataConfigRef" @update="handleMetadataUpdate" />
      </el-collapse-item>
    </el-collapse>

    <!-- Action Buttons -->
    <div class="action-section">
      <el-button
        type="primary"
        size="large"
        :disabled="selectedFiles.size === 0"
        @click="handleStartTranscode"
        :loading="processing"
      >
        <el-icon><VideoCamera /></el-icon>
        开始转码 ({{ selectedFiles.size }})
      </el-button>
      <el-button size="large" @click="$emit('refresh-tasks')">
        <el-icon><Refresh /></el-icon> 刷新任务
      </el-button>
    </div>

    <!-- Active Tasks -->
    <div class="tasks-section">
      <h4><el-icon><List /></el-icon> 进行中的任务</h4>
      <div v-if="activeTasks.length === 0" class="empty-state">
        <el-empty description="暂无进行中的任务" />
      </div>
      <div v-else class="task-list">
        <div
          v-for="task in activeTasks"
          :key="task.id"
          class="task-item"
        >
          <div class="task-info">
            <div class="task-name">{{ getFileName(task.input_path) }}</div>
            <div class="task-status">
              <el-tag :type="getStatusType(task.status)" size="small">
                {{ getStatusText(task.status) }}
              </el-tag>
            </div>
          </div>
          <el-progress
            :percentage="Math.round(task.progress)"
            :status="task.status === 'completed' ? 'success' : undefined"
          />
          <div class="task-actions">
            <el-button
              v-if="task.status === 'processing'"
              type="danger"
              size="small"
              link
              @click="$emit('cancel-task', task.id)"
            >
              取消
            </el-button>
            <span class="output-path">{{ getFileName(task.output_path) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Completed Tasks -->
    <el-collapse v-if="completedTasks.length > 0" class="completed-section">
      <el-collapse-item title="已完成任务" name="completed">
        <div class="task-list">
          <div
            v-for="task in completedTasks"
            :key="task.id"
            class="task-item completed"
          >
            <div class="task-info">
              <div class="task-name">{{ getFileName(task.input_path) }}</div>
              <el-tag type="success" size="small">完成</el-tag>
            </div>
            <div class="task-meta">
              <span class="output-path">→ {{ getFileName(task.output_path) }}</span>
            </div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- Failed Tasks -->
    <el-collapse v-if="failedTasks.length > 0" class="failed-section">
      <el-collapse-item title="失败任务" name="failed">
        <div class="task-list">
          <div
            v-for="task in failedTasks"
            :key="task.id"
            class="task-item failed"
          >
            <div class="task-info">
              <div class="task-name">{{ getFileName(task.input_path) }}</div>
              <el-tag type="danger" size="small">失败</el-tag>
            </div>
            <div class="error-message">{{ task.error }}</div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, VideoCamera, Refresh, List } from '@element-plus/icons-vue'
import MetadataConfig from './MetadataConfig.vue'
import type { Task, MetadataConfig as MetadataConfigType } from '@/api/client'

const props = defineProps<{
  selectedFiles: Set<string>
  currentPath: string
  tasks: Task[]
}>()

const emit = defineEmits<{
  transcode: [config: { outputDir: string; metadata?: MetadataConfigType }]
  'cancel-task': [taskId: number]
  'refresh-tasks': []
}>()

const outputDir = ref('/app/workspace/output')
const processing = ref(false)
const useMetadata = ref(false)
const metadataConfig = ref<MetadataConfigType>({})
const metadataConfigRef = ref<InstanceType<typeof MetadataConfig>>()

// Load saved settings on mount
const loadSavedSettings = async () => {
  try {
    const { api } = await import('@/api/client')
    const response = await api.getSettings()
    const settings = response.data

    // Load saved output directory
    if (settings.output_dir) {
      outputDir.value = settings.output_dir
    }

    // Load saved metadata
    if (settings.metadata_title || settings.metadata_author || settings.metadata_year) {
      useMetadata.value = true
      const saved: MetadataConfigType = {}
      if (settings.metadata_title) saved.title = settings.metadata_title
      if (settings.metadata_author) saved.author = settings.metadata_author
      if (settings.metadata_album) saved.album = settings.metadata_album
      if (settings.metadata_year) saved.year = settings.metadata_year
      if (settings.metadata_comment) saved.comment = settings.metadata_comment
      if (settings.metadata_description) saved.description = settings.metadata_description
      if (settings.metadata_copyright) saved.copyright = settings.metadata_copyright
      if (settings.metadata_genre) saved.genre = settings.metadata_genre
      metadataConfig.value = saved
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
  }
}

// Load settings on mount
loadSavedSettings()

const activeTasks = computed(() =>
  props.tasks.filter(t => t.status === 'processing' || t.status === 'pending')
)

const completedTasks = computed(() =>
  props.tasks.filter(t => t.status === 'completed')
)

const failedTasks = computed(() =>
  props.tasks.filter(t => t.status === 'failed')
)

const useDefaultOutput = () => {
  outputDir.value = '/app/workspace/output'
}

const handleMetadataToggle = (checked: boolean) => {
  if (!checked) {
    metadataConfig.value = {}
  }
}

const handleMetadataUpdate = (metadata: MetadataConfigType) => {
  metadataConfig.value = metadata
}

const handleStartTranscode = () => {
  if (!outputDir.value) {
    ElMessage.warning('请设置输出目录')
    return
  }

  const config: { outputDir: string; metadata?: MetadataConfigType } = {
    outputDir: outputDir.value
  }

  if (useMetadata.value && metadataConfig.value) {
    config.metadata = metadataConfig.value
  }

  emit('transcode', config)
}

const getFileName = (path: string): string => {
  return path.split('/').pop() || path
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}
</script>

<style scoped>
.transcode-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-section h4,
.tasks-section h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
}

.metadata-section {
  border: 1px solid #ebeef5;
  border-radius: 6px;
}

.action-section {
  display: flex;
  gap: 10px;
  padding: 15px 0;
  border-top: 1px solid #ebeef5;
  border-bottom: 1px solid #ebeef5;
}

.tasks-section {
  flex: 1;
  overflow-y: auto;
}

.empty-state {
  padding: 20px 0;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.task-item.completed {
  border-left-color: #67c23a;
}

.task-item.failed {
  border-left-color: #f56c6c;
}

.task-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-name {
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 12px;
}

.output-path {
  color: #909399;
  font-size: 12px;
}

.error-message {
  margin-top: 8px;
  padding: 8px;
  background: #fef0f0;
  color: #f56c6c;
  border-radius: 4px;
  font-size: 12px;
}

.task-meta {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.completed-section,
.failed-section {
  margin-top: 10px;
}
</style>
