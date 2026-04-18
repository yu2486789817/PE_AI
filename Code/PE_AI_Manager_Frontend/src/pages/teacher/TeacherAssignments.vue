<template>
  <div class="min-h-screen bg-slate-50 font-display">
    <div class="max-w-7xl mx-auto p-6 space-y-10">
      <div class="flex items-center space-x-3">
        <ClipboardListIcon class="w-8 h-8 text-blue-600" />
        <h2 class="text-3xl font-bold text-slate-900">作业统计</h2>
      </div>

      <!-- 筛选条件 -->
      <div class="glass-card p-6 rounded-2xl shadow-sm border border-slate-200 kinetic-shadow">
        <div class="flex items-center space-x-2 mb-4">
          <FilterIcon class="w-4 h-4 text-slate-400" />
          <span class="text-sm font-bold text-slate-700">筛选条件</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="space-y-1.5">
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider">选择班级</label>
            <select v-model="selectedClass" class="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-700 text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all shadow-sm cursor-pointer">
              <option value="all">所有班级</option>
              <option v-for="cls in courses" :key="cls.id" :value="cls.id">{{ cls.name }}</option>
            </select>
          </div>
          <div class="space-y-1.5">
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider">选择运动类型</label>
            <select v-model="selectedAiType" class="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-700 text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all shadow-sm cursor-pointer">
              <option value="all">所有类型</option>
              <option value="squat">深蹲</option>
              <option value="pushup">俯卧撑</option>
              <option value="deadlift">硬拉</option>
            </select>
          </div>
          <div class="space-y-1.5">
            <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider">作业状态</label>
            <select v-model="selectedStatus" class="w-full px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-700 text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all shadow-sm cursor-pointer">
              <option value="all">所有状态</option>
              <option value="进行中">进行中</option>
              <option value="已截止">已截止</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 kinetic-shadow flex items-center space-x-4">
          <div class="p-3 rounded-xl bg-blue-50 text-blue-600">
            <ClipboardListIcon class="w-6 h-6" />
          </div>
          <div>
            <div class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-0.5">总作业数</div>
            <div class="text-3xl font-bold text-slate-900">{{ totalAssignmentsCount }}</div>
          </div>
        </div>
        <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 kinetic-shadow flex items-center space-x-4">
          <div class="p-3 rounded-xl bg-teal-50 text-teal-600">
            <UsersIcon class="w-6 h-6" />
          </div>
          <div>
            <div class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-0.5">总提交人次</div>
            <div class="text-3xl font-bold text-teal-600">{{ totalSubmittedCount }}</div>
          </div>
        </div>
        <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 kinetic-shadow flex items-center space-x-4">
          <div class="p-3 rounded-xl bg-indigo-50 text-indigo-600">
            <LineChartIcon class="w-6 h-6" />
          </div>
          <div>
            <div class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-0.5">整体平均分</div>
            <div class="text-3xl font-bold text-indigo-600">{{ overallAvgScore }}</div>
          </div>
        </div>
      </div>

      <!-- 作业详情表格 -->
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 kinetic-shadow overflow-hidden">
        <div class="px-8 py-5 border-b border-slate-100 bg-slate-50/50 flex items-center space-x-2">
          <TableIcon class="w-5 h-5 text-slate-400" />
          <h3 class="text-lg font-bold text-slate-900">作业详情</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="bg-slate-50/50">
                <th class="text-left py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider">班级</th>
                <th class="text-left py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider">作业标题</th>
                <th class="text-left py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider">运动类型</th>
                <th class="text-left py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider">截止时间</th>
                <th class="text-left py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider">提交情况</th>
                <th class="text-left py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider text-center">平均分</th>
                <th class="text-left py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider text-center">状态</th>
                <th class="text-center py-4 px-6 text-xs font-bold text-slate-500 uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="assignment in filteredAssignments" :key="assignment.id" class="hover:bg-slate-50/80 transition-colors">
                <td class="py-4 px-6 text-sm text-slate-600 font-medium">{{ getCourseName(assignment.courseId) }}</td>
                <td class="py-4 px-6 text-sm font-bold text-slate-900">{{ assignment.title }}</td>
                <td class="py-4 px-6 text-sm">
                  <span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-50 text-indigo-600 border border-indigo-100">
                    {{ assignment.aiTypeDisplay }}
                  </span>
                </td>
                <td class="py-4 px-6 text-sm text-slate-500">{{ formatDate(assignment.deadline) }}</td>
                <td class="py-4 px-6 text-sm text-slate-600 font-medium">
                  {{ assignment.submittedCount }} / {{ assignment.totalStudents }}
                </td>
                <td class="py-4 px-6 text-sm font-bold text-slate-900 text-center">
                  {{ assignment.avgScore || '-' }}
                </td>
                <td class="py-4 px-6 text-center">
                  <span :class="['px-2.5 py-1 rounded-lg text-xs font-bold border',
                                 assignment.status === '进行中' ? 'bg-blue-50 text-blue-600 border-blue-100' : 'bg-red-50 text-red-600 border-red-100']">
                    {{ assignment.status }}
                  </span>
                </td>
                <td class="py-4 px-6 text-center">
                  <div class="flex items-center justify-center gap-2">
                    <button
                      @click="viewAssignmentDetails(assignment.courseId, assignment.id)"
                      class="px-4 py-1.5 rounded-lg bg-slate-50 text-slate-700 text-xs font-bold hover:bg-slate-100 border border-slate-200 transition-all kinetic-button"
                    >
                      详情
                    </button>
                    <button
                      @click="goToGrading(assignment.courseId, assignment.id)"
                      class="px-4 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-bold hover:bg-blue-700 shadow-sm transition-all kinetic-button"
                    >
                      批改
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="filteredAssignments.length === 0" class="text-center py-6 text-gray-500">
          暂无符合条件的作业
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../../services/axios.js'
import { cacheService } from '@/services/DataCacheService';
import { ClipboardList as ClipboardListIcon, Filter as FilterIcon, Users as UsersIcon, LineChart as LineChartIcon, Table as TableIcon } from 'lucide-vue-next'

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

