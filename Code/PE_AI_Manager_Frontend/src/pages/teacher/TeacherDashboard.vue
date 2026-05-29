<template>
  <div class="page-shell">
    <div class="page-container">
      <PageHeader title="数据看板" subtitle="查看课程作业提交、成绩分布和优秀率趋势。">
        <template #actions>
          <button class="btn-outline" @click="goBack">返回</button>
          <button class="btn-primary" :disabled="loading || stats.totalSubmissions === 0" @click="exportToExcel">
            导出 Excel
          </button>
        </template>
      </PageHeader>

      <FilterBar :summary="`当前筛选：${filterText}`">
        <div>
          <label class="mb-1 block text-xs font-semibold text-web-ink-600">课程</label>
          <select v-model="query.courseId" class="input-base" @change="fetchData">
            <option value="">全部课程</option>
            <option v-for="cls in courses" :key="cls.id" :value="cls.id">{{ cls.name }}</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-web-ink-600">开始日期</label>
          <input v-model="query.startDate" type="date" class="input-base" @change="fetchData" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-web-ink-600">结束日期</label>
          <input v-model="query.endDate" type="date" class="input-base" @change="fetchData" />
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-web-ink-600">动作类型</label>
          <select v-model="query.aiType" class="input-base" @change="fetchData">
            <option value="">全部类型</option>
            <option value="squat">深蹲</option>
            <option value="pushup">俯卧撑</option>
            <option value="deadlift">硬拉</option>
          </select>
        </div>
      </FilterBar>

      <div v-if="loading" class="py-12 text-center text-web-ink-500">正在加载统计数据...</div>

      <div v-else-if="stats.totalSubmissions > 0" class="space-y-6">
        <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="总提交次数" :value="stats.totalSubmissions" tone="primary" />
          <StatCard label="平均成绩" :value="stats.avgFinalScore !== null ? stats.avgFinalScore.toFixed(1) : '-'" tone="success" />
          <StatCard label="提交率" :value="`${stats.completionRate.toFixed(1)}%`" tone="warning" />
          <StatCard label="优秀率" :value="`${stats.excellentRate.toFixed(1)}%`" tone="warning" />
        </section>

        <section class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SectionCard title="作业提交率">
            <canvas ref="submissionChart" class="max-h-96 w-full"></canvas>
          </SectionCard>
          <SectionCard title="平均成绩趋势">
            <canvas ref="scoreTrendChart" class="max-h-96 w-full"></canvas>
          </SectionCard>
          <SectionCard title="各作业优秀率">
            <canvas ref="excellentRateChart" class="max-h-96 w-full"></canvas>
          </SectionCard>
          <SectionCard title="成绩分布">
            <canvas ref="scoreDistChart" class="max-h-96 w-full"></canvas>
          </SectionCard>
        </section>
      </div>

      <EmptyState v-else title="暂无数据" description="当前筛选条件下没有提交记录。" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import Chart from 'chart.js/auto'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import dayjs from 'dayjs'
import apiClient from '../../services/axios.js'
import { cacheService } from '../../services/DataCacheService.js'
import PageHeader from '../../components/ui/PageHeader.vue'
import FilterBar from '../../components/ui/FilterBar.vue'
import StatCard from '../../components/ui/StatCard.vue'
import SectionCard from '../../components/ui/SectionCard.vue'
import EmptyState from '../../components/ui/EmptyState.vue'

const router = useRouter()

const courses = ref([])
const submissions = ref([])
const loading = ref(true)

const query = ref({
  courseId: '',
  startDate: '',
  endDate: '',
  aiType: ''
})

const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const teacherId = currentUser.id || ''
const jwt = currentUser.token || ''

const aiTypeMap = {
  squat: '深蹲',
  pushup: '俯卧撑',
  deadlift: '硬拉'
}

const parseDate = (str) => {
  if (!str || !str.trim()) return null
  let date = dayjs(str.trim())
  if (!date.isValid()) {
    date = dayjs(str.trim(), 'MM/DD/YYYY h:mm:ss A')
  }
  return date.isValid() ? date.toDate() : null
}

