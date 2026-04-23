<template>
  <div class="page-shell">
    <div class="page-container">
      <PageHeader title="作业管理" subtitle="按课程、动作类型和状态查看作业统计。" />

      <FilterBar>
        <div>
          <label class="mb-1 block text-xs font-semibold text-web-ink-600">课程</label>
          <select v-model="selectedClass" class="input-base">
            <option value="all">全部课程</option>
            <option v-for="cls in courses" :key="cls.id" :value="cls.id">{{ cls.name }}</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-web-ink-600">动作类型</label>
          <select v-model="selectedAiType" class="input-base">
            <option value="all">全部类型</option>
            <option value="squat">深蹲</option>
            <option value="pushup">俯卧撑</option>
            <option value="deadlift">硬拉</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-web-ink-600">作业状态</label>
          <select v-model="selectedStatus" class="input-base">
            <option value="all">全部状态</option>
            <option value="进行中">进行中</option>
            <option value="已截止">已截止</option>
          </select>
        </div>
      </FilterBar>

      <section class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="作业总数" :value="totalAssignmentsCount" tone="primary">
          <template #icon>
            <ClipboardListIcon class="w-5 h-5" />
          </template>
        </StatCard>
        <StatCard label="总提交人次" :value="totalSubmittedCount" tone="success">
          <template #icon>
            <UsersIcon class="w-5 h-5" />
          </template>
        </StatCard>
        <StatCard label="整体平均分" :value="overallAvgScore" tone="warning">
          <template #icon>
            <LineChartIcon class="w-5 h-5" />
          </template>
        </StatCard>
      </section>

      <SectionCard title="作业详情">
        <div v-if="loading" class="py-10 text-center text-web-ink-500">正在加载...</div>
        <div v-else-if="errorMsg" class="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{{ errorMsg }}</div>

        <EmptyState
          v-else-if="filteredAssignments.length === 0"
          title="暂无符合条件的作业"
          description="请调整筛选条件后重试。"
        />

        <DataTable v-else>
          <table class="min-w-full text-sm">
            <thead class="bg-web-surface-100 text-web-ink-600">
              <tr>
                <th class="px-4 py-3 text-left">课程</th>
                <th class="px-4 py-3 text-left">作业标题</th>
                <th class="px-4 py-3 text-left">动作类型</th>
                <th class="px-4 py-3 text-left">截止时间</th>
                <th class="px-4 py-3 text-left">提交情况</th>
                <th class="px-4 py-3 text-center">平均分</th>
                <th class="px-4 py-3 text-center">状态</th>
                <th class="px-4 py-3 text-center">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="assignment in filteredAssignments" :key="assignment.id" class="border-t border-web-line-100">
                <td class="px-4 py-3">{{ getCourseName(assignment.courseId) }}</td>
                <td class="px-4 py-3 font-semibold text-web-ink-900">{{ assignment.title }}</td>
                <td class="px-4 py-3">{{ assignment.aiTypeDisplay }}</td>
                <td class="px-4 py-3">{{ formatDate(assignment.deadline) }}</td>
                <td class="px-4 py-3">{{ assignment.submittedCount }} / {{ assignment.totalStudents }}</td>
                <td class="px-4 py-3 text-center">{{ assignment.avgScore || '-' }}</td>
                <td class="px-4 py-3 text-center">
                  <StatusTag :value="assignment.status === '进行中' ? 'active' : 'expired'" />
                </td>
                <td class="px-4 py-3 text-center">
                  <div class="flex items-center justify-center gap-2">
                    <button class="btn-outline" @click="viewAssignmentDetails(assignment.courseId, assignment.id)">详情</button>
                    <button class="btn-primary" @click="goToGrading(assignment.courseId, assignment.id)">批改</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </DataTable>
      </SectionCard>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../../services/axios.js'
import { cacheService } from '@/services/DataCacheService'
import PageHeader from '../../components/ui/PageHeader.vue'
import FilterBar from '../../components/ui/FilterBar.vue'
import StatCard from '../../components/ui/StatCard.vue'
import SectionCard from '../../components/ui/SectionCard.vue'
import DataTable from '../../components/ui/DataTable.vue'
import StatusTag from '../../components/ui/StatusTag.vue'
import EmptyState from '../../components/ui/EmptyState.vue'
import { ClipboardList as ClipboardListIcon, Users as UsersIcon, LineChart as LineChartIcon } from 'lucide-vue-next'

const router = useRouter()

const courses = ref([])
const assignments = ref([])
const loading = ref(true)
const errorMsg = ref('')

const selectedClass = ref('all')
const selectedAiType = ref('all')
const selectedStatus = ref('all')

const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const teacherId = currentUser.id || ''
const jwt = currentUser.token || 'valid_teacher_jwt'

const aiTypeMap = {
  squat: '深蹲',
  pushup: '俯卧撑',
  deadlift: '硬拉'
}

