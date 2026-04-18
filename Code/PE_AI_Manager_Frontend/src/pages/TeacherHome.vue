<template>
  <div class="min-h-screen bg-slate-50 font-display">
    <div class="max-w-6xl mx-auto p-6 space-y-10">
      <!-- 顶部 Banner -->
      <div class="relative w-full rounded-2xl overflow-hidden shadow-xl kinetic-shadow">
        <img src="../assets/HomeHeader.jpg" class="w-full h-80 object-cover opacity-60" />
        <div class="absolute inset-0 bg-gradient-to-t from-slate-900/40 to-transparent">
          <div class="absolute inset-0 flex flex-col items-center justify-center space-y-4">
            <h2 class="text-5xl font-bold tracking-tight text-white drop-shadow-lg">
              智慧体育课堂
            </h2>
            <p class="text-xl text-white/90 font-medium">科学管理 · 高效教学</p>
          </div>
        </div>
      </div>

      <!-- 快捷数据概览 (取代原来的操作按钮) -->
      <section class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white p-6 rounded-2xl border border-slate-100 kinetic-shadow flex items-center space-x-4">
          <div class="p-3 rounded-xl bg-blue-50 text-blue-600">
            <GraduationCapIcon class="w-6 h-6" />
          </div>
          <div>
            <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">进行中课程</p>
            <p class="text-2xl font-black text-slate-900">{{ teacherCourses.filter(c => c.is_active === '1').length }}</p>
          </div>
        </div>
        <div class="bg-white p-6 rounded-2xl border border-slate-100 kinetic-shadow flex items-center space-x-4">
          <div class="p-3 rounded-xl bg-indigo-50 text-indigo-600">
            <ClipboardListIcon class="w-6 h-6" />
          </div>
          <div>
            <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">待评分作业</p>
            <p class="text-2xl font-black text-slate-900">12</p> <!-- Mock value -->
          </div>
        </div>
        <div class="bg-white p-6 rounded-2xl border border-slate-100 kinetic-shadow flex items-center space-x-4">
          <div class="p-3 rounded-xl bg-teal-50 text-teal-600">
            <VideoIcon class="w-6 h-6" />
          </div>
          <div>
            <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">分析资源</p>
            <p class="text-2xl font-black text-slate-900">24</p> <!-- Mock value -->
          </div>
        </div>
      </section>

      <!-- 课程列表 -->
      <section>
        <div class="flex justify-between items-center mb-6">
          <div class="flex items-center space-x-2">
            <GraduationCapIcon class="w-6 h-6 text-blue-600" />
            <h2 class="text-2xl font-bold text-slate-900">我的课程</h2>
          </div>
          <!-- 新建课程按钮 -->
          <button @click="goToCreateCourse" class="px-6 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 shadow-sm flex items-center space-x-2 kinetic-button">
            <PlusIcon class="w-5 h-5" />
            <span class="font-bold">新建课程</span>
          </button>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="text-center py-20">
          <div class="inline-block animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-blue-500"></div>
          <p class="mt-6 text-xl text-gray-600">加载您的课程中...</p>
        </div>

        <!-- 错误状态 -->
        <div v-else-if="errorMsg" class="text-center py-20">
          <p class="text-2xl text-red-600 mb-6">{{ errorMsg }}</p>
          <button @click="loadCourses" class="px-8 py-3 rounded-xl bg-blue-500 text-white hover:bg-blue-600 shadow-lg">
            重试
          </button>
        </div>

        <!-- 课程列表 -->
        <div v-else class="grid grid-cols-1 gap-4">
          <div v-if="teacherCourses.length === 0" class="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center kinetic-shadow">
            <BookIcon class="w-16 h-16 text-slate-200 mb-4 mx-auto" stroke-width="1.5" />
            <p class="text-lg font-bold text-slate-600 mb-2">暂无课程</p>
            <p class="text-slate-400 text-sm">您尚未创建任何课程，点击上方“新建课程”开始吧！</p>
          </div>
          <div v-else v-for="course in teacherCourses" :key="course.id"
            class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-all kinetic-shadow">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div class="flex-1">
                <div class="flex items-center space-x-3 mb-2">
                  <h3 class="text-xl font-bold text-slate-900">{{ course.name }}</h3>
                  <span :class="['text-xs px-2.5 py-1 rounded-full font-bold',
                    course.is_active === '1' ? 'bg-blue-50 text-blue-600 border border-blue-100' : 'bg-slate-100 text-slate-600 border border-slate-200']">
                    {{ course.is_active === '1' ? '进行中' : '未发布' }}
                  </span>
                </div>
                <p class="text-sm text-slate-500 mb-4 line-clamp-1">{{ course.info || '暂无描述' }}</p>
                <div class="flex items-center space-x-6 text-xs text-slate-400 font-medium">
                  <span class="flex items-center"><TagIcon class="w-3.5 h-3.5 mr-1.5" />{{ course.subject || '体育' }}</span>
                  <span class="flex items-center"><ClipboardListIcon class="w-3.5 h-3.5 mr-1.5" />作业: {{ course.assignmentCount > 0 ? course.assignmentCount : '暂无' }}</span>
                  <span class="flex items-center"><HashIcon class="w-3.5 h-3.5 mr-1.5" />邀请码: {{ course.code || '暂无' }}</span>
                </div>
              </div>
              <div class="flex flex-wrap gap-2">
                <button @click="viewCourseDetails(course.id)" class="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg text-sm font-bold transition-colors kinetic-button">
                  查看详情
                </button>
                <button @click="editCourse(course)" class="px-4 py-2 text-slate-600 hover:bg-slate-50 rounded-lg text-sm font-bold transition-colors kinetic-button">
                  编辑
                </button>
                <button @click="manageStudents(course.id)" class="px-4 py-2 text-slate-600 hover:bg-slate-50 rounded-lg text-sm font-bold transition-colors kinetic-button">
                  学生管理
                </button>
                <button @click="deleteCourse(course.id)" class="px-4 py-2 text-red-500 hover:bg-red-50 rounded-lg text-sm font-bold transition-colors kinetic-button">
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/axios.js'
import { controllers } from 'chart.js'
import { cacheService } from '../services/DataCacheService.js'
import { Rocket as RocketIcon, FilePlus as FilePlusIcon, Video as VideoIcon, BookOpen as BookOpenIcon, BarChart3 as BarChart3Icon, Plus as PlusIcon, GraduationCap as GraduationCapIcon, Book as BookIcon, Tag as TagIcon, ClipboardList as ClipboardListIcon, Hash as HashIcon } from 'lucide-vue-next'

