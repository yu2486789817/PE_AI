<template>
  <div class="flex h-screen bg-slate-50 overflow-hidden font-display">
    <!-- 侧边栏 -->
    <Sidebar ref="sidebarRef" />

    <!-- 主内容区域 -->
    <main
      :class="[
        'flex-1 flex flex-col transition-all duration-300 relative',
        isSidebarCollapsed ? 'ml-20' : 'ml-64'
      ]"
    >
      <!-- 内容区顶部阴影/装饰 (可选) -->
      <div class="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-blue-50/50 to-transparent pointer-events-none z-0"></div>

      <!-- 核心内容容器 -->
      <div class="flex-1 overflow-y-auto custom-scrollbar relative z-10">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Sidebar from '../components/Sidebar.vue'

const sidebarRef = ref(null)

// 通过访问子组件状态或在父组件维护状态来同步 margin
// 为了简化，这里我们假设侧边栏状态可以同步。
// 在实际项目中，可以使用 Pinia 或 provide/inject。
// 这里我直接在 Sidebar 中 emit 事件或通过全局状态。

const isSidebarCollapsed = computed(() => {
  return sidebarRef.value?.isCollapsed || false
})
</script>

<style scoped>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f8fafc;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 10px;
  border: 2px solid #f8fafc;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #cbd5e1;
}
</style>