const loadData = async () => {
  loading.value = true
  errorMsg.value = ''

  try {
    const courseResp = await cacheService.fetchWithCache(`teacher_course_ids:${teacherId}`, () =>
      apiClient.post('/Course/get_course_id_by_teacher', { First: teacherId, Second: jwt })
    )

    if (!courseResp.data.success) {
      errorMsg.value = '获取课程失败'
      return
    }

    const courseIds = String(courseResp.data.data || '').split('\t\r').filter(Boolean)
    const coursePromises = courseIds.map((id) =>
      cacheService.fetchWithCache(`course_info:${id}`, () => apiClient.post('/Course/get_info_by_course_id', { First: id }))
    )
    const courseResps = await Promise.all(coursePromises)

    const processedResponses = courseResps.map((resp) => {
      if (!resp?.data?.data) return []
      return String(resp.data.data).trim().replace(/\t\r$/g, '').split(/\t\r/).filter(Boolean)
    })

    courses.value = processedResponses.filter((r) => r[0] >= 0).map((r, i) => ({ id: courseIds[i], name: r[1] }))

    const tempAssignments = []
    for (const courseId of courseIds) {
      const hwResp = await cacheService.fetchWithCache(`course_hw_ids:${courseId}`, () =>
        apiClient.post('/Homework/get_homework_id_by_course', {
          First: '1',
          Second: teacherId,
          Third: jwt,
          Fourth: courseId
        })
      )
      if (!hwResp.data.success || !hwResp.data.data) continue
      const hwIds = String(hwResp.data.data).split('\t\r').filter(Boolean)

      const studentResp = await cacheService.fetchWithCache(`course_student_ids:${courseId}`, () =>
        apiClient.post('/Course_student/get_student_id_by_course', {
          First: teacherId,
          Second: jwt,
          Third: courseId
        })
      )
      const totalStudents = studentResp.data.success && studentResp.data.data
        ? String(studentResp.data.data).split('\t\r').filter(Boolean).length
        : 0

      for (const hwId of hwIds) {
        const infoResp = await cacheService.fetchWithCache(`hw_info:${hwId}`, () =>
          apiClient.post('/Homework/get_info_by_homework_id', { First: courseId, Second: hwId })
        )
        if (!infoResp.data.success) continue

        const d = String(infoResp.data.data).split('\t\r').filter(Boolean)
        const deadline = new Date(d[2])
        const status = deadline > new Date() ? '进行中' : '已截止'

        const aiResp = await cacheService.fetchWithCache(`hw_ai_type:${hwId}`, () =>
          apiClient.post('/Homework/get_AI_type', { First: hwId })
        )
        let rawAiType = 'squat'
        if (aiResp.data.success) {
          rawAiType = String(aiResp.data.data).trim().split('\t\r')[0] || 'squat'
        }

        const submitResp = await cacheService.fetchWithCache(`hw_final_submits:${hwId}`, () =>
          apiClient.post('/Homework/get_final_submit', {
            First: teacherId,
            Second: jwt,
            Third: courseId,
            Fourth: hwId
          })
        )

        let submittedCount = 0
        let totalScore = 0
        let scoreCount = 0

        if (submitResp.data.success && submitResp.data.data) {
          const pairs = String(submitResp.data.data).split('\t\r').filter(Boolean)

          const detailPromises = pairs.map(async (pair) => {
            const [, submitId] = pair.split('\n')
            if (submitId === '-1' || submitId === '-2') return null

            const detailResp = await cacheService.fetchWithCache(`submit_detail:${submitId}`, () =>
              apiClient.post('/Homework/get_submit_info', {
                First: '1',
                Second: teacherId,
                Third: jwt,
                Fourth: submitId
              })
            )

            if (detailResp.data.success && detailResp.data.data) {
              const detail = String(detailResp.data.data).split('\t\r').filter(Boolean)
              return parseInt(detail[1], 10) || 0
            }
            return null
          })

          const scores = await Promise.all(detailPromises)
          scores.forEach((score) => {
            if (score !== null) {
              submittedCount += 1
              if (score > 0) {
                totalScore += score
                scoreCount += 1
              }
            }
          })
        }

        const avgScore = scoreCount > 0 ? (totalScore / scoreCount).toFixed(1) : null

        tempAssignments.push({
          id: hwId,
          courseId,
          title: d[0],
          description: d[1],
          deadline: d[2],
          create_time: d[3],
          aiType: rawAiType,
          aiTypeDisplay: aiTypeMap[rawAiType] || '标准动作',
          status,
          submittedCount,
          totalStudents,
          avgScore
        })
      }
    }

    assignments.value = tempAssignments
  } catch (err) {
    errorMsg.value = '加载失败'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const filteredAssignments = computed(() =>
  assignments.value.filter((item) => {
    const matchClass = selectedClass.value === 'all' || item.courseId === selectedClass.value
    const matchAiType = selectedAiType.value === 'all' || item.aiType === selectedAiType.value
    const matchStatus = selectedStatus.value === 'all' || item.status === selectedStatus.value
    return matchClass && matchAiType && matchStatus
  })
)

const totalAssignmentsCount = computed(() => filteredAssignments.value.length)
const totalSubmittedCount = computed(() => filteredAssignments.value.reduce((sum, a) => sum + a.submittedCount, 0))
const overallAvgScore = computed(() => {
  const validScores = filteredAssignments.value
    .filter((a) => a.avgScore !== null)
    .map((a) => parseFloat(a.avgScore))

  if (validScores.length === 0) return '-'
  const avg = validScores.reduce((sum, s) => sum + s, 0) / validScores.length
  return avg.toFixed(1)
})

const getCourseName = (courseId) => courses.value.find((item) => item.id === courseId)?.name || '未知课程'

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

const viewAssignmentDetails = (courseId, homeworkId) => {
  router.push(`/teacher/course/${courseId}/assignment/${homeworkId}`)
}

const goToGrading = (courseId, homeworkId) => {
  router.push(`/teacher/grade/course/${courseId}/assignment/${homeworkId}`)
}

onMounted(loadData)
</script>
