<template>
  <div class="page-shell">
    <div class="page-container">
      <section class="rounded-2xl border border-web-line-200 bg-white/85 p-6 shadow-card">
        <h1 class="text-3xl font-bold text-web-ink-900">智慧运动课堂</h1>
        <p class="mt-2 text-sm text-web-ink-500">记录每一次进步，查看课程与作业完成情况。</p>
      </section>

      <section class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div class="rounded-2xl border border-web-line-200 bg-white p-4 shadow-card">
          <p class="text-xs font-semibold tracking-wide text-web-ink-500">已加入课程</p>
          <p class="mt-2 text-3xl font-bold text-web-ink-900">{{ courses.length }}</p>
        </div>
        <div class="rounded-2xl border border-web-line-200 bg-white p-4 shadow-card">
          <p class="text-xs font-semibold tracking-wide text-web-ink-500">完成作业数</p>
          <p class="mt-2 text-3xl font-bold text-web-ink-900">{{ totalCompletedAssignments }}</p>
        </div>
        <div class="rounded-2xl border border-web-line-200 bg-white p-4 shadow-card">
          <p class="text-xs font-semibold tracking-wide text-web-ink-500">平均完成率</p>
          <p class="mt-2 text-3xl font-bold text-web-ink-900">{{ averageCompletionRate }}%</p>
        </div>
      </section>

      <section class="rounded-2xl border border-web-line-200 bg-white p-5 shadow-card">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-xl font-bold text-web-ink-900">我的课程</h2>
          <div class="flex gap-2">
            <button class="btn-outline" @click="openAddCourseModal">加入课程</button>
            <button class="btn-outline" @click="fetchCourseList">刷新</button>
          </div>
        </div>

        <div v-if="loadingCourses" class="py-10 text-center text-web-ink-500">正在加载课程列表...</div>

        <div v-else-if="coursesError" class="rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-700">
          <p>{{ coursesErrorMessage }}</p>
        </div>

        <div v-else-if="courses.length === 0" class="rounded-lg border border-web-line-200 bg-web-surface-100 p-8 text-center">
          <p class="text-web-ink-700">暂无课程</p>
          <p class="mt-2 text-sm text-web-ink-500">点击“加入课程”输入课程码。</p>
        </div>

        <div v-else class="space-y-3">
          <article
            v-for="course in courses"
            :key="course.id"
            class="rounded-xl border border-web-line-200 bg-white p-4"
          >
            <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <h3 class="text-lg font-bold text-web-ink-900">{{ course.name }}</h3>
                  <span
                    class="rounded-full border px-2 py-0.5 text-xs font-semibold"
                    :class="course.status === '进行中' ? 'border-blue-200 bg-blue-50 text-blue-600' : 'border-slate-200 bg-slate-100 text-slate-600'"
                  >
                    {{ course.status }}
                  </span>
                </div>
                <p class="mt-1 text-sm text-web-ink-500">{{ course.description || '暂无课程描述' }}</p>
                <p class="mt-2 text-xs text-web-ink-600">
                  课程号：{{ course.subject || '-' }}
                  <span class="mx-2">|</span>
                  作业：{{ course.completedAssignments }}/{{ course.totalAssignments }}
                  <span class="mx-2">|</span>
                  完成率：{{ course.completionRate }}%
                </p>
              </div>
              <router-link :to="`/student/course/${course.id}`" class="btn-primary">进入课程</router-link>
            </div>
          </article>
        </div>
      </section>
    </div>

    <div v-if="showAddCourseModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4" @click="showAddCourseModal = false">
      <div class="w-full max-w-md rounded-2xl border border-web-line-200 bg-white p-6 shadow-soft" @click.stop>
        <h3 class="text-xl font-bold text-web-ink-900">加入课程</h3>
        <p class="mt-2 text-sm text-web-ink-500">请输入 6 位课程码。</p>

        <input v-model="courseCodeInput" type="text" class="input-base mt-4" maxlength="6" placeholder="例如：123456" />

        <p v-if="addCourseMessage" class="mt-3 text-sm" :class="addCourseSuccess ? 'text-green-600' : 'text-red-600'">
          {{ addCourseMessage }}
        </p>

        <div class="mt-5 flex gap-2">
          <button class="btn-outline flex-1" @click="showAddCourseModal = false">取消</button>
          <button class="btn-primary flex-1 justify-center" @click="handleAddCourse">加入</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { apiClient } from '../services/axios'

