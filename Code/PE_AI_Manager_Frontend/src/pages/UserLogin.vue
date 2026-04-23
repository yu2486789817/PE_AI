<template>
  <div class="page-shell min-h-screen grid lg:grid-cols-2">
    <section class="hidden lg:flex relative overflow-hidden rounded-r-[40px] m-4 shadow-soft">
      <img src="../assets/Login/1.jpg" class="absolute inset-0 h-full w-full object-cover" alt="体育课堂" />
      <div class="absolute inset-0 bg-gradient-to-br from-slate-900/70 via-blue-900/55 to-cyan-700/45"></div>
      <div class="relative z-10 p-10 flex flex-col justify-between text-white w-full">
        <div class="flex items-center gap-3">
          <img src="../assets/Login/2.jpg" class="w-12 h-12 rounded-xl border border-white/30" alt="logo" />
          <div>
            <p class="text-sm tracking-[0.2em] uppercase text-white/70">Tongji Smart PE</p>
            <h1 class="text-2xl font-bold">智慧体育课堂平台</h1>
          </div>
        </div>
        <div>
          <p class="text-4xl font-bold leading-tight">用数据驱动课堂，
            <br />让运动教学更高效。</p>
          <p class="mt-4 text-white/80">教师端支持课程、作业、学生与评分的全流程管理。</p>
        </div>
        <p class="text-xs text-white/60">Software Engineering Project · 2026</p>
      </div>
    </section>

    <section class="flex items-center justify-center px-6 py-10">
      <div class="w-full max-w-md rounded-[24px] border border-web-line-200 bg-white/90 backdrop-blur shadow-card p-7">
        <div>
          <h2 class="text-3xl font-bold text-web-ink-900">账户登录</h2>
          <p class="mt-2 text-sm text-web-ink-500">请选择身份并输入账号信息。</p>
        </div>

        <form class="mt-6 space-y-4" @submit.prevent="login">
          <div class="grid grid-cols-2 gap-2 rounded-lg bg-web-surface-200 p-1">
            <button
              type="button"
              class="rounded-md px-3 py-2 text-sm font-semibold transition"
              :class="role === 'student' ? 'bg-white text-web-primary-600 shadow' : 'text-web-ink-600'"
              @click="role = 'student'"
            >
              学生
            </button>
            <button
              type="button"
              class="rounded-md px-3 py-2 text-sm font-semibold transition"
              :class="role === 'teacher' ? 'bg-white text-web-primary-600 shadow' : 'text-web-ink-600'"
              @click="role = 'teacher'"
            >
              教师
            </button>
          </div>

          <div>
            <label class="mb-1 block text-xs font-semibold text-web-ink-600">用户 ID</label>
            <input v-model="username" type="text" required class="input-base" placeholder="请输入账号" />
          </div>

          <div>
            <label class="mb-1 block text-xs font-semibold text-web-ink-600">登录密码</label>
            <input v-model="password" type="password" required class="input-base" placeholder="请输入密码" />
          </div>

          <p v-if="errorMessage" class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {{ errorMessage }}
          </p>

          <button type="submit" class="btn-primary w-full justify-center" :disabled="loading">
            <span v-if="loading" class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></span>
            <span>{{ loading ? '登录中...' : '登录' }}</span>
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-web-ink-500">
          还没有账号？
          <router-link to="/register" class="font-semibold text-web-primary-600 hover:underline">去注册</router-link>
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { loginTeacher, loginStudent } from '../services/auth'

const router = useRouter()
const role = ref('student')
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

const login = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    let result
    if (
      (role.value === 'student' && username.value === 'student001' && password.value === '123456') ||
      (role.value === 'teacher' && username.value === 'teacher001' && password.value === '123456')
    ) {
      result = { success: true, data: { jwt_ans: 'mock_token_123456' } }
    } else if (role.value === 'student') {
      result = await loginStudent(username.value, password.value)
    } else {
      result = await loginTeacher(username.value, password.value)
    }

    if (!result.success || result.data?.success === false) {
      errorMessage.value = result.data?.message || result.message || '用户名或密码错误'
      return
    }

    const token = result.data?.data || result.data?.jwt_ans
    if (!token || typeof token !== 'string') {
      errorMessage.value = '登录失败：未获取有效凭证'
      return
    }

    localStorage.setItem('token', token)
    localStorage.setItem(
      'user',
      JSON.stringify({ id: username.value, role: role.value, username: username.value, token })
    )

    router.push(role.value === 'student' ? '/student' : '/teacher')
  } catch (error) {
    errorMessage.value = '登录过程发生错误，请稍后重试'
    console.error('登录错误:', error)
  } finally {
    loading.value = false
  }
}
</script>