const loadData = async () => {
  loading.value = true
  courses.value = []
  submissions.value = []

  try {
    const courseIdResp = await cacheService.fetchWithCache(`teacher_course_ids:${teacherId}`, () =>
      apiClient.post('/Course/get_course_id_by_teacher', { First: teacherId, Second: jwt })
    )
    if (!courseIdResp.data.success || !courseIdResp.data.data) return

    const courseIds = String(courseIdResp.data.data).split('\t\r').filter(Boolean)

    const coursePromises = courseIds.map((id) =>
      cacheService.fetchWithCache(`course_info:${id}`, () => apiClient.post('/Course/get_info_by_course_id', { First: id }))
    )
    const courseResps = await Promise.all(coursePromises)

    courses.value = courseResps
      .map((resp, i) => {
        if (!resp?.data?.data) return null
        const parts = String(resp.data.data).replace(/(\t\r)+$/g, '').split('\t\r')
        return parts.length > 1 ? { id: courseIds[i], name: parts[1] } : null
      })
      .filter(Boolean)

    for (const courseId of courseIds) {
      const hwResp = await cacheService.fetchWithCache(`course_homework_ids:${courseId}`, () =>
        apiClient.post('/Homework/get_homework_id_by_course', {
          First: '1',
          Second: teacherId,
          Third: jwt,
          Fourth: courseId
        })
      )
      if (!hwResp.data.success || !hwResp.data.data) continue
      const hwIds = String(hwResp.data.data).split('\t\r').map(s => s.trim()).filter(s => s && s !== 'NULL')

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
        const infoResp = await cacheService.fetchWithCache(`homework_info:${hwId}`, () =>
          apiClient.post('/Homework/get_info_by_homework_id', { First: courseId, Second: hwId })
        )
        if (!infoResp.data.success || !infoResp.data.data) continue
        const infoParts = String(infoResp.data.data).replace(/(\t\r)+$/g, '').split('\t\r')
        const title = infoParts[0] || '未命名作业'

        const aiResp = await cacheService.fetchWithCache(`homework_ai_config:${hwId}`, () =>
          apiClient.post('/Homework/get_AI_type', { First: hwId })
        )
        const rawAiType = aiResp.data?.data ? String(aiResp.data.data).split('\t\r')[0] || 'squat' : 'squat'

        const submitResp = await cacheService.fetchWithCache(`final_submits:${hwId}`, () =>
          apiClient.post('/Homework/get_final_submit', {
            First: teacherId,
            Second: jwt,
            Third: courseId,
            Fourth: hwId
          })
        )
        if (!submitResp.data.success || !submitResp.data.data) continue

        const pairs = String(submitResp.data.data).split('\t\r').filter(Boolean)
        for (const pair of pairs) {
          const [studentId, submitId] = pair.split('\n')
          if (submitId === '-1' || submitId === '-2') continue

          const detailResp = await cacheService.fetchWithCache(`submit_detail:${submitId}`, () =>
            apiClient.post('/Homework/get_submit_info', {
              First: '1',
              Second: teacherId,
              Third: jwt,
              Fourth: submitId
            })
          )

          if (detailResp.data.success && detailResp.data.data) {
            const detail = String(detailResp.data.data).trim().replace(/\t\r$/g, '').split('\t\r')
            const score = parseInt(detail[1], 10) || 0
            const submissionTime = parseDate(detail[4] || '')

            if (submissionTime) {
              submissions.value.push({
                courseId,
                homeworkId: hwId,
                homeworkTitle: title,
                aiType: rawAiType,
                studentId,
                score,
                submissionTime,
                totalStudents
              })
            }
          }
        }
      }
    }
  } catch (err) {
    console.error('加载失败', err)
  } finally {
    loading.value = false
  }
}

const filteredSubmissions = computed(() =>
  submissions.value.filter((item) => {
    const matchCourse = !query.value.courseId || item.courseId === query.value.courseId
    const matchAiType = !query.value.aiType || item.aiType === query.value.aiType
    const subTime = item.submissionTime
    const start = query.value.startDate ? new Date(query.value.startDate) : null
    const end = query.value.endDate ? new Date(`${query.value.endDate}T23:59:59`) : null
    const matchDate = (!start || subTime >= start) && (!end || subTime <= end)
    return matchCourse && matchAiType && matchDate
  })
)