const showAddCourseModal = ref(false)
const courseCodeInput = ref('')
const addCourseMessage = ref('')
const addCourseSuccess = ref(false)

const courses = ref([])
const loadingCourses = ref(false)
const coursesError = ref(false)
const coursesErrorMessage = ref('')

const totalCompletedAssignments = computed(() =>
  courses.value.reduce((acc, course) => acc + Number(course?.completedAssignments || 0), 0)
)

const averageCompletionRate = computed(() => {
  if (!courses.value.length) return 0
  const totalRate = courses.value.reduce((acc, course) => acc + Number(course?.completionRate || 0), 0)
  return Math.round(totalRate / courses.value.length)
})

const fetchCourseList = async () => {
  loadingCourses.value = true
  coursesError.value = false
  coursesErrorMessage.value = ''

  try {
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
    const studentId = currentUser.id
    const token = (currentUser.token || '').trim()

    if (!studentId || !token) {
      throw new Error('登录信息失效，请重新登录')
    }

    const response = await apiClient.post('/Course_student/get_course_id_by_student', {
      first: studentId,
      second: token
    })

    if (!response.data.success) {
      throw new Error(response.data.message || '获取课程列表失败')
    }

    const raw = String(response.data.data || '').trim()
    if (!raw || raw === 'NULL') {
      courses.value = []
      return
    }

    const courseIdList = raw.split('\t\r').map((id) => id.trim()).filter(Boolean)

    const courseDetails = await Promise.all(
      courseIdList.map(async (courseId) => {
        try {
          const detailResponse = await apiClient.post('/Course/get_info_by_course_id', {
            first: courseId,
            second: token
          })

          if (!detailResponse.data.success || !detailResponse.data.data) return null

          const arr = String(detailResponse.data.data).split('\t\r')
          const isActive = String(arr[5] || '0')

          const homeworkResponse = await apiClient.post('/Homework/get_homework_id_by_course', {
            first: '0',
            second: studentId,
            third: token,
            fourth: courseId
          })

          let totalAssignments = 0
          if (homeworkResponse.data.success && homeworkResponse.data.data && homeworkResponse.data.data !== 'NULL') {
            totalAssignments = String(homeworkResponse.data.data).split('\t\r').map((x) => x.trim()).filter(Boolean).length
          }

          return {
            id: courseId,
            name: arr[1] || '未命名课程',
            description: arr[2] || '',
            subject: arr[3] || '',
            status: isActive === '1' ? '进行中' : '已结束',
            totalAssignments,
            completedAssignments: 0,
            completionRate: 0
          }
        } catch (error) {
          console.error(`获取课程 ${courseId} 详情失败`, error)
          return null
        }
      })
    )

    courses.value = courseDetails.filter(Boolean)
  } catch (err) {
    coursesError.value = true
    coursesErrorMessage.value = err?.response?.data?.message || err.message || '获取课程失败'
    courses.value = []
    console.error('获取课程列表失败:', err)
  } finally {
    loadingCourses.value = false
  }
}

const openAddCourseModal = () => {
  showAddCourseModal.value = true
  courseCodeInput.value = ''
  addCourseMessage.value = ''
  addCourseSuccess.value = false
}

const handleAddCourse = async () => {
  const code = courseCodeInput.value.trim()
  if (!/^\d{6}$/.test(code)) {
    addCourseMessage.value = '课程码必须是 6 位数字'
    addCourseSuccess.value = false
    return
  }

  try {
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
    const studentId = currentUser.id
    const token = currentUser.token

    const response = await apiClient.post('/Course_student/add_course', {
      first: studentId,
      second: token,
      third: code
    })

    if (!response.data.success) {
      throw new Error(response.data.message || '加入课程失败')
    }

    addCourseMessage.value = '加入课程成功'
    addCourseSuccess.value = true

    setTimeout(() => {
      showAddCourseModal.value = false
      fetchCourseList()
    }, 800)
  } catch (err) {
    addCourseMessage.value = err?.response?.data?.message || err.message || '加入课程失败'
    addCourseSuccess.value = false
  }
}

onMounted(fetchCourseList)
</script>
