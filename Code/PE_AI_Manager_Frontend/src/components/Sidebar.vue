<template>
  <div :class="['h-screen border-r border-web-line-200 bg-white shadow-card fixed left-0 top-0 z-50 flex flex-col transition-all duration-300', isCollapsed ? 'w-20' : 'w-64']">
    <div class="flex items-center justify-between border-b border-web-line-100 p-4">
        <div v-if="!isCollapsed" class="flex items-center gap-2">
          <div class="rounded-lg bg-web-primary-500 p-2 text-white">
            <ActivityIcon class="h-5 w-5" />
          </div>
          <div>
            <p class="text-sm font-bold text-web-ink-900">Smart PE</p>
            <p class="text-xs text-web-ink-500">{{ productSubtitle }}</p>
          </div>
        </div>
      <button @click="toggleSidebar" class="rounded-lg p-2 text-web-ink-500 hover:bg-web-surface-200">
        <MenuIcon v-if="isCollapsed" class="h-5 w-5" />
        <ChevronLeftIcon v-else class="h-5 w-5" />
      </button>
    </div>

    <div class="flex-1 overflow-y-auto p-3 space-y-1">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        :class="[
          'group relative flex items-center rounded-lg px-3 py-2 text-sm font-semibold transition-colors',
          isActive(item) ? 'bg-web-primary-500 text-white' : 'text-web-ink-600 hover:bg-web-surface-200'
        ]"
      >
        <component :is="item.icon" class="h-5 w-5" />
        <span v-if="!isCollapsed" class="ml-3">{{ item.name }}</span>
        <span v-if="isCollapsed" class="absolute left-full ml-2 hidden rounded bg-web-ink-900 px-2 py-1 text-xs text-white group-hover:block">{{ item.name }}</span>
      </router-link>
    </div>

    <div class="border-t border-web-line-100 p-3">
      <div
        v-if="!isCollapsed"
        class="relative mb-2 overflow-hidden rounded-2xl border border-web-line-200 bg-gradient-to-br from-web-surface-100 via-white to-blue-50/70 px-3 pb-3 pt-4 shadow-card"
      >
        <div
          class="pointer-events-none absolute left-0 right-0 top-0 h-1.5 bg-gradient-to-r from-web-primary-500 via-blue-400 to-cyan-300"
        ></div>
        <div class="pointer-events-none absolute -right-7 -top-7 h-16 w-16 rounded-full bg-web-primary-200/40"></div>
        <div class="pointer-events-none absolute -bottom-8 -left-8 h-20 w-20 rounded-full bg-blue-200/30"></div>

        <div class="relative">
          <div class="flex items-center gap-3">
            <div
              class="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-web-primary-500 to-web-primary-700 text-base font-bold text-white shadow-soft"
            >
              {{ userInitial }}
              <span class="absolute -right-0.5 -top-0.5 h-3 w-3 rounded-full border-2 border-white bg-blue-400"></span>
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate text-[15px] font-bold text-web-ink-900">{{ userName }}</p>
              <p class="mt-0.5 text-xs text-web-ink-500">{{ productSubtitle }}</p>
            </div>
          </div>

          <div class="mt-3 flex items-center gap-2 text-[11px]">
            <span
              class="rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 font-semibold text-blue-700"
            >
              {{ userRoleText }}
            </span>
            <span class="rounded-full border border-web-line-200 bg-white/80 px-2.5 py-1 font-medium text-web-ink-600">
              学号/工号 {{ userIdText }}
            </span>
          </div>
        </div>
      </div>
      <button class="flex w-full items-center rounded-lg px-3 py-2 text-sm font-semibold text-web-danger-600 hover:bg-red-50" @click="handleLogout">
        <LogOutIcon class="h-5 w-5" />
        <span v-if="!isCollapsed" class="ml-3">退出登录</span>
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
  ClipboardList as ClipboardListIcon
} from 'lucide-vue-next'

defineOptions({ name: 'AppSidebar' })

const route = useRoute()
const router = useRouter()
const isCollapsed = ref(false)

const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
const userName = computed(() => user.value.name || user.value.username || 'User')
const userRole = computed(() => user.value.role || 'student')
const userRoleText = computed(() => (userRole.value === 'teacher' ? '教师' : '学生'))
const productSubtitle = computed(() => (userRole.value === 'teacher' ? '教师管理端' : '学生学习端'))
const userIdText = computed(() => user.value.id || '--')
const userInitial = computed(() => {
  const text = String(userName.value || '').trim()
  return text ? text.slice(0, 1).toUpperCase() : 'U'
})

const fetchUserName = async () => {
  const activeToken = (localStorage.getItem('token') || user.value.token || '').trim()
  if (!user.value.id || !activeToken) return

  try {
    let result
    if (user.value.role === 'teacher') {
      result = await getTeacherInfo(user.value.id, activeToken, '1', user.value.id)
    } else {
      result = await getStudentInfo(user.value.id, activeToken, '0', user.value.id)
    }

    if (result.success && result.data && result.data.name) {
      user.value.name = result.data.name
      user.value.token = activeToken
      localStorage.setItem('user', JSON.stringify(user.value))
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

onMounted(fetchUserName)

const currentPath = computed(() => route.path)
const isActive = (item) => (item.exact ? currentPath.value === item.path : currentPath.value.startsWith(item.path))

const teacherMenu = [
  { name: '工作台', path: '/teacher/dashboard', icon: HomeIcon },
  { name: '我的课程', path: '/teacher', icon: GraduationCapIcon, exact: true },
  { name: '发布作业', path: '/teacher/publish', icon: FilePlusIcon },
  { name: '作业管理', path: '/teacher/assignments', icon: ClipboardListIcon },
  { name: '视频分析', path: '/teacher/videos', icon: VideoIcon },
  { name: 'AI 助手', path: '/assistant', icon: BotIcon },
  { name: '个人信息', path: '/profile', icon: UserIcon }
]

const studentMenu = [
  { name: '学习概览', path: '/student', icon: HomeIcon, exact: true },
  { name: 'AI 助手', path: '/assistant', icon: BotIcon },
  { name: '个人信息', path: '/profile', icon: UserIcon }
]

const menuItems = computed(() => (userRole.value === 'teacher' ? teacherMenu : studentMenu))

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const handleLogout = () => {
  localStorage.removeItem('user')
  router.push('/login')
}

defineExpose({ isCollapsed })
</script>