const stats = computed(() => {
  const list = filteredSubmissions.value
  if (list.length === 0) {
    return {
      totalSubmissions: 0,
      avgFinalScore: null,
      completionRate: 0,
      excellentRate: 0,
      assignmentSubmission: [],
      assignmentExcellent: [],
      scoreTrend: [],
      scoreDistribution: []
    }
  }

  const hwMap = new Map()
  list.forEach((s) => {
    const key = `${s.courseId}-${s.homeworkId}`
    if (!hwMap.has(key)) {
      hwMap.set(key, {
        title: s.homeworkTitle,
        submitted: 0,
        totalStudents: s.totalStudents,
        scores: [],
        excellentCount: 0
      })
    }
    const hw = hwMap.get(key)
    hw.submitted += 1
    if (s.score > 0) {
      hw.scores.push(s.score)
      if (s.score >= 90) hw.excellentCount += 1
    }
  })

  const assignmentSubmission = Array.from(hwMap.values()).map((hw) => ({
    title: hw.title,
    submitted: hw.submitted,
    total: hw.totalStudents,
    avgScore: hw.scores.length > 0 ? Number((hw.scores.reduce((a, b) => a + b, 0) / hw.scores.length).toFixed(1)) : null,
    excellentRate: hw.submitted > 0 ? Number(((hw.excellentCount / hw.submitted) * 100).toFixed(1)) : 0
  }))

  const totalSubmissions = list.length
  const totalStudentsAll = assignmentSubmission.reduce((sum, a) => sum + a.total, 0)
  const completionRate = totalStudentsAll > 0 ? Number(((totalSubmissions / totalStudentsAll) * 100).toFixed(1)) : 0

  const validScores = list.filter((s) => s.score > 0).map((s) => s.score)
  const avgFinalScore = validScores.length > 0 ? Number((validScores.reduce((a, b) => a + b, 0) / validScores.length).toFixed(1)) : null

  const excellentAssignments = assignmentSubmission.filter((a) => a.avgScore >= 90).length
  const excellentRate = assignmentSubmission.length > 0 ? Number(((excellentAssignments / assignmentSubmission.length) * 100).toFixed(1)) : 0

  const assignmentExcellent = assignmentSubmission.map((a) => ({ title: a.title, excellentRate: a.excellentRate }))
  const scoreTrend = assignmentSubmission.map((hw) => ({ date: hw.title, avgScore: hw.avgScore || 0 }))
  const scoreDistribution = [
    { label: '优秀 (90-100)', count: list.filter((s) => s.score >= 90).length, color: '#139769' },
    { label: '良好 (80-89)', count: list.filter((s) => s.score >= 80 && s.score < 90).length, color: '#236df2' },
    { label: '及格 (60-79)', count: list.filter((s) => s.score >= 60 && s.score < 80).length, color: '#ea8814' },
    { label: '不及格 (<60)', count: list.filter((s) => s.score < 60).length, color: '#d63e35' }
  ]

  return {
    totalSubmissions,
    avgFinalScore,
    completionRate,
    excellentRate,
    assignmentSubmission,
    assignmentExcellent,
    scoreTrend,
    scoreDistribution
  }
})

const filterText = computed(() => {
  const parts = []
  if (query.value.courseId) {
    const c = courses.value.find((c) => c.id === query.value.courseId)
    parts.push(c ? c.name : '未知课程')
  } else {
    parts.push('全部课程')
  }
  if (query.value.aiType) parts.push(aiTypeMap[query.value.aiType])
  parts.push(`${query.value.startDate || '开始'} 至 ${query.value.endDate || '现在'}`)
  return parts.join(' | ')
})

const submissionChart = ref(null)
const scoreTrendChart = ref(null)
const excellentRateChart = ref(null)
const scoreDistChart = ref(null)

let subChart = null
let trendChart = null
let excellentChart = null
let distChart = null

