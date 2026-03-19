<template>
  <div class="metadata-config">
    <el-form label-width="100px" size="small">
      <el-form-item label="标题">
        <el-input v-model="localMetadata.title" placeholder="视频标题" clearable />
      </el-form-item>

      <el-form-item label="作者">
        <el-input v-model="localMetadata.author" placeholder="作者名称" clearable />
      </el-form-item>

      <el-form-item label="专辑">
        <el-input v-model="localMetadata.album" placeholder="专辑名称" clearable />
      </el-form-item>

      <el-form-item label="年份">
        <el-input-number
          v-model="localMetadata.year"
          :min="1900"
          :max="2100"
          placeholder="年份"
          controls-position="right"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="简介">
        <el-input
          v-model="localMetadata.description"
          type="textarea"
          :rows="2"
          placeholder="视频简介"
          clearable
        />
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="localMetadata.comment"
          placeholder="备注信息"
          clearable
        />
      </el-form-item>

      <el-form-item label="版权">
        <el-input v-model="localMetadata.copyright" placeholder="版权信息" clearable />
      </el-form-item>

      <el-form-item label="类型">
        <el-select v-model="localMetadata.genre" placeholder="选择类型" clearable style="width: 100%">
          <el-option label="电影" value="Movie" />
          <el-option label="电视节目" value="TV Show" />
          <el-option label="音乐视频" value="Music Video" />
          <el-option label="纪录片" value="Documentary" />
          <el-option label="动画" value="Animation" />
          <el-option label="其他" value="Other" />
        </el-select>
      </el-form-item>

      <!-- Custom metadata -->
      <el-form-item label="自定义">
        <div class="custom-metadata">
          <div
            v-for="(custom, index) in customEntries"
            :key="index"
            class="custom-entry"
          >
            <el-input
              v-model="custom.key"
              placeholder="键名"
              size="small"
              style="width: 120px"
            />
            <el-input
              v-model="custom.value"
              placeholder="值"
              size="small"
              style="flex: 1"
            />
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              circle
              @click="removeCustom(index)"
            />
          </div>
          <el-button
            type="primary"
            size="small"
            :icon="Plus"
            @click="addCustom"
            style="width: 100%; margin-top: 8px"
          >
            添加自定义项
          </el-button>
        </div>
      </el-form-item>

      <el-form-item>
        <el-button @click="resetMetadata" style="width: 100%">
          重置为默认
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Delete, Plus } from '@element-plus/icons-vue'
import type { MetadataConfig } from '@/api/client'

const emit = defineEmits<{
  update: [metadata: MetadataConfig]
}>()

const localMetadata = ref<MetadataConfig>({
  title: '',
  author: '',
  album: '',
  year: undefined,
  comment: '',
  description: '',
  copyright: '',
  genre: '',
  custom: {}
})

const customEntries = ref<Array<{ key: string; value: string }>>([])

// Emit updates when metadata changes
watch(localMetadata, () => {
  emit('update', getMetadata())
}, { deep: true })

watch(customEntries, () => {
  const custom: Record<string, string> = {}
  for (const entry of customEntries.value) {
    if (entry.key && entry.value) {
      custom[entry.key] = entry.value
    }
  }
  localMetadata.value.custom = Object.keys(custom).length > 0 ? custom : undefined
  emit('update', getMetadata())
}, { deep: true })

const getMetadata = (): MetadataConfig => {
  const result: MetadataConfig = {}
  if (localMetadata.value.title) result.title = localMetadata.value.title
  if (localMetadata.value.author) result.author = localMetadata.value.author
  if (localMetadata.value.album) result.album = localMetadata.value.album
  if (localMetadata.value.year) result.year = localMetadata.value.year
  if (localMetadata.value.comment) result.comment = localMetadata.value.comment
  if (localMetadata.value.description) result.description = localMetadata.value.description
  if (localMetadata.value.copyright) result.copyright = localMetadata.value.copyright
  if (localMetadata.value.genre) result.genre = localMetadata.value.genre
  if (localMetadata.value.custom && Object.keys(localMetadata.value.custom).length > 0) {
    result.custom = localMetadata.value.custom
  }
  return result
}

const addCustom = () => {
  customEntries.value.push({ key: '', value: '' })
}

const removeCustom = (index: number) => {
  customEntries.value.splice(index, 1)
}

const resetMetadata = () => {
  localMetadata.value = {
    title: '',
    author: '',
    album: '',
    year: undefined,
    comment: '',
    description: '',
    copyright: '',
    genre: '',
    custom: {}
  }
  customEntries.value = []
  emit('update', {})
}

// Expose reset method
defineExpose({ resetMetadata })
</script>

<style scoped>
.metadata-config {
  width: 100%;
}

.custom-metadata {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.custom-entry {
  display: flex;
  gap: 8px;
  align-items: center;
}

:deep(.el-form-item) {
  margin-bottom: 12px;
}

:deep(.el-form-item__label) {
  font-size: 13px;
}
</style>
