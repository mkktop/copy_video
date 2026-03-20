<template>
  <div class="file-browser">
    <!-- Toolbar -->
    <div class="toolbar">
      <el-button-group>
        <el-button size="small" @click="$emit('refresh')" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <el-button size="small" @click="selectAll">全选</el-button>
        <el-button size="small" @click="clearSelection">清空</el-button>
      </el-button-group>
      <span class="selection-count">已选择: {{ selectedFiles.size }} 个文件</span>
    </div>

    <!-- Parent directory link -->
    <div v-if="currentPath !== '.'" class="parent-dir">
      <el-link @click="$emit('navigate', '..')">
        <el-icon><Back /></el-icon> 返回上级
      </el-link>
    </div>

    <!-- File list -->
    <el-table
      :data="files"
      style="width: 100%"
      @row-click="handleRowClick"
      v-loading="loading"
      height="calc(100% - 100px)"
    >
      <el-table-column type="selection" width="50" :selectable="isSelectable" />

      <el-table-column label="名称" min-width="200">
        <template #default="{ row }">
          <div class="file-name">
            <el-icon v-if="row.is_dir"><Folder /></el-icon>
            <el-icon v-else><VideoCamera /></el-icon>
            <span>{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="大小" width="120" align="right">
        <template #default="{ row }">
          {{ row.is_dir ? '-' : formatSize(row.size) }}
        </template>
      </el-table-column>

      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          {{ row.is_dir ? '文件夹' : row.extension.toUpperCase() }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.is_dir"
            type="primary"
            size="small"
            link
            @click.stop="$emit('navigate', row.path)"
          >
            打开
          </el-button>
          <el-checkbox
            v-else
            :model-value="selectedFiles.has(row.path)"
            @change="(val: boolean) => $emit('select-file', row, val)"
          >
            选择
          </el-checkbox>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { type PropType } from 'vue'
import { Refresh, Back, Folder, VideoCamera } from '@element-plus/icons-vue'
import type { FileInfo } from '@/api/client'

defineProps({
  currentPath: String,
  files: Array as PropType<FileInfo[]>,
  loading: Boolean,
  selectedFiles: Set as PropType<Set<string>>
})

const emit = defineEmits<{
  navigate: [path: string]
  selectFile: [file: FileInfo, selected: boolean]
  refresh: []
}>()

const isSelectable = (row: FileInfo) => !row.is_dir

const handleRowClick = (row: FileInfo) => {
  if (row.is_dir) {
    emit('navigate', row.path)
  }
}

const selectAll = () => {
  for (const file of (props.files || [])) {
    if (!file.is_dir) {
      emit('select-file', file, true)
    }
  }
}

const clearSelection = () => {
  for (const file of (props.files || [])) {
    if (selectedFiles.value.has(file.path)) {
      emit('select-file', file, false)
    }
  }
}

const formatSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.file-browser {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 10px;
}

.selection-count {
  font-size: 14px;
  color: #909399;
}

.parent-dir {
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 10px;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>
