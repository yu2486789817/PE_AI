<template>
  <div class="min-h-screen bg-slate-50 font-display p-8 pt-28">
    <div class="max-w-3xl mx-auto bg-white rounded-3xl shadow-2xl overflow-hidden">
      <!-- 页面标题 -->
      <div class="p-8 border-b border-slate-100 bg-white">
        <div class="flex items-center space-x-3">
          <UserIcon class="w-8 h-8 text-blue-600" />
          <h1 class="text-3xl font-bold text-slate-900 tracking-tight">个人信息</h1>
        </div>
        <p class="text-slate-500 mt-2 font-medium">管理您的账号与安全设置</p>
      </div>

      <!-- 用户基本信息 -->
      <div class="p-8">
        <div class="flex items-center space-x-6 mb-10">
          <!-- 用户头像 -->
          <div class="w-24 h-24 bg-blue-600 rounded-2xl flex items-center justify-center text-white text-4xl font-black shadow-lg shadow-blue-100 kinetic-shadow">
            {{ userInitial }}
          </div>
          <!-- 用户信息 -->
          <div>
            <h2 class="text-3xl font-bold text-slate-900">{{ userInfo.name || userInfo.username }}</h2>
            <div class="flex items-center space-x-2 mt-2">
              <span class="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-600 text-xs font-bold border border-blue-100 uppercase tracking-wider">
                {{ userRoleText }}
              </span>
            </div>
          </div>
        </div>

        <!-- 详细信息卡片 -->
        <div class="bg-slate-50/50 rounded-2xl p-8 border border-slate-100 mb-8">
          <div class="flex justify-between items-center mb-6">
            <h3 class="text-lg font-bold text-slate-900">账号详情</h3>
          </div>
          <div class="space-y-4">
            <div class="grid grid-cols-3 gap-4 py-3 border-b border-slate-100/50 last:border-0">
              <span class="text-sm font-bold text-slate-400 uppercase tracking-wider">账号类型</span>
              <span class="col-span-2 text-sm font-bold text-slate-700">{{ userRoleText }}</span>
            </div>
            <div class="grid grid-cols-3 gap-4 py-3 border-b border-slate-100/50 last:border-0">
              <span class="text-sm font-bold text-slate-400 uppercase tracking-wider">{{ userInfo.role === 'student' ? '学号' : '工号' }}</span>
              <span class="col-span-2 text-sm font-bold text-slate-700">{{ userInfo.username }}</span>
            </div>
            <div class="grid grid-cols-3 gap-4 py-3 border-b border-slate-100/50 last:border-0">
              <span class="text-sm font-bold text-slate-400 uppercase tracking-wider">姓名</span>
              <span class="col-span-2 text-sm font-bold text-slate-700">{{ userInfo.name || '-' }}</span>
            </div>
            <div class="grid grid-cols-3 gap-4 py-3 border-b border-slate-100/50 last:border-0">
              <span class="text-sm font-bold text-slate-400 uppercase tracking-wider">性别</span>
              <span class="col-span-2 text-sm font-bold text-slate-700">{{ userInfo.gender || '-' }}</span>
            </div>
            <div v-if="userInfo.role === 'student'" class="grid grid-cols-3 gap-4 py-3 border-b border-slate-100/50 last:border-0">
              <span class="text-sm font-bold text-slate-400 uppercase tracking-wider">专业</span>
              <span class="col-span-2 text-sm font-bold text-slate-700">{{ userInfo.major || '-' }}</span>
            </div>
            <div v-if="userInfo.role === 'teacher'" class="grid grid-cols-3 gap-4 py-3 border-b border-slate-100/50 last:border-0">
              <span class="text-sm font-bold text-slate-400 uppercase tracking-wider">职称</span>
              <span class="col-span-2 text-sm font-bold text-slate-700">{{ userInfo.title || '-' }}</span>
            </div>
            <div class="grid grid-cols-3 gap-4 py-3 border-b border-slate-100/50 last:border-0">
              <span class="text-sm font-bold text-slate-400 uppercase tracking-wider">所属学院</span>
              <span class="col-span-2 text-sm font-bold text-slate-700">{{ userInfo.college || '-' }}</span>
            </div>
            <div class="grid grid-cols-3 gap-4 py-3 border-b border-slate-100/50 last:border-0">
              <span class="text-sm font-bold text-slate-400 uppercase tracking-wider">所属系</span>
              <span class="col-span-2 text-sm font-bold text-slate-700">{{ userInfo.department || '-' }}</span>
            </div>
          </div>
        </div>

        <!-- 修改密码区域 -->
        <div class="bg-slate-50/50 rounded-2xl p-8 border border-slate-100">
          <div class="flex items-center space-x-3 mb-6">
            <ShieldCheckIcon class="w-5 h-5 text-teal-600" />
            <h3 class="text-lg font-bold text-slate-900">账号安全</h3>
          </div>
          <button
            @click="showChangePasswordModal = true"
            class="w-full py-4 bg-slate-900 text-white font-bold rounded-xl shadow-lg hover:bg-slate-800 transition-all kinetic-button"
          >
            修改登录密码
          </button>
        </div>
      </div>
    </div>

    <!-- 修改密码模态框 -->
    <div v-if="showChangePasswordModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-3xl shadow-2xl max-w-md w-full">
        <div class="p-6 border-b border-gray-100">
          <h2 class="text-2xl font-bold text-gray-800">修改密码</h2>
          <button @click="showChangePasswordModal = false" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
            <span class="text-2xl">&times;</span>
          </button>
        </div>
        <div class="p-6">
          <!-- 旧密码 -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">旧密码</label>
            <input
              type="password"
              v-model="oldPassword"
              class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="请输入旧密码"
            >
          </div>

          <!-- 新密码 -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">新密码</label>
            <input
              type="password"
              v-model="newPassword"
              class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="请输入新密码"
            >
          </div>

          <!-- 确认新密码 -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">确认新密码</label>
            <input
              type="password"
              v-model="confirmPassword"
              class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              placeholder="请再次输入新密码"
            >
          </div>

          <!-- 错误信息 -->
          <div v-if="passwordError" class="text-red-500 text-sm mb-4">
            {{ passwordError }}
          </div>

          <!-- 成功信息 -->
          <div v-if="passwordSuccess" class="text-green-500 text-sm mb-4">
            {{ passwordSuccess }}
          </div>

          <!-- 操作按钮 -->
          <div class="flex space-x-4">
            <button
              @click="showChangePasswordModal = false"
              class="flex-1 py-3 bg-gray-200 text-gray-800 font-bold rounded-xl hover:bg-gray-300 transition-all"
            >
              取消
            </button>
            <button
              @click="handleChangePassword"
              class="flex-1 py-3 bg-blue-500 text-white font-bold rounded-xl shadow-lg hover:bg-blue-600 transition-all"
              :disabled="passwordLoading"
            >
              <span v-if="passwordLoading">修改中...</span>
              <span v-else>确认修改</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { changeTeacherPassword, changeStudentPassword, getTeacherInfo, getStudentInfo } from '../services/auth'
