<template>
  <div class="min-h-screen bg-slate-50 flex items-center justify-center p-6 font-display">
    <div class="max-w-md w-full bg-white rounded-2xl shadow-2xl overflow-hidden border border-slate-100 kinetic-shadow">
      <!-- 顶部 Banner -->
      <div class="h-40 bg-slate-900 flex flex-col items-center justify-center p-6 text-center">
        <h1 class="text-2xl font-black text-white tracking-tighter uppercase">Join Platform</h1>
        <p class="text-blue-400 text-[10px] font-bold tracking-[0.2em] mt-2">智慧体育教务系统</p>
      </div>

      <!-- 注册表单 -->
      <div class="p-8">
        <div class="text-center mb-8">
          <h2 class="text-xl font-bold text-slate-900 tracking-tight">创建新账号</h2>
          <div class="h-1 w-6 bg-blue-600 mx-auto mt-2 rounded-full"></div>
        </div>

        <form @submit.prevent="register" class="space-y-5">
          <!-- 角色选择 -->
          <div class="flex p-1 bg-slate-50 rounded-xl border border-slate-100 mb-2">
            <button type="button"
                    :class="['flex-1 py-2.5 rounded-lg text-sm font-bold transition-all', role === 'student' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-400 hover:text-slate-600']"
                    @click="role = 'student'">
              学生注册
            </button>
            <button type="button"
                    :class="['flex-1 py-2.5 rounded-lg text-sm font-bold transition-all', role === 'teacher' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-400 hover:text-slate-600']"
                    @click="role = 'teacher'">
              教师注册
            </button>
          </div>

          <!-- 用户名/ID -->
          <div class="space-y-1">
            <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">{{ role === 'student' ? 'Student ID' : 'Teacher ID' }}</label>
            <input type="text" v-model="formData.id"
                   class="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm font-medium"
                   :placeholder="role === 'student' ? '学号' : '工号'" required maxlength="50">
          </div>

          <div class="grid grid-cols-2 gap-4">
            <!-- 密码 -->
            <div class="space-y-1">
              <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">Password</label>
              <input type="password" v-model="formData.password"
                     class="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm font-medium"
                     placeholder="密码" required minlength="6" maxlength="255">
            </div>

            <!-- 确认密码 -->
            <div class="space-y-1">
              <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">Confirm</label>
              <input type="password" v-model="confirmPassword"
                     class="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm font-medium"
                     placeholder="确认" required minlength="6" maxlength="255">
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <!-- 姓名 -->
            <div class="space-y-1">
              <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">Name</label>
              <input type="text" v-model="formData.name"
                     class="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm font-medium"
                     placeholder="姓名" required maxlength="100">
            </div>

            <!-- 性别 -->
            <div class="space-y-1">
              <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">Gender</label>
              <select v-model="formData.gender"
                      class="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm font-medium">
                <option value="男">男</option>
                <option value="女">女</option>
              </select>
            </div>
          </div>

          <!-- 角色特有字段 -->
          <div class="space-y-1">
            <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">{{ role === 'student' ? 'Major' : 'Title' }}</label>
            <input v-if="role === 'teacher'" type="text" v-model="formData.title"
                   class="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm font-medium"
                   placeholder="职称（如：讲师、副教授）" required maxlength="100">
            <input v-else type="text" v-model="formData.major"
                   class="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm font-medium"
                   placeholder="专业（如：网信、嵌入式）" required maxlength="100">
          </div>

          <div class="grid grid-cols-2 gap-4">
            <!-- 学院 -->
            <div class="space-y-1">
              <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">College</label>
              <input type="text" v-model="formData.college"
                     class="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm font-medium"
                     placeholder="学院" required maxlength="100">
            </div>

            <!-- 系 -->
            <div class="space-y-1">
              <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider ml-1">Dept</label>
              <input type="text" v-model="formData.department"
                     class="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-sm font-medium"
                     placeholder="系" required maxlength="100">
            </div>
          </div>

          <!-- 错误信息显示 -->
          <div v-if="errorMessage" class="text-xs font-bold text-red-500 bg-red-50 border border-red-100 p-3 rounded-lg flex items-center">
            <AlertCircleIcon class="w-4 h-4 mr-2" />
            {{ errorMessage }}
          </div>

          <!-- 注册按钮 -->
          <button type="submit"
                  class="w-full py-4 bg-slate-900 text-white font-black rounded-xl shadow-lg hover:bg-slate-800 transition-all kinetic-button disabled:opacity-50 mt-4"
                  :disabled="loading">
            <span v-if="loading" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent inline-block mr-2 align-middle"></span>
            <span class="align-middle">{{ loading ? '注册中...' : '创建账号' }}</span>
          </button>
        </form>

        <!-- 登录链接 -->
        <div class="mt-8 text-center">
          <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">已经有账号了? 
            <router-link to="/login" class="text-blue-600 hover:text-blue-700 ml-1">立即登录</router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { registerTeacher, registerStudent } from '../services/auth'
import { AlertCircle as AlertCircleIcon } from 'lucide-vue-next'

const router = useRouter()
const role = ref('student')
const confirmPassword = ref('')
const loading = ref(false)
const errorMessage = ref('')

// 表单数据
const formData = reactive({
  id: '',
  password: '',
  name: '',
  gender: '男',
  title: '', // 教师特有
  major: '', // 学生特有
  college: '',
  department: ''
})

// 注册功能
const register = async () => {
  // 表单验证
  if (!formData.id || !formData.password || !formData.name || !formData.college || !formData.department) {
    errorMessage.value = '请填写所有必填字段'
    return
  }

  if (role.value === 'teacher' && !formData.title) {
    errorMessage.value = '教师请填写职称'
    return
  }

  if (role.value === 'student' && !formData.major) {
    errorMessage.value = '学生请填写专业'
    return
  }

  if (formData.password !== confirmPassword.value) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    let result

    // 根据角色调用不同的注册API
    if (role.value === 'student') {
      result = await registerStudent(
        formData.id,
        formData.password,
        formData.name,
        formData.gender,
        formData.major,
        formData.college,
        formData.department
      )
    } else {
      result = await registerTeacher(
        formData.id,
        formData.password,
        formData.name,
        formData.gender,
        formData.title,
        formData.college,
        formData.department
      )
    }

    if (result.success) {
      // 注册成功，跳转到登录页面
      alert('注册成功，请登录')
      router.push('/login')
    } else {
      // 注册失败，显示错误信息
      errorMessage.value = result.message || '注册失败，请重试'
    }
  } catch (error) {
    errorMessage.value = '注册过程中发生错误，请稍后重试'
    console.error('注册错误:', error)
  } finally {
    loading.value = false
  }
}
</script>
