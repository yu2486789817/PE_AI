<template>
  <div class="min-h-screen bg-slate-50 flex items-center justify-center p-6 font-display">
    <div class="max-w-md w-full rounded-2xl shadow-2xl overflow-hidden bg-white kinetic-shadow border border-slate-100">
      <!-- 顶部 Banner -->
      <div class="h-48 relative overflow-hidden">
        <img src="../assets/Login/1.jpg"
             class="w-full h-full object-cover opacity-80"
             alt="Banner">
        <div class="absolute inset-0 bg-gradient-to-t from-slate-900/60 to-transparent flex flex-col items-center justify-center p-6">
          <h1 class="text-3xl font-bold text-white tracking-tight drop-shadow-md text-center">同济大学智慧体育</h1>
          <p class="text-white/80 text-xs font-bold uppercase tracking-widest mt-2">Precision Intelligence Platform</p>
        </div>
      </div>

      <!-- 登录表单 -->
      <div class="p-10 relative">
        <div class="text-center mb-10">
          <h2 class="text-2xl font-black text-slate-900 tracking-tight">账户登录</h2>
          <div class="h-1 w-8 bg-blue-600 mx-auto mt-2 rounded-full"></div>
        </div>

        <form @submit.prevent="login" class="space-y-6">
          <!-- 角色选择 -->
          <div class="flex p-1 bg-slate-50 rounded-xl border border-slate-100">
            <button type="button"
                    :class="['flex-1 py-2.5 rounded-lg text-sm font-bold transition-all', role === 'student' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-400 hover:text-slate-600']"
                    @click="role = 'student'">
              学生登录
            </button>
            <button type="button"
                    :class="['flex-1 py-2.5 rounded-lg text-sm font-bold transition-all', role === 'teacher' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-400 hover:text-slate-600']"
                    @click="role = 'teacher'">
              教师登录
            </button>
          </div>

          <!-- 用户名输入框 -->
          <div class="space-y-1.5">
            <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">用户名 / ID</label>
            <div class="relative group">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-300 group-focus-within:text-blue-500 transition-colors">
                <UserIcon class="w-5 h-5" />
              </div>
              <input type="text" v-model="username"
                       class="w-full pl-12 pr-4 py-3.5 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-medium text-slate-800"
                       placeholder="请输入用户名" required>
            </div>
          </div>

          <!-- 密码输入框 -->
          <div class="space-y-1.5">
            <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">访问密码</label>
            <div class="relative group">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-300 group-focus-within:text-blue-500 transition-colors">
                <LockIcon class="w-5 h-5" />
              </div>
              <input type="password" v-model="password"
                       class="w-full pl-12 pr-4 py-3.5 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-medium text-slate-800"
                       placeholder="请输入密码" required>
            </div>
          </div>

          <!-- 错误信息显示 -->
          <div v-if="errorMessage" class="text-xs font-bold text-red-500 bg-red-50 border border-red-100 p-3 rounded-lg flex items-center">
            <AlertCircleIcon class="w-4 h-4 mr-2 flex-shrink-0" />
            {{ errorMessage }}
          </div>

          <!-- 登录按钮 -->
          <button type="submit"
                  class="w-full py-4 bg-slate-900 text-white font-black rounded-xl shadow-lg hover:bg-slate-800 transition-all kinetic-button disabled:opacity-50 flex items-center justify-center gap-2"
                  :disabled="loading">
            <span v-if="loading" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
            <span>{{ loading ? '验证中...' : '立即登录' }}</span>
          </button>
        </form>

        <!-- 注册链接 -->
        <div class="mt-10 text-center">
          <p class="text-sm font-bold text-slate-400 uppercase tracking-widest">还没有账号？ 
            <router-link to="/register" class="text-blue-600 hover:text-blue-700 transition-colors ml-1">立即加入</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { loginTeacher, loginStudent } from '../services/auth'
import { User as UserIcon, Lock as LockIcon, AlertCircle as AlertCircleIcon } from 'lucide-vue-next'

const router = useRouter()
const role = ref('student')
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

// 登录功能
const login = async () => {
  // 表单验证
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    let result
    // 测试账户特判
    if ((role.value === 'student' && username.value === 'student001' && password.value === '123456') ||
        (role.value === 'teacher' && username.value === 'teacher001' && password.value === '123456')) {
      // 直接模拟登录成功，避免网络请求
      result = {
        success: true,
        data: {
          jwt_ans: 'mock_token_123456'
        }
      }
    } else {
      // 根据角色调用不同的登录API
      if (role.value === 'student') {
        result = await loginStudent(username.value, password.value)
      } else {
        result = await loginTeacher(username.value, password.value)
      }
    }

    if (result.success) {
      // 需要同时检查后端返回的 success 字段
      // auth 服务层只要 HTTP 200 就返回 success:true，但后端可能在响应体里返回 success:false
      const backendSuccess = result.data?.success !== false

      if (!backendSuccess) {
        errorMessage.value = result.data?.message || '用户名或密码错误'
        return
      }

      // 兼容处理 mock 和 真实接口的 token 字段
      const token = result.data?.data || result.data?.jwt_ans

      // 验证 token 是一个有效的字符串
      if (!token || typeof token !== 'string') {
        errorMessage.value = '登录异常：未获取到有效凭证，请重试'
        return
      }

      console.log('✅ 登录成功')
      localStorage.setItem('token', token)

      // 保存用户信息
      localStorage.setItem('user', JSON.stringify({
        id: username.value,
        role: role.value,
        username: username.value,
        token: token
      }))

      // 根据角色跳转到对应首页
      if (role.value === 'student') {
        router.push('/student')
      } else {
        router.push('/teacher')
      }
    } else {
      // 登录失败，显示错误信息
      errorMessage.value = result.message || '用户名或密码错误'
    }
  } catch (error) {
    errorMessage.value = '登录过程中发生错误，请稍后重试'
    console.error('登录错误:', error)
  } finally {
    loading.value = false
  }
}
</script>
