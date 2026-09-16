<template>
  <el-container class="app-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '68px' : '220px'" class="sidebar">
      <div class="logo" :class="{ collapsed: isCollapse }">
        <div class="logo-icon">
          <el-icon :size="22"><Car /></el-icon>
        </div>
        <transition name="fade">
          <span v-if="!isCollapse" class="logo-text">二手车价格评估</span>
        </transition>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        :collapse="isCollapse"
        :collapse-transition="false"
        background-color="transparent"
        text-color="var(--sidebar-text)"
        active-text-color="#ffffff"
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>数据看板</template>
        </el-menu-item>
        <el-menu-item index="/predict">
          <el-icon><MagicStick /></el-icon>
          <template #title>价格预测</template>
        </el-menu-item>
        <el-menu-item index="/model-analysis">
          <el-icon><TrendCharts /></el-icon>
          <template #title>模型分析</template>
        </el-menu-item>
        <el-menu-item index="/cars">
          <el-icon><List /></el-icon>
          <template #title>车辆列表</template>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><History /></el-icon>
          <template #title>预测历史</template>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer" v-if="!isCollapse">
        <div class="footer-dot"></div>
        <span>系统运行正常</span>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="right-container">
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" :size="20" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <el-tag type="primary" effect="light" round class="tech-tag">大数据 + 机器学习</el-tag>
          <div class="user-info">
            <el-avatar :size="30" class="user-avatar">管</el-avatar>
            <span>管理员</span>
          </div>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isCollapse = ref(false)

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta.title || '二手车价格评估系统')

// 窄屏自动折叠
const handleResize = () => {
  isCollapse.value = window.innerWidth < 900
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background: linear-gradient(180deg, #0F1E3A 0%, #16294D 100%);
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;
  overflow: hidden;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
  white-space: nowrap;
}

.logo.collapsed {
  gap: 0;
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2D6BFF, #5B8CFF);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(45, 107, 255, 0.4);
  flex-shrink: 0;
}

.logo-text {
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.sidebar-menu {
  border-right: none;
  padding: 12px 10px;
  flex: 1;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: var(--sidebar-text);
  --el-menu-active-color: #fff;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 46px;
  line-height: 46px;
  border-radius: 10px;
  margin-bottom: 4px;
  transition: background 0.2s, color 0.2s;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #2D6BFF, #4A7DFF);
  box-shadow: 0 4px 12px rgba(45, 107, 255, 0.35);
  color: #fff;
}

.sidebar-menu :deep(.el-menu-item.is-active .el-icon) {
  color: #fff;
}

.sidebar-footer {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--sidebar-text);
  font-size: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

.footer-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22C55E;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.8);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.right-container {
  flex-direction: column;
  min-width: 0;
}

.header {
  background: #fff;
  border-bottom: 1px solid #EEF1F6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  color: var(--text-regular);
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  transition: background 0.2s, color 0.2s;
}

.collapse-btn:hover {
  background: #F0F6FF;
  color: var(--primary);
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.tech-tag {
  border: 1px solid #D6E4FF;
  background: #F0F6FF;
  color: var(--primary);
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-regular);
  font-size: 14px;
}

.user-avatar {
  background: linear-gradient(135deg, #2D6BFF, #5B8CFF);
  color: #fff;
  font-weight: 600;
}

.main-content {
  background-color: var(--page-bg);
  padding: 20px;
  overflow-y: auto;
}

/* 窄屏适配 */
@media (max-width: 1200px) {
  .tech-tag { display: none; }
}
</style>
