<template>
  <div class="page-shell">
    <div class="page-container">
      <PageHeader :title="course?.name || '课程详情'" subtitle="管理课程信息、作业发布和课程归档。">
        <template #actions>
          <button class="btn-outline" @click="goBack">返回</button>
          <button class="btn-outline" @click="manageStudents">学生管理</button>
          <button class="btn-primary" :disabled="isArchived" @click="openPublishDialog">发布作业</button>
          <button class="btn-outline" @click="editCourse" :disabled="isArchived">编辑课程</button>
          <button class="btn-danger" @click="toggleArchive">{{ isArchived ? '取消归档' : '归档课程' }}</button>
        </template>
      </PageHeader>

      <SectionCard title="课程概览">
        <div v-if="loading" class="py-10 text-center text-web-ink-500">正在加载课程信息...</div>

        <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          <p>{{ errorMessage }}</p>
          <button class="btn-primary mt-3" @click="fetchCourseDetails">重试</button>
        </div>

        <div v-else-if="course" class="space-y-3">
          <p class="text-web-ink-600">{{ course.info || '暂无课程描述' }}</p>
          <div class="flex flex-wrap gap-6 text-sm text-web-ink-600">
            <div>课程号：{{ course.subject || '-' }}</div>
            <div>邀请码：{{ course.code || '-' }}</div>
            <div>作业数：{{ course.assignments.length }}</div>
            <div class="flex items-center gap-2">状态：<StatusTag :value="course.is_active" /></div>
          </div>
          <div v-if="isArchived" class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-amber-700">
            当前课程已归档，不能编辑课程和发布作业。
          </div>
        </div>
      </SectionCard>

      <SectionCard title="课程作业">
        <template #extra>
          <button class="btn-primary" :disabled="isArchived" @click="openPublishDialog">新建作业</button>
        </template>

        <EmptyState
          v-if="course && assignmentList.length === 0"
          title="暂无作业"
          description="点击“新建作业”开始布置课程任务。"
        />

        <div v-else-if="course" class="space-y-3">
          <article
            v-for="assignment in assignmentList"
            :key="assignment.id"
            class="rounded-lg border border-web-line-200 bg-white p-4"
          >
            <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h4 class="text-base font-bold text-web-ink-900">{{ assignment.title }}</h4>
                <p class="mt-1 text-sm text-web-ink-500">{{ assignment.description || '暂无描述' }}</p>
                <div class="mt-2 flex flex-wrap gap-3 text-xs text-web-ink-600">
                  <span>动作类型：{{ assignment.aiTypeDisplay }}</span>
                  <span>截止时间：{{ formatDate(assignment.deadline) }}</span>
                  <StatusTag :value="assignment.status === '进行中' ? 'active' : 'expired'" />
                </div>
              </div>
              <router-link :to="`/teacher/course/${course.id}/assignment/${assignment.id}`" class="btn-outline">
                查看详情
              </router-link>
            </div>
          </article>
        </div>
      </SectionCard>

      <el-dialog v-model="showPublishAssignment" title="发布新作业" width="680px">
        <form class="grid grid-cols-1 md:grid-cols-2 gap-4" @submit.prevent="submitForm">
          <div class="md:col-span-2">
            <label class="mb-1 block text-sm text-web-ink-600">作业标题</label>
            <input v-model="newAssignment.title" class="input-base" required placeholder="例如：深蹲动作训练" />
          </div>

          <div>
            <label class="mb-1 block text-sm text-web-ink-600">动作类型</label>
            <select v-model="newAssignment.aiType" class="input-base" required>
              <option value="">请选择动作类型</option>
              <option value="squat">深蹲</option>
              <option value="pushup">俯卧撑</option>
              <option value="deadlift">硬拉</option>
            </select>
          </div>

          <div>
            <label class="mb-1 block text-sm text-web-ink-600">要求次数</label>
            <input v-model.number="newAssignment.requiredCount" class="input-base" type="number" min="1" max="999" required />
          </div>

          <div class="md:col-span-2">
            <label class="mb-1 block text-sm text-web-ink-600">截止时间</label>
            <input v-model="newAssignment.deadline" class="input-base" type="datetime-local" required />
          </div>

          <div class="md:col-span-2">
            <label class="mb-1 block text-sm text-web-ink-600">作业描述</label>
            <textarea v-model="newAssignment.description" rows="4" class="input-base" required placeholder="填写动作要求与评分标准" />
          </div>

          <div class="md:col-span-2 flex justify-end gap-2">
            <button type="button" class="btn-outline" @click="showPublishAssignment = false">取消</button>
            <button type="submit" class="btn-primary">发布作业</button>
          </div>
        </form>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import dayjs from 'dayjs'
import apiClient from '../../services/axios.js'
import { cacheService } from '../../services/DataCacheService.js'
import { parseCourseInfo, parseHomeworkInfo, parseLegacyIdList } from '../../utils/legacyParse.js'
import PageHeader from '../../components/ui/PageHeader.vue'
import SectionCard from '../../components/ui/SectionCard.vue'
import StatusTag from '../../components/ui/StatusTag.vue'
import EmptyState from '../../components/ui/EmptyState.vue'

const router = useRouter()
const route = useRoute()

const course = ref(null)
const loading = ref(true)
const error = ref(false)
const errorMessage = ref('')
const showPublishAssignment = ref(false)

const newAssignment = ref({
  title: '',
  aiType: '',
  requiredCount: 30,
  description: '',
  deadline: ''
})

const courseId = route.params.courseId
const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const teacherId = currentUser.id || ''
const jwt = currentUser.token || ''

const aiTypeMap = {
  squat: '深蹲',
  pushup: '俯卧撑',
  deadlift: '硬拉'
}