const renderCharts = () => {
  ;[subChart, trendChart, excellentChart, distChart].forEach((c) => c?.destroy())
  const s = stats.value

  if (submissionChart.value && s.assignmentSubmission.length > 0) {
    subChart = new Chart(submissionChart.value, {
      type: 'bar',
      data: {
        labels: s.assignmentSubmission.map((i) => i.title),
        datasets: [
          {
            label: '提交率(%)',
            data: s.assignmentSubmission.map((i) => (i.total > 0 ? ((i.submitted / i.total) * 100).toFixed(1) : 0)),
            backgroundColor: '#236df2',
            borderRadius: 8
          }
        ]
      },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 100 } } }
    })
  }

  if (scoreTrendChart.value && s.scoreTrend.length > 0) {
    trendChart = new Chart(scoreTrendChart.value, {
      type: 'line',
      data: {
        labels: s.scoreTrend.map((i) => i.date),
        datasets: [
          {
            label: '平均分',
            data: s.scoreTrend.map((i) => i.avgScore),
            borderColor: '#236df2',
            backgroundColor: 'rgba(35,109,242,0.15)',
            tension: 0.35,
            fill: true
          }
        ]
      },
      options: { responsive: true, plugins: { legend: { position: 'top' } }, scales: { y: { beginAtZero: true, max: 100 } } }
    })
  }

  if (excellentRateChart.value && s.assignmentExcellent.length > 0) {
    excellentChart = new Chart(excellentRateChart.value, {
      type: 'bar',
      data: {
        labels: s.assignmentExcellent.map((i) => i.title),
        datasets: [
          {
            label: '优秀率(%)',
            data: s.assignmentExcellent.map((i) => i.excellentRate),
            backgroundColor: '#ea8814',
            borderRadius: 8
          }
        ]
      },
      options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, max: 100 } } }
    })
  }

  if (scoreDistChart.value && s.scoreDistribution.some((d) => d.count > 0)) {
    distChart = new Chart(scoreDistChart.value, {
      type: 'doughnut',
      data: {
        labels: s.scoreDistribution.map((d) => d.label),
        datasets: [
          {
            data: s.scoreDistribution.map((d) => d.count),
            backgroundColor: s.scoreDistribution.map((d) => d.color),
            borderWidth: 0
          }
        ]
      },
      options: { responsive: true, plugins: { legend: { position: 'right' } } }
    })
  }
}

const fetchData = async () => {
  await loadData()
  await nextTick()
  renderCharts()
}

const exportToExcel = () => {
  const s = stats.value
  if (s.assignmentSubmission.length === 0) {
    alert('暂无数据可导出')
    return
  }

  const tableData = s.assignmentSubmission.map((item) => ({
    作业名称: item.title,
    应交人数: item.total,
    已交人数: item.submitted,
    提交率: item.total > 0 ? (item.submitted / item.total * 100).toFixed(1) : '0',
    平均成绩: item.avgScore !== null ? item.avgScore.toFixed(1) : '-',
    优秀率: s.assignmentExcellent.find((e) => e.title === item.title)?.excellentRate || '0'
  }))

  tableData.push({
    作业名称: '汇总',
    应交人数: s.assignmentSubmission.reduce((sum, i) => sum + i.total, 0),
    已交人数: s.totalSubmissions,
    提交率: s.completionRate.toFixed(1),
    平均成绩: s.avgFinalScore !== null ? s.avgFinalScore.toFixed(1) : '-',
    优秀率: s.excellentRate.toFixed(1)
  })

  const ws = XLSX.utils.json_to_sheet(tableData)
  ws['!cols'] = [{ wch: 25 }, { wch: 12 }, { wch: 12 }, { wch: 14 }, { wch: 12 }, { wch: 14 }]

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '作业统计')

  const courseName = query.value.courseId
    ? courses.value.find((c) => c.id === query.value.courseId)?.name || '未知课程'
    : '全部课程'
  const fileName = `体育作业统计_${courseName}_${query.value.startDate || '全部'}_至_${query.value.endDate || '全部'}.xlsx`

  const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  saveAs(new Blob([wbout], { type: 'application/octet-stream' }), fileName)
}

const goBack = () => router.push('/teacher')

onMounted(() => {
  const end = new Date()
  const start = new Date()
  start.setDate(end.getDate() - 30)

  query.value.startDate = start.toISOString().split('T')[0]
  query.value.endDate = end.toISOString().split('T')[0]

  fetchData()
})
</script>