import { User as UserIcon, ShieldCheck as ShieldCheckIcon } from 'lucide-vue-next'

const router = useRouter()

// 用户信息
const userInfo = ref({
  role: '',
  username: '',
  name: '',
  gender: '',
  title: '',
  major: '',
  college: '',
  department: ''
})

// 修改密码相关状态
const showChangePasswordModal = ref(false)
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordError = ref('')
const passwordSuccess = ref('')
const passwordLoading = ref(false)

// 计算属性
const userInitial = computed(() => {
  const name = userInfo.value.name || userInfo.value.username
  return name.charAt(0).toUpperCase()
})

const userRoleText = computed(() => {
  return userInfo.value.role === 'student' ? '学生' : '教师'
})

// 获取用户信息
onMounted(async () => {
  const user = localStorage.getItem('user')
  if (user) {
    userInfo.value = JSON.parse(user)

    try {
      let result
      const userId = userInfo.value.username
      const userType = userInfo.value.role === 'student' ? '0' : '1'

      if (userInfo.value.role === 'student') {
        result = await getStudentInfo(userId, userInfo.value.token, userType, userId)
      } else {
        result = await getTeacherInfo(userId, userInfo.value.token, userType, userId)
      }

      if (result.success) {
        userInfo.value = {
          ...userInfo.value,
          ...result.data
        }
        // 更新本地存储
        localStorage.setItem('user', JSON.stringify(userInfo.value))
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  } else {
    // 未登录，跳转到登录页
    router.push('/login')
  }
})

// 修改密码处理函数
const handleChangePassword = async () => {
  // 表单验证
  if (!oldPassword.value) {
    passwordError.value = '请输入旧密码'
    return
  }
  if (!newPassword.value) {
    passwordError.value = '请输入新密码'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = '两次输入的新密码不一致'
    return
  }
  if (newPassword.value.length < 6) {
    passwordError.value = '新密码长度不能少于6位'
    return
  }

  passwordError.value = ''
  passwordSuccess.value = ''
  passwordLoading.value = true

  try {
    let result
    const userId = userInfo.value.username

    // 根据用户角色调用不同的修改密码API
    if (userInfo.value.role === 'student') {
      result = await changeStudentPassword(userId, oldPassword.value, newPassword.value)
    } else {
      result = await changeTeacherPassword(userId, oldPassword.value, newPassword.value)
    }

    if (result.success) {
      passwordSuccess.value = '密码修改成功！'
      // 重置表单
      oldPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
      // 3秒后关闭模态框
      setTimeout(() => {
        showChangePasswordModal.value = false
      }, 3000)
    } else {
      passwordError.value = result.message || '密码修改失败'
    }
  } catch (error) {
    passwordError.value = '修改密码时发生错误，请稍后重试'
    console.error('修改密码错误:', error)
  } finally {
    passwordLoading.value = false
  }
}
</script>