const isArchived = computed(() => course.value?.is_active === '2')
const assignmentList = computed(() => course.value?.assignments || [])

const editCourse = () => {
  if (isArchived.value) {
    alert('课程已归档，不能编辑')
    return
  }
  router.push({ path: `/teacher/course/${courseId}/edit` })
}

const manageStudents = () => {
  router.push(`/teacher/course/${courseId}/students`)
}

const openPublishDialog = () => {
  if (isArchived.value) {
    alert('课程已归档，不能发布作业')
    return
  }
  showPublishAssignment.value = true
}

const toggleArchive = async () => {
  if (!course.value) return

  const willArchive = !isArchived.value
  const actionText = willArchive ? '归档' : '取消归档'
  if (!confirm(`确定要${actionText}该课程吗？`)) return

  try {
    const endpoint = willArchive ? '/Course/archive_course' : '/Course/unarchive_course'
    const resp = await apiClient.post(endpoint, {
      First: teacherId,
      Second: jwt,
      Third: courseId
    })

    if (!resp.data.success) {
      alert(`${actionText}失败：${resp.data.message || '未知错误'}`)
      return
    }

    course.value.is_active = willArchive ? '2' : '1'
    cacheService.invalidate(`course_info:${courseId}`)
    cacheService.invalidate(`teacher_course_ids:${teacherId}`)
    alert(`${actionText}成功`)
  } catch (err) {
    console.error(err)
    alert(`${actionText}失败，请稍后重试`)
  }
}

const fetchCourseDetails = async () => {
  loading.value = true
  error.value = false

  try {
    const courseResp = await cacheService.fetchWithCache(`course_info:${courseId}`, () =>
      apiClient.post('/Course/get_info_by_course_id', { First: courseId })
    )
    if (!courseResp.data.success) {
      errorMessage.value = '课程不存在或已被删除'
      error.value = true
      return
    }

    const c = parseCourseInfo(courseResp.data.data, courseId)

    course.value = {
      id: courseId,
      name: c.name,
      info: c.info,
      code: c.code,
      subject: courseId,
      is_active: String(c.isActive || '1'),
      assignments: []
    }

    const homeworkResp = await cacheService.fetchWithCache(`course_homework_ids:${courseId}`, () =>
      apiClient.post('/Homework/get_homework_id_by_course', {
        First: '1',
        Second: teacherId,
        Third: jwt,
        Fourth: courseId
      })
    )

    if (!homeworkResp.data.success || !homeworkResp.data.data || homeworkResp.data.data === 'NULL') {
      course.value.assignments = []
      return
    }

    const homeworkIds = parseLegacyIdList(homeworkResp.data.data)
    const assignmentPromises = homeworkIds.map(async (id) => {
      const [infoResp, aiResp] = await Promise.all([
        cacheService.fetchWithCache(`homework_info:${id}`, () =>
          apiClient.post('/Homework/get_info_by_homework_id', { First: courseId, Second: id })
        ),
        cacheService.fetchWithCache(`homework_ai_config:${id}`, () =>
          apiClient.post('/Homework/get_AI_type', { First: id })
        )
      ])

      if (!infoResp.data.success || !infoResp.data.data) return null

      const info = parseHomeworkInfo(infoResp.data.data, id)
      let rawAiType = 'squat'
      if (aiResp.data.success && aiResp.data.data) {
        rawAiType = String(aiResp.data.data).split('\t\r')[0] || 'squat'
      }

      return {
        id,
        title: info.title,
        description: info.description,
        deadline: info.deadline,
        status: info.deadline && new Date(info.deadline) > new Date() ? '进行中' : '已截止',
        aiType: rawAiType,
        aiTypeDisplay: aiTypeMap[rawAiType] || '未知动作'
      }
    })

    course.value.assignments = (await Promise.all(assignmentPromises)).filter(Boolean)
  } catch (err) {
    console.error(err)
    error.value = true
    errorMessage.value = '加载失败，请检查网络连接'
  } finally {
    loading.value = false
  }
}

const submitForm = async () => {
  if (isArchived.value) {
    alert('课程已归档，不能发布作业')
    return
  }

  if (
    !newAssignment.value.title ||
    !newAssignment.value.description ||
    !newAssignment.value.deadline ||
    !newAssignment.value.aiType ||
    !newAssignment.value.requiredCount
  ) {
    alert('请完整填写所有字段')
    return
  }

  try {
    const addResp = await apiClient.post('/Homework/new_homework', {
      First: teacherId,
      Second: jwt,
      Third: courseId,
      Fourth: newAssignment.value.title,
      Fifth: newAssignment.value.description,
      Sixth: dayjs(newAssignment.value.deadline).format('YYYY-MM-DD HH:mm:ss')
    })

    const homeworkId = String(addResp.data?.data || '').trim()
    if (!homeworkId) {
      alert('作业创建失败：未返回 ID')
      return
    }

    const setResp = await apiClient.post('/Homework/set_AI_type', {
      First: teacherId,
      Second: jwt,
      Third: courseId,
      Fourth: homeworkId,
      Fifth: newAssignment.value.aiType,
      Sixth: String(newAssignment.value.requiredCount)
    })

    if (!setResp.data.success) {
      alert('作业已创建，但 AI 配置失败')
    }

    alert('作业发布成功')
    cacheService.invalidate(`course_homework_ids:${courseId}`)
    showPublishAssignment.value = false
    newAssignment.value = { title: '', aiType: '', requiredCount: 30, description: '', deadline: '' }
    await fetchCourseDetails()
  } catch (err) {
    console.error(err)
    alert('发布失败，请稍后重试')
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const goBack = () => router.push('/teacher')

onMounted(fetchCourseDetails)
</script>
