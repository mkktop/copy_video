<template>
  <div class="task-history">
    <el-table :data="tasks" style="width: 100%" max-height="500">
      <el-table-column prop="id" label="ID" width="60" />

      <el-table-column label="输入文件" min-width="150">
        <template #default="{ row }">
          {{ getFileName(row.input_path) }}
        </template>
      </el-table-column>

      <el-table-column label="输出文件" min-width="150">
        <template #default="{ row }">
          {{ getFileName(row.output_path) }}
        </template>
      </el-table-column>

      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="进度" width="120">
        <template #default="{ row }">
          <el-progress
            :percentage="Math.round(row.progress)"
            :status="row.status === 'completed' ? 'success' : undefined"
            :stroke-width="8"
          />
        </template>
      </el-table-column>

      <el-table-column label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>

      <el-table-column label="错误信息" min-width="150">
        <template #default="{ row }">
          <span v-if="row.error" class="error-text">{{ row.error }}</span>
          <span v-else class="no-error">-</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import type { Task } from '@/api/client'

defineProps<{
  tasks: Task[]
}>()

defineEmits<{
  refresh: []
}>()

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

const formatTime = (isoString: string): string => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.task-history {
  width: 100%;
}

.error-text {
  color: #f56c6c;
  font-size: 12px;
}

.no-error {
  color: #909399;
}
</style>
