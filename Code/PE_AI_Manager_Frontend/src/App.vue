<template>
  <div class="font-display">
    <!-- 认证页面 (登录/注册) -->
    <div v-if="isLoginPage" class="min-h-screen">
      <router-view />
    </div>

    <!-- 主系统布局 (带侧边栏) -->
    <div v-else class="flex h-screen bg-slate-50 overflow-hidden">
      <!-- 侧边栏 -->
      <Sidebar ref="sidebarRef" />

      <!-- 主内容区域 -->
      <main
        :class="[
          'flex-1 flex flex-col transition-all duration-300 relative',
          isSidebarCollapsed ? 'ml-20' : 'ml-64'
        ]"
      >
        <!-- 内容区背景装饰 -->
        <div class="absolute top-0 left-0 right-0 h-64 bg-gradient-to-b from-blue-50/50 to-transparent pointer-events-none z-0"></div>

        <!-- 核心内容容器 -->
        <div class="flex-1 overflow-y-auto custom-scrollbar relative z-10">
          <router-view v-slot="{ Component }">
            <transition name="page-fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'

const route = useRoute()
const sidebarRef = ref(null)

// 判断当前是否为登录页面
const isLoginPage = computed(() => {
  return route.path === '/login' || route.path === '/register' || route.path === '/'
})

const isSidebarCollapsed = computed(() => {
  return sidebarRef.value?.isCollapsed || false
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

.font-display {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* 页面切换动画 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 全局滚动条美化 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #cbd5e1;
}
</style>