const router = useRouter()

const teacherCourses = ref([])
const loading = ref(true)
const errorMsg = ref('')

const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const teacherId = currentUser.id || ''
const jwt = currentUser.token || ''

const loadCourses = async () => {
  loading.value = true
  errorMsg.value = ''

  try {
    const courseIdResp = await apiClient.post('/Course/get_course_id_by_teacher', {
      First: teacherId,
      Second: jwt
    })

    if (!courseIdResp.data.success) {
      errorMsg.value = '获取课程列表失败'
      return
    }
    const courseIdStr = courseIdResp.data.data
    const courseIds = courseIdStr ? courseIdStr.split('\t\r').filter(Boolean) : []

    if (courseIds.length === 0) {
      loading.value = false
      return
    }

    const coursePromises = courseIds.map(async (id) => {
      const [courseResp, homeworkResp] = await Promise.all([
        apiClient.post('/Course/get_info_by_course_id', { First: id }),
        apiClient.post('/Homework/get_homework_id_by_course', {
          First: '1',
          Second: teacherId,
          Third: jwt,
          Fourth: id
        })
      ])

      if (!courseResp.data.success) return null
      const courseRespData = courseResp.data.data.trim().replace(/\t\r$/g, '');
      const courseRespDataArray = courseRespData.split(/\t\r/).filter(item => item !== '');

      let assignmentCount = 0
      if (homeworkResp.data.success) {
        const homeworkIdStr = homeworkResp.data.data
        assignmentCount = homeworkIdStr.trim().split(/[\t\r\n]+/).filter(Boolean).length
      }

      return {
        id: id,
        name: courseRespDataArray[1],
        info: courseRespDataArray[2],
        code: courseRespDataArray[3],
        subject: courseRespDataArray[3] || '未知课号',
        semester: courseRespDataArray[4],
        is_active: courseRespDataArray[5],
        created_time: courseRespDataArray[6],
        assignmentCount: assignmentCount
      }
    })

    const results = await Promise.all(coursePromises)
    teacherCourses.value = results.filter(Boolean)

  } catch (err) {
    errorMsg.value = '加载失败，请检查网络'
    console.error(err)
  } finally {
    loading.value = false
  }
}

onMounted(loadCourses)

// 导航函数
const goToPublish = () => router.push('/teacher/publish')
const goToVideos = () => router.push('/teacher/videos')
const goToAssignments = () => router.push('/teacher/assignments')
const goToDashboard = () => router.push('/teacher/dashboard')
const viewCourseDetails = (courseId) => router.push(`/teacher/course/${courseId}`)

// 新建课程
const goToCreateCourse = () => {
  router.push('/teacher/createCourse')  // 新建模式
}

// 编辑课程
const editCourse = (course) => {
  router.push({
    path: `/teacher/course/${course.id}/edit`,
  })
}

// 学生管理
const manageStudents = (courseId) => {
  router.push(`/teacher/course/${courseId}/students`)
}

// 删除课程
const deleteCourse = async (courseId) => {
  if (!confirm(`确定要删除课程 ${courseId} 吗？删除后不可恢复！`)) return

  try {
    const resp = await apiClient.post('/Course/delete_course', {
      First: courseId,     // course_id
      Second: teacherId,   // teacher_id
      Third: jwt
    })

    if (resp.data.success) {  // 成功标志
      alert('课程删除成功')
      teacherCourses.value = teacherCourses.value.filter(c => c.id !== courseId)
      cacheService.invalidate(`teacher_course_ids:${teacherId}`)
      cacheService.invalidate(`course_info:${courseId}`)
    } else {
      alert('删除失败：' + (resp.data.message || '未知错误'))
    }
  } catch (err) {
    alert('删除失败，请检查网络')
    console.error(err)
  }
}
</script>
