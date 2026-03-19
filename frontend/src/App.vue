<template>
  <div id="app">
    <el-container class="app-container">
      <el-header class="app-header">
        <div class="header-content">
          <h1>
            <el-icon><VideoCamera /></el-icon>
            Copy Video - 视频转码工具
          </h1>
          <p class="subtitle">通过FFmpeg复制流并修改元信息，改变文件哈希值</p>
        </div>
        <div class="header-nav">
          <el-menu
            :default-active="currentPage"
            mode="horizontal"
            :ellipsis="false"
            @select="handlePageChange"
            class="header-menu"
          >
            <el-menu-item index="home">转码</el-menu-item>
            <el-menu-item index="settings">设置</el-menu-item>
          </el-menu>
        </div>
      </el-header>

      <el-main class="app-main">
        <HomeView v-if="currentPage === 'home'" />
        <SettingsView v-else-if="currentPage === 'settings'" />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { VideoCamera } from '@element-plus/icons-vue'
import HomeView from './views/Home.vue'
import SettingsView from './views/Settings.vue'

const currentPage = ref('home')

const handlePageChange = (index: string) => {
  currentPage.value = index
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.app-header {
  background: linear-gradient(135deg, #409eff 0%, #79bbff 100%);
  color: white;
  padding: 15px 20px 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-content h1 {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 8px 0;
  font-size: 22px;
}

.subtitle {
  margin: 0;
  opacity: 0.9;
  font-size: 13px;
}

.header-menu {
  border: none;
  background: transparent;
}

.header-menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.8);
  border-bottom: 2px solid transparent;
}

.header-menu :deep(.el-menu-item:hover),
.header-menu :deep(.el-menu-item.is-active) {
  color: white;
  background: rgba(255, 255, 255, 0.1);
  border-bottom-color: white;
}

.app-main {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}
</style>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  min-height: 100vh;
}
</style>
