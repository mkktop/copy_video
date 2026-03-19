<template>
  <div class="settings-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span><el-icon><Setting /></el-icon> 系统设置</span>
          <el-button type="primary" @click="saveSettings" :loading="saving">
            保存设置
          </el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- Basic Settings -->
        <el-tab-pane label="基本设置" name="basic">
          <el-form label-width="150px" :model="localSettings">
            <el-form-item label="输出目录">
              <el-input v-model="localSettings.output_dir" placeholder="/app/workspace/output" />
            </el-form-item>

            <el-form-item label="转码后删除源文件">
              <el-switch v-model="localSettings.delete_source" />
              <span class="form-tip">转码成功后自动删除源视频文件</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Auto Scan Settings -->
        <el-tab-pane label="自动扫描" name="autoscan">
          <el-form label-width="150px" :model="localSettings">
            <el-form-item label="启用自动扫描">
              <el-switch v-model="localSettings.auto_scan_enabled" @change="handleAutoScanChange" />
              <span class="form-tip">定期扫描指定目录并自动转码新文件</span>
            </el-form-item>

            <el-form-item label="扫描间隔（秒）">
              <el-input-number
                v-model="localSettings.auto_scan_interval"
                :min="60"
                :max="86400"
                :step="60"
                controls-position="right"
              />
              <span class="form-tip">建议 3600 秒（1小时）</span>
            </el-form-item>

            <el-form-item label="扫描目录">
              <el-input v-model="localSettings.scan_input_dir" placeholder="/app/workspace/input" />
            </el-form-item>

            <el-form-item label="调度器状态">
              <div class="scheduler-status">
                <el-tag :type="schedulerStatus.running ? 'success' : 'info'">
                  {{ schedulerStatus.running ? '运行中' : '已停止' }}
                </el-tag>
                <el-button-group>
                  <el-button size="small" @click="startScheduler" :disabled="schedulerStatus.running">
                    启动
                  </el-button>
                  <el-button size="small" @click="stopScheduler" :disabled="!schedulerStatus.running">
                    停止
                  </el-button>
                  <el-button size="small" @click="scanNow" :loading="scanning">
                    立即扫描
                  </el-button>
                </el-button-group>
              </div>
            </el-form-item>

            <el-form-item label="已扫描文件数">
              <span>{{ schedulerStatus.scanned_count }} 个文件</span>
              <el-button size="small" @click="clearHistory" style="margin-left: 10px">
                清空历史
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- Metadata Settings -->
        <el-tab-pane label="默认元数据" name="metadata">
          <el-form label-width="150px" :model="localSettings">
            <el-form-item label="默认标题">
              <el-input v-model="localSettings.metadata_title" placeholder="留空则自动生成" />
            </el-form-item>

            <el-form-item label="默认作者">
              <el-input v-model="localSettings.metadata_author" placeholder="作者名称" />
            </el-form-item>

            <el-form-item label="默认专辑">
              <el-input v-model="localSettings.metadata_album" placeholder="专辑名称" />
            </el-form-item>

            <el-form-item label="默认年份">
              <el-input-number
                v-model="localSettings.metadata_year"
                :min="1900"
                :max="2100"
                placeholder="年份"
                controls-position="right"
              />
            </el-form-item>

            <el-form-item label="默认备注">
              <el-input v-model="localSettings.metadata_comment" placeholder="备注信息" />
            </el-form-item>

            <el-form-item label="默认简介">
              <el-input
                v-model="localSettings.metadata_description"
                type="textarea"
                :rows="3"
                placeholder="视频简介"
              />
            </el-form-item>

            <el-form-item label="默认版权">
              <el-input v-model="localSettings.metadata_copyright" placeholder="版权信息" />
            </el-form-item>

            <el-form-item label="默认类型">
              <el-select v-model="localSettings.metadata_genre" placeholder="选择类型" clearable>
                <el-option label="电影" value="Movie" />
                <el-option label="电视节目" value="TV Show" />
                <el-option label="音乐视频" value="Music Video" />
                <el-option label="纪录片" value="Documentary" />
                <el-option label="动画" value="Animation" />
                <el-option label="其他" value="Other" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import api, { type TranscodeSettings, type SchedulerStatus } from '@/api/client'

const activeTab = ref('basic')
const saving = ref(false)
const scanning = ref(false)

const localSettings = reactive<TranscodeSettings>({
  output_dir: '/app/workspace/output',
  delete_source: false,
  auto_scan_enabled: false,
  auto_scan_interval: 3600,
  scan_input_dir: '/app/workspace/input',
  metadata_title: '',
  metadata_author: '',
  metadata_album: '',
  metadata_year: undefined,
  metadata_comment: '',
  metadata_description: '',
  metadata_copyright: '',
  metadata_genre: '',
  metadata_custom: '',
  scanned_files: []
})

const schedulerStatus = reactive<SchedulerStatus>({
  running: false,
  enabled: false,
  interval: 3600,
  scan_dir: '',
  scanned_count: 0
})

const loadSettings = async () => {
  try {
    const response = await api.getSettings()
    Object.assign(localSettings, response.data)
  } catch (error: any) {
    ElMessage.error('加载设置失败')
  }
}

const loadSchedulerStatus = async () => {
  try {
    const response = await api.getSchedulerStatus()
    Object.assign(schedulerStatus, response.data)
  } catch (error: any) {
    console.error('Failed to load scheduler status:', error)
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    await api.updateSettings(localSettings)
    ElMessage.success('设置已保存')
    await loadSchedulerStatus()
  } catch (error: any) {
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

const handleAutoScanChange = async (enabled: boolean) => {
  if (enabled) {
    await startScheduler()
  } else {
    await stopScheduler()
  }
}

const startScheduler = async () => {
  try {
    await api.startScheduler()
    ElMessage.success('调度器已启动')
    await loadSchedulerStatus()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '启动调度器失败')
  }
}

const stopScheduler = async () => {
  try {
    await api.stopScheduler()
    ElMessage.success('调度器已停止')
    await loadSchedulerStatus()
  } catch (error: any) {
    ElMessage.error('停止调度器失败')
  }
}

const scanNow = async () => {
  scanning.value = true
  try {
    await api.scanNow()
    ElMessage.success('扫描任务已启动')
    await loadSchedulerStatus()
  } catch (error: any) {
    ElMessage.error('启动扫描失败')
  } finally {
    scanning.value = false
  }
}

const clearHistory = async () => {
  try {
    await api.clearScanHistory()
    ElMessage.success('扫描历史已清空')
    await loadSchedulerStatus()
  } catch (error: any) {
    ElMessage.error('清空历史失败')
  }
}

onMounted(() => {
  loadSettings()
  loadSchedulerStatus()
})
</script>

<style scoped>
.settings-view {
  max-width: 800px;
  margin: 0 auto;
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

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.scheduler-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-tabs__content) {
  padding: 20px 0;
}
</style>
