<template>
  <div class="min-h-screen flex flex-col lg:flex-row font-display bg-white overflow-hidden">
    <!-- 左侧：视觉区 -->
    <div class="hidden lg:flex lg:w-5/12 relative overflow-hidden bg-slate-900">
      <img src="../assets/Login/1.jpg" 
           class="absolute inset-0 w-full h-full object-cover opacity-60"
           alt="Sakura Background">
      <div class="absolute inset-0 bg-gradient-to-br from-blue-900/40 to-slate-900/80"></div>
      
      <div class="relative z-10 p-16 flex flex-col justify-between h-full w-full">
        <div class="flex items-center gap-4 animate-fade-in">
          <img src="../assets/Login/2.jpg" class="w-12 h-12 rounded-full border-2 border-white/20 p-1 bg-white/10 backdrop-blur-sm" alt="Logo">
          <span class="text-white/80 font-bold tracking-widest text-sm uppercase">Smart PE Join</span>
        </div>

        <div class="space-y-6">
          <h1 class="text-6xl font-black text-white leading-tight">
            开启您的<br/>
            <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">智慧体育之旅</span>
          </h1>
          <p class="text-lg text-white/70 leading-relaxed">
            加入同济大学数字化运动平台，体验 AI 驱动的精准教学与实时反馈。
          </p>
        </div>

        <div class="text-white/30 text-xs font-bold tracking-[0.3em] uppercase">
          Innovation & Excellence
        </div>
      </div>
    </div>

    <!-- 右侧：注册表单区 -->
    <div class="w-full lg:w-7/12 flex items-center justify-center p-8 lg:p-12 relative bg-white overflow-y-auto">
      <!-- 校徽水印 -->
      <img src="../assets/Login/2.jpg" 
           class="absolute pointer-events-none opacity-[0.4] w-[600px] max-w-[90%] object-contain top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
           alt="Watermark">

      <div class="max-w-2xl w-full space-y-8 relative z-10 py-8">
        <div>
          <h2 class="text-3xl font-black text-slate-900 tracking-tight">创建新账号</h2>
          <p class="mt-2 text-slate-500 font-medium">请填写以下信息以完成注册。</p>
        </div>

        <form @submit.prevent="register" class="space-y-6">
          <!-- 角色选择 (药丸切换) -->
          <div class="bg-slate-100 p-1.5 rounded-2xl flex gap-1 w-fit min-w-[240px]">
            <button type="button" @click="role = 'student'"
                    :class="['flex-1 py-2.5 px-6 rounded-xl text-sm font-bold transition-all duration-300', 
                            role === 'student' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500']">
              学生注册
            </button>
            <button type="button" @click="role = 'teacher'"
                    :class="['flex-1 py-2.5 px-6 rounded-xl text-sm font-bold transition-all duration-300', 
                            role === 'teacher' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500']">
              教师注册
            </button>
          </div>

          <!-- 第一行：账号与密码 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">{{ role === 'student' ? '学号' : '工号' }}</label>
              <div class="relative group">
                <UserIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-300 group-focus-within:text-blue-500 transition-colors" />
                <input type="text" v-model="formData.id"
                       class="w-full bg-slate-50 border-2 border-slate-100 pl-12 pr-4 py-3.5 rounded-2xl focus:bg-white focus:border-blue-500/30 outline-none transition-all font-medium text-slate-800"
                       :placeholder="role === 'student' ? '请输入学号' : '请输入工号'" required>
              </div>
            </div>
            <div class="space-y-2">
              <label class="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">姓名</label>
              <div class="relative group">
                <UserCircleIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-300 group-focus-within:text-blue-500 transition-colors" />
                <input type="text" v-model="formData.name"
                       class="w-full bg-slate-50 border-2 border-slate-100 pl-12 pr-4 py-3.5 rounded-2xl focus:bg-white focus:border-blue-500/30 outline-none transition-all font-medium text-slate-800"
                       placeholder="您的真实姓名" required>
              </div>
            </div>
          </div>

          <!-- 第二行：密码 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">设置密码</label>
              <div class="relative group">
                <LockIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-300 group-focus-within:text-blue-500 transition-colors" />
                <input type="password" v-model="formData.password"
                       class="w-full bg-slate-50 border-2 border-slate-100 pl-12 pr-4 py-3.5 rounded-2xl focus:bg-white focus:border-blue-500/30 outline-none transition-all font-medium text-slate-800"
                       placeholder="不少于 6 位" required>
              </div>
            </div>
            <div class="space-y-2">
              <label class="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">确认密码</label>
              <div class="relative group">
                <LockIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-300 group-focus-within:text-blue-500 transition-colors" />
                <input type="password" v-model="confirmPassword"
                       class="w-full bg-slate-50 border-2 border-slate-100 pl-12 pr-4 py-3.5 rounded-2xl focus:bg-white focus:border-blue-500/30 outline-none transition-all font-medium text-slate-800"
                       placeholder="请再次输入" required>
              </div>
            </div>
          </div>

          <!-- 第三行：性别与专业/职称 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">性别</label>
              <div class="relative group">
                <UsersIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-300 group-focus-within:text-blue-500 transition-colors" />
                <select v-model="formData.gender"
                        class="w-full bg-slate-50 border-2 border-slate-100 pl-12 pr-4 py-3.5 rounded-2xl focus:bg-white focus:border-blue-500/30 outline-none transition-all font-medium text-slate-800 appearance-none">
                  <option value="男">男</option>
                  <option value="女">女</option>
                </select>
              </div>
            </div>
            <div class="space-y-2">
              <label class="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">{{ role === 'student' ? '专业' : '职称' }}</label>
              <div class="relative group">
                <BadgeCheckIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-300 group-focus-within:text-blue-500 transition-colors" />
                <input v-if="role === 'student'" 
                       type="text" v-model="formData.major"
                       class="w-full bg-slate-50 border-2 border-slate-100 pl-12 pr-4 py-3.5 rounded-2xl focus:bg-white focus:border-blue-500/30 outline-none transition-all font-medium text-slate-800"
                       placeholder="如：计算机科学" required>
                <input v-else 
                       type="text" v-model="formData.title"
                       class="w-full bg-slate-50 border-2 border-slate-100 pl-12 pr-4 py-3.5 rounded-2xl focus:bg-white focus:border-blue-500/30 outline-none transition-all font-medium text-slate-800"
                       placeholder="如：副教授" required>
              </div>
            </div>
          </div>

          <!-- 第四行：学院与系所 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">所属学院</label>
              <div class="relative group">
                <SchoolIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-300 group-focus-within:text-blue-500 transition-colors" />
                <input type="text" v-model="formData.college"
                       class="w-full bg-slate-50 border-2 border-slate-100 pl-12 pr-4 py-3.5 rounded-2xl focus:bg-white focus:border-blue-500/30 outline-none transition-all font-medium text-slate-800"
                       placeholder="您的学院" required>
              </div>
            </div>
            <div class="space-y-2">
              <label class="text-[11px] font-black text-slate-400 uppercase tracking-widest ml-1">所在系所</label>
              <div class="relative group">
                <MapPinIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-300 group-focus-within:text-blue-500 transition-colors" />
                <input type="text" v-model="formData.department"
                       class="w-full bg-slate-50 border-2 border-slate-100 pl-12 pr-4 py-3.5 rounded-2xl focus:bg-white focus:border-blue-500/30 outline-none transition-all font-medium text-slate-800"
                       placeholder="您的系所" required>
              </div>
            </div>
          </div>

          <!-- 错误提示 -->
          <Transition enter-active-class="animate-shake">
            <div v-if="errorMessage" class="bg-red-50 text-red-500 p-4 rounded-2xl text-xs font-bold border border-red-100 flex items-center gap-3">
              <AlertCircleIcon class="w-4 h-4 flex-shrink-0" />
              {{ errorMessage }}
            </div>
          </Transition>

          <!-- 提交按钮 -->
          <button type="submit"
                  class="w-full py-5 bg-slate-900 hover:bg-blue-600 text-white font-black rounded-2xl shadow-xl active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50"
                  :disabled="loading">
            <span v-if="loading" class="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white"></span>
            <span class="tracking-wide">{{ loading ? '正在创建...' : '立即注册' }}</span>
            <ArrowRightIcon v-if="!loading" class="w-5 h-5" />
          </button>
        </form>

        <!-- 登录链接 -->
        <div class="pt-4 text-center">
          <p class="text-sm font-bold text-slate-400 uppercase tracking-widest">
            已经有账号了? 
            <router-link to="/login" class="text-blue-600 hover:underline ml-1">立即登录</router-link>
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
import { 
  User as UserIcon, 
  Lock as LockIcon, 
  AlertCircle as AlertCircleIcon,
  UserCircle as UserCircleIcon,
  Users as UsersIcon,
  BadgeCheck as BadgeCheckIcon,
  School as SchoolIcon,
  MapPin as MapPinIcon,
  ArrowRight as ArrowRightIcon
} from 'lucide-vue-next'

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

<style scoped>
@keyframes fade-in {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.animate-fade-in {
  animation: fade-in 0.8s ease-out forwards;
}

.animate-slide-up {
  animation: slide-up 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.animate-shake {
  animation: shake 0.4s ease-in-out;
}

.bg-clip-text {
  -webkit-background-clip: text;
  background-clip: text;
}

/* 隐藏滚动条但保留功能 */
.overflow-y-auto::-webkit-scrollbar {
  display: none;
}
.overflow-y-auto {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

@media (max-width: 1024px) {
  .lg\:flex {
    display: none;
  }
}
</style>
