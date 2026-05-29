<template>
  <div class="page-shell">
    <div class="page-container">
      <PageHeader title="我的课程" subtitle="管理课程、学生和作业发布。">
        <template #actions>
          <button class="btn-primary" @click="goToCreateCourse">
            <PlusIcon class="w-4 h-4" />
            新建课程
          </button>
        </template>
      </PageHeader>

      <section class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="进行中课程" :value="teacherCourses.filter(c => c.is_active === '1').length" tone="primary">
          <template #icon>
            <GraduationCapIcon class="w-5 h-5" />
          </template>
        </StatCard>
        <StatCard label="已归档课程" :value="teacherCourses.filter(c => c.is_active === '2').length" tone="warning">
          <template #icon>
            <ArchiveIcon class="w-5 h-5" />
          </template>
        </StatCard>
        <StatCard label="课程总数" :value="teacherCourses.length" tone="success">
          <template #icon>
            <BookIcon class="w-5 h-5" />
          </template>
        </StatCard>
      </section>

      <SectionCard title="课程列表">
        <template #extra>
          <button class="btn-outline" @click="loadCourses">刷新</button>
        </template>

        <div v-if="loading" class="py-12 text-center text-web-ink-500">正在加载课程...</div>

        <div v-else-if="errorMsg" class="py-12 text-center">
          <p class="text-red-600 mb-4">{{ errorMsg }}</p>
          <button class="btn-primary" @click="loadCourses">重试</button>
        </div>

        <EmptyState
          v-else-if="teacherCourses.length === 0"
          title="暂无课程"
          description="点击右上角“新建课程”创建第一门课程。"
        >
          <template #icon>
            <BookIcon class="w-10 h-10 text-web-ink-500 mx-auto" />
          </template>
        </EmptyState>

        <div v-else class="space-y-3">
          <article
            v-for="course in teacherCourses"
            :key="course.id"
            class="rounded-xl border border-web-line-200 bg-white p-4 shadow-card"
          >
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <h3 class="text-lg font-bold text-web-ink-900">{{ course.name }}</h3>
                  <StatusTag :value="course.is_active" />
                </div>
                <p class="mt-1 text-sm text-web-ink-500">{{ course.info || '暂无描述' }}</p>
                <div class="mt-3 flex flex-wrap gap-4 text-xs text-web-ink-600">
                  <span>课程号：{{ course.subject || '-' }}</span>
                  <span>邀请码：{{ course.code || '-' }}</span>
                  <span>作业数：{{ course.assignmentCount }}</span>
                </div>
              </div>
              <ActionButtonGroup>
                <button class="btn-outline" @click="viewCourseDetails(course.id)">详情</button>
                <button class="btn-outline" @click="editCourse(course)">编辑</button>
                <button class="btn-outline" @click="manageStudents(course.id)">学生管理</button>
                <button class="btn-danger" @click="deleteCourse(course.id)">删除</button>
              </ActionButtonGroup>
            </div>
          </article>
        </div>
      </SectionCard>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/axios.js'
import { cacheService } from '../services/DataCacheService.js'
import PageHeader from '../components/ui/PageHeader.vue'
import SectionCard from '../components/ui/SectionCard.vue'
import StatCard from '../components/ui/StatCard.vue'
import StatusTag from '../components/ui/StatusTag.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import ActionButtonGroup from '../components/ui/ActionButtonGroup.vue'
import {
  Plus as PlusIcon,
  GraduationCap as GraduationCapIcon,
  Archive as ArchiveIcon,
  Book as BookIcon
} from 'lucide-vue-next'

const router = useRouter()

const teacherCourses = ref([])
const loading = ref(true)
const errorMsg = ref('')

const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const teacherId = String(currentUser.id || '').trim()
const jwt = String(currentUser.token || '').trim()

const loadCourses = async () => {
  loading.value = true
  errorMsg.value = ''

  try {
    if (!teacherId || !jwt) {
      errorMsg.value = '登录信息失效，请重新登录'
      teacherCourses.value = []
      return
    }

    const courseIdResp = await apiClient.post('/Course/get_course_id_by_teacher', {
      First: teacherId,
      Second: jwt
    })

    if (!courseIdResp.data.success) {
      errorMsg.value = courseIdResp.data.message || '获取课程列表失败'
      return
    }

    const rawIds = String(courseIdResp.data.data || '').trim()
    if (!rawIds || rawIds === 'NULL') {
      teacherCourses.value = []
      return
    }

    const courseIds = rawIds.split('\t\r').map(id => id.trim()).filter(Boolean)
    if (courseIds.length === 0) {
      teacherCourses.value = []
      return
    }

    const coursePromises = courseIds.map(async (id) => {
      const [courseResp, homeworkResp] = await Promise.all([
        apiClient.post('/Course/get_info_by_course_id', {
          First: id,
          Second: jwt
        }),
        apiClient.post('/Homework/get_homework_id_by_course', {
          First: '1',
          Second: teacherId,
          Third: jwt,
          Fourth: id
        })
      ])

      if (!courseResp.data.success) return null

      const parts = String(courseResp.data.data || '')
        .replace(/(\t\r)+$/g, '')
        .split(/\t\r/)

      const assignmentCount = homeworkResp.data.success
        ? String(homeworkResp.data.data || '')
            .trim()
            .split(/[\t\r\n]+/)
            .filter(Boolean).length
        : 0

      return {
        id,
        name: parts[1] || '未命名课程',
        info: parts[2] || '',
        code: parts[3] || '',
        subject: parts[3] || '',
        semester: parts[4] || '',
        is_active: String(parts[5] || '0'),
        created_time: parts[6] || '',
        assignmentCount
      }
    })

    teacherCourses.value = (await Promise.all(coursePromises)).filter(Boolean)
  } catch (err) {
    errorMsg.value = '加载失败，请检查网络连接'
    console.error(err)
  } finally {
    loading.value = false
  }
}

onMounted(loadCourses)

const viewCourseDetails = (courseId) => router.push(`/teacher/course/${courseId}`)
const goToCreateCourse = () => router.push('/teacher/createCourse')
const editCourse = (course) => router.push({ path: `/teacher/course/${course.id}/edit` })
const manageStudents = (courseId) => router.push(`/teacher/course/${courseId}/students`)

const deleteCourse = async (courseId) => {
  if (!confirm(`确定要删除课程 ${courseId} 吗？删除后不可恢复。`)) return

  try {
    const resp = await apiClient.post('/Course/delete_course', {
      First: teacherId,
      Second: jwt,
      Third: courseId
    })

    if (resp.data.success) {
      alert('课程删除成功')
      teacherCourses.value = teacherCourses.value.filter((c) => c.id !== courseId)
      cacheService.invalidate(`teacher_course_ids:${teacherId}`)
      cacheService.invalidate(`course_info:${courseId}`)
    } else {
      alert(`删除失败：${resp.data.message || '未知错误'}`)
    }
  } catch (err) {
    alert('删除失败，请稍后重试')
    console.error(err)
  }
}
</script>
