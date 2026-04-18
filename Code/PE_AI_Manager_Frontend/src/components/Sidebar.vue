<template>
  <div
    :class="[
      'h-screen bg-white border-r border-slate-200 transition-all duration-300 flex flex-col shadow-xl z-50 fixed left-0 top-0',
      isCollapsed ? 'w-20' : 'w-64'
    ]"
  >
    <!-- 顶部 Logo & Toggle -->
    <div class="p-6 flex items-center justify-between border-b border-slate-50">
      <div v-if="!isCollapsed" class="flex items-center space-x-3 overflow-hidden whitespace-nowrap">
        <div class="p-2 rounded-xl bg-blue-600 text-white shadow-lg shadow-blue-100">
          <ActivityIcon class="w-6 h-6" />
        </div>
        <span class="text-xl font-black text-slate-900 tracking-tighter uppercase italic">Smart PE</span>
      </div>
      <button
        @click="toggleSidebar"
        class="p-2 rounded-xl hover:bg-slate-50 text-slate-400 hover:text-blue-600 transition-all kinetic-button"
      >
        <MenuIcon v-if="isCollapsed" class="w-6 h-6" />
        <ChevronLeftIcon v-else class="w-6 h-6" />
      </button>
    </div>

    <!-- 菜单区域 -->
    <div class="flex-1 overflow-y-auto py-6 px-4 space-y-2 custom-scrollbar">
      <div v-for="item in menuItems" :key="item.path">
        <router-link
          :to="item.path"
          :class="[
            'flex items-center p-3.5 rounded-2xl transition-all group relative',
            isActive(item)
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-100'
              : 'text-slate-500 hover:bg-slate-50 hover:text-blue-600'
          ]"
        >
          <component :is="item.icon" class="w-6 h-6 flex-shrink-0" />
          <span
            v-if="!isCollapsed"
            class="ml-4 font-bold text-sm tracking-tight whitespace-nowrap transition-opacity"
          >
            {{ item.name }}
          </span>
          <!-- Tooltip on collapsed -->
          <div
            v-if="isCollapsed"
            class="absolute left-full ml-4 px-3 py-2 bg-slate-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50 font-bold"
          >
            {{ item.name }}
          </div>
        </router-link>
      </div>
    </div>

    <!-- 底部区域 -->
    <div class="p-4 border-t border-slate-50">
      <div v-if="!isCollapsed" class="mb-4 p-4 rounded-2xl bg-slate-50 border border-slate-100 flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-blue-600 font-black shadow-sm">
          {{ userInitial }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-black text-slate-900 truncate">{{ userName }}</p>
          <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{{ userRoleText }}</p>
        </div>
      </div>
      <button
        @click="handleLogout"
        :class="[
          'w-full flex items-center p-3.5 rounded-2xl transition-all text-slate-400 hover:bg-red-50 hover:text-red-600 font-bold group relative',
          isCollapsed ? 'justify-center' : ''
        ]"
      >
        <LogOutIcon class="w-6 h-6" />
        <span v-if="!isCollapsed" class="ml-4 text-sm tracking-tight">退出登录</span>
        <div
          v-if="isCollapsed"
          class="absolute left-full ml-4 px-3 py-2 bg-red-600 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50 font-bold"
        >
          退出登录
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getStudentInfo, getTeacherInfo } from '../services/auth'
import {
  Activity as ActivityIcon,
  LayoutDashboard as HomeIcon,
  GraduationCap as GraduationCapIcon,
  FilePlus as FilePlusIcon,
  Video as VideoIcon,
  Bot as BotIcon,
  User as UserIcon,
  LogOut as LogOutIcon,
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  ClipboardList as ClipboardListIcon,
  BarChart3 as BarChart3Icon,
  FileText as FileTextIcon
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const isCollapsed = ref(false)

const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const userName = computed(() => user.value.name || user.value.username || 'User')
const userRole = computed(() => user.value.role || 'student')
const userInitial = computed(() => userName.value.charAt(0).toUpperCase())
const userRoleText = computed(() => userRole.value === 'teacher' ? '教师' : '学生')

const fetchUserName = async () => {
  if (!user.value.id || !user.value.token) return

  try {
    let result
    if (user.value.role === 'teacher') {
      result = await getTeacherInfo(user.value.id, user.value.token, '1', user.value.id)
    } else {
      result = await getStudentInfo(user.value.id, user.value.token, '1', user.value.id)
    }

    if (result.success && result.data && result.data.name) {
      // 更新本地状态
      user.value.name = result.data.name
      // 同步到 localStorage
      localStorage.setItem('user', JSON.stringify(user.value))
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

onMounted(() => {
  fetchUserName()
})

const currentPath = computed(() => route.path)

// 精确匹配短路径，前缀匹配长路径
const isActive = (item) => {
  if (item.exact) {
    return currentPath.value === item.path
  }
  return currentPath.value.startsWith(item.path)
}

const teacherMenu = [
  { name: '工作台', path: '/teacher/dashboard', icon: HomeIcon },
  { name: '我的课程', path: '/teacher', icon: GraduationCapIcon, exact: true },
  { name: '发布作业', path: '/teacher/publish', icon: FilePlusIcon },
  { name: '作业管理', path: '/teacher/assignments', icon: ClipboardListIcon },
  { name: '视频分析', path: '/teacher/videos', icon: VideoIcon },
  { name: 'AI 助手', path: '/assistant', icon: BotIcon },
  { name: '个人信息', path: '/profile', icon: UserIcon },
]

const studentMenu = [
  { name: '学习概览', path: '/student', icon: HomeIcon, exact: true },
  { name: 'AI 助手', path: '/assistant', icon: BotIcon },
  { name: '个人信息', path: '/profile', icon: UserIcon },
]

const menuItems = computed(() => userRole === 'teacher' ? teacherMenu : studentMenu)

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const handleLogout = () => {
  localStorage.removeItem('user')
  router.push('/login')
}

defineExpose({ isCollapsed })
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #f1f5f9;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #e2e8f0;
}
</style>