// AI 类型中英文映射
const aiTypeMap = {
  squat: '深蹲',
  pushup: '俯卧撑',
  deadlift: '硬拉'
}

const loadData = async () => {
  loading.value = true
  errorMsg.value = ''

  try {
    // 1. 获取教师课程 (使用缓存包装)
    const courseResp = await cacheService.fetchWithCache(`teacher_course_ids:${teacherId}`, () =>
      apiClient.post('/Course/get_course_id_by_teacher', { First: teacherId, Second: jwt })
    )

    if (!courseResp.data.success) {
      errorMsg.value = '获取课程失败'
      loading.value = false
      return
    }

    const courseIds = courseResp.data.data.split('\t\r').filter(Boolean)

    // 并发获取课程信息
    const coursePromises = courseIds.map(id =>
      cacheService.fetchWithCache(`course_info:${id}`, () =>
        apiClient.post('/Course/get_info_by_course_id', { First: id })
      )
    )
    const courseResps = await Promise.all(coursePromises)

    const processedResponses = courseResps.map(resp => {
      if (!resp?.data?.data) return [];
      const data = resp.data.data.trim().replace(/\t\r$/g, '');
      return data.split(/\t\r/).filter(item => item !== '');
    });

    courses.value = processedResponses
      .filter(r => r[0] >= 0)
      .map((r, i) => ({ id: courseIds[i], name: r[1] }))

    // 2. 获取所有作业 + AI类型 + 提交统计
    const tempAssignments = []

    for (const courseId of courseIds) {
      // 获取作业列表 (缓存)
      const hwResp = await cacheService.fetchWithCache(`course_hw_ids:${courseId}`, () =>
        apiClient.post('/Homework/get_homework_id_by_course', {
          First: '1', Second: teacherId, Third: jwt, Fourth: courseId
        })
      )

      if (!hwResp.data.success || !hwResp.data.data) continue
      const hwIds = hwResp.data.data.split('\t\r').filter(Boolean)

      // 获取学生总数 (缓存)
      const studentResp = await cacheService.fetchWithCache(`course_student_ids:${courseId}`, () =>
        apiClient.post('/Course_student/get_student_id_by_course', {
          First: teacherId, Second: jwt, Third: courseId
        })
      )
      const totalStudents = studentResp.data.success && studentResp.data.data
        ? studentResp.data.data.split('\t\r').filter(Boolean).length
        : 0

      for (const hwId of hwIds) {
        // 获取作业基本信息 (缓存)
        const infoResp = await cacheService.fetchWithCache(`hw_info:${hwId}`, () =>
          apiClient.post('/Homework/get_info_by_homework_id', { First: courseId, Second: hwId })
        )
        if (!infoResp.data.success) continue

        const d = infoResp.data.data.split('\t\r').filter(Boolean)
        const deadline = new Date(d[2])
        const status = deadline > new Date() ? '进行中' : '已截止'

        // 获取 AI 类型 (缓存)
        const aiResp = await cacheService.fetchWithCache(`hw_ai_type:${hwId}`, () =>
          apiClient.post('/Homework/get_AI_type', { First: hwId })
        )
        let rawAiType = 'squat'
        if (aiResp.data.success) {
          const config = aiResp.data.data.trim()
          rawAiType = config.split('\t\r')[0] || 'squat'
        }

        // 获取所有学生提交情况
        const submitResp = await cacheService.fetchWithCache(`hw_final_submits:${hwId}`, () =>
          apiClient.post('/Homework/get_final_submit', {
            First: teacherId, Second: jwt, Third: courseId, Fourth: hwId
          })
        )

        let submittedCount = 0
        let totalScore = 0
        let scoreCount = 0

        if (submitResp.data.success && submitResp.data.data) {
          const pairs = submitResp.data.data.split('\t\r').filter(Boolean)

          // 获取提交详情
          const detailPromises = pairs.map(async (pair) => {
            const [studentId, submitId] = pair.split('\n')
            if (submitId === '-1' || submitId === '-2') return null

            const detailResp = await cacheService.fetchWithCache(`submit_detail:${submitId}`, () =>
              apiClient.post('/Homework/get_submit_info', {
                First: '1', Second: teacherId, Third: jwt, Fourth: submitId
              })
            )

            if (detailResp.data.success && detailResp.data.data) {
              const detail = detailResp.data.data.split('\t\r').filter(Boolean)
              return parseInt(detail[1]) || 0
            }
            return null
          })

          const scores = await Promise.all(detailPromises)

          // 统计计算
          scores.forEach(score => {
            if (score !== null) {
              submittedCount++
              if (score > 0) {
                totalScore += score
                scoreCount++
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

    // 最终赋值
    assignments.value = tempAssignments

  } catch (err) {
    errorMsg.value = '加载失败'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const filteredAssignments = computed(() => {
  return assignments.value.filter(item => {
    const matchClass = selectedClass.value === 'all' || item.courseId === selectedClass.value
    const matchAiType = selectedAiType.value === 'all' || item.aiType === selectedAiType.value
    const matchStatus = selectedStatus.value === 'all' || item.status === selectedStatus.value
    return matchClass && matchAiType && matchStatus
  })
})

const totalAssignmentsCount = computed(() => filteredAssignments.value.length)
const totalSubmittedCount = computed(() =>
  filteredAssignments.value.reduce((sum, a) => sum + a.submittedCount, 0)
)
const overallAvgScore = computed(() => {
  const validScores = filteredAssignments.value
    .filter(a => a.avgScore !== null)
    .map(a => parseFloat(a.avgScore))

  if (validScores.length === 0) return '-'
  const avg = validScores.reduce((sum, s) => sum + s, 0) / validScores.length
  return avg.toFixed(1)
})

const getCourseName = (courseId) => {
  const c = courses.value.find(item => item.id === courseId)
  return c ? c.name : '未知班级'
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

const viewAssignmentDetails = (courseId, homeworkId) => {
  router.push(`/teacher/course/${courseId}/assignment/${homeworkId}`)
}

const goToGrading = (courseId, homeworkId) => {
  router.push(`/teacher/grade/course/${courseId}/assignment/${homeworkId}`)
}

onMounted(loadData)
</script>
