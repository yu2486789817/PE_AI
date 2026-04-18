<template>
  <div class="min-h-screen bg-slate-50 font-display">
    <div class="max-w-6xl mx-auto p-6 space-y-10">
      <!-- 顶部导航栏 -->
      <div class="flex justify-between items-center py-4">
        <div class="flex items-center gap-2">
          <button @click="goBack" class="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors">
            返回
          </button>
        </div>

      </div>

      <section class="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div class="flex items-center space-x-4">
          <div class="p-4 rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-200">
            <PencilIcon class="w-8 h-8" />
          </div>
          <div>
            <h2 class="text-3xl font-bold text-slate-900 tracking-tight">{{ assignmentTitle }}</h2>
            <p class="text-slate-500 text-sm font-medium mt-1">查看学生提交并进行评分</p>
          </div>
        </div>
      </section>

      <!-- 加载状态 -->
      <div v-if="loading" class="flex justify-center items-center py-20">
        <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-500"></div>
      </div>

      <!-- 成绩表格 -->
      <section v-else class="glass-card rounded-2xl p-0 kinetic-shadow overflow-hidden border border-slate-200">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="bg-slate-50/50 border-b border-slate-100">
                <th class="text-left py-5 px-8 text-xs font-bold text-slate-500 uppercase tracking-wider">学生信息</th>
                <th class="text-center py-5 px-8 text-xs font-bold text-slate-500 uppercase tracking-wider">提交时间</th>
                <th class="text-center py-5 px-8 text-xs font-bold text-slate-500 uppercase tracking-wider">成绩</th>
                <th class="text-left py-5 px-8 text-xs font-bold text-slate-500 uppercase tracking-wider">AI反馈</th>
                <th class="text-left py-5 px-8 text-xs font-bold text-slate-500 uppercase tracking-wider">教师评价</th>
                <th class="text-center py-5 px-8 text-xs font-bold text-slate-500 uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="sub in studentSubmissions"
                :key="sub.studentId"
                class="hover:bg-slate-50/80 transition-colors"
              >
                <td class="py-6 px-8">
                  <div class="flex items-center gap-4">
                    <div class="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 text-lg font-bold border border-blue-100">
                      {{ sub.studentName.charAt(0) }}
                    </div>
                    <div>
                      <div class="font-bold text-slate-900">{{ sub.studentName }}</div>
                      <div class="text-xs text-slate-400 font-medium">学号：{{ sub.studentId }}</div>
                    </div>
                  </div>
                </td>

                <td class="py-6 px-8 text-center text-sm text-slate-500 font-medium">
                  {{ formatDate(sub.createTime) }}
                </td>

                <!-- 统一成绩列（字符串处理） -->
                <td class="py-6 px-8 text-center">
                  <div v-if="editingStudentId === sub.studentId" class="flex justify-center gap-2">
                    <input
                      v-model="editingScore"
                      type="text"
                      class="w-20 px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-center font-bold text-slate-900 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                      placeholder="分数"
                    />
                  </div>
                  <div v-else class="text-3xl font-black tracking-tight" :class="sub.score !== null ? 'text-blue-600' : 'text-slate-200'">
                    {{ sub.score ?? '-' }}
                  </div>
                </td>

                <td class="py-6 px-8">
                  <div class="max-w-xs text-sm text-slate-500 font-medium line-clamp-2" :title="sub.aiFeedback">
                    {{ sub.aiFeedback || '暂无反馈' }}
                  </div>
                </td>

                <td class="py-6 px-8">
                  <div v-if="editingStudentId === sub.studentId">
                    <input
                      v-model="editingComment"
                      type="text"
                      class="w-full max-w-xs px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none text-sm text-slate-900"
                      placeholder="输入评价..."
                    />
                  </div>
                  <div v-else class="max-w-xs text-sm text-slate-500 font-medium line-clamp-2" :title="sub.teacherFeedback">
                    {{ sub.teacherFeedback || '-' }}
                  </div>
                </td>

                <td class="py-6 px-8 text-center">
                  <div class="flex gap-2 justify-center">
                    <button
                      v-if="editingStudentId === sub.studentId"
                      @click="saveGrade(sub)"
                      class="px-4 py-2 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 shadow-sm text-xs transition-all kinetic-button flex items-center"
                    >
                      <CheckIcon class="w-3.5 h-3.5 mr-1" />
                      保存
                    </button>
                    <button
                      v-else-if="sub.submitId && sub.submitId !== '-1' && sub.submitId !== '-2'"
                      @click="startEdit(sub)"
                      class="px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-xl font-bold hover:bg-slate-50 shadow-sm text-xs transition-all kinetic-button flex items-center"
                    >
                      <Edit3Icon class="w-3.5 h-3.5 mr-1 text-blue-600" />
                      评分
                    </button>

                    <button
                      v-if="sub.videoUrl && !sub.videoUrl.includes('test')"
                      @click="viewVideo(sub.studentId, sub.studentName)"
                      class="px-4 py-2 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 shadow-sm text-xs transition-all kinetic-button flex items-center"
                    >
                      <VideoIcon class="w-3.5 h-3.5 mr-1" />
                      分析
                    </button>
                    <span v-else class="text-slate-300 text-xs font-medium">尚未提交</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 无提交记录 -->
        <div v-if="studentSubmissions.length === 0" class="py-24 text-center">
          <FileQuestionIcon class="w-16 h-16 text-slate-200 mb-4 mx-auto" stroke-width="1.5" />
          <h3 class="text-lg font-bold text-slate-900 mb-2">暂无提交记录</h3>
          <p class="text-slate-400 text-sm font-medium">该作业目前还没有学生提交</p>
        </div>
      </section>
    </div>

    <!-- 视频播放对话框 -->
    <el-dialog
      v-model="videoDialogVisible"
      :title="currentVideoTitle"
      width="800px"
      top="5vh"
      :destroy-on-close="true"
      @closed="currentVideoUrl = ''"
    >
      <div class="bg-black rounded-xl p-2">
        <SSEVideoPlayer
          v-if="videoDialogVisible && currentVideoUrl"
      :stream-url="currentVideoUrl"
      />
      </div>

      <template #footer>
        <div class="flex justify-center pb-4">
          <el-button @click="videoDialogVisible = false" type="info" plain>关闭预览</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {apiClient, aiClient} from '../../services/axios.js'
import SSEVideoPlayer from '@/components/SSEVideoPlayer.vue'
import { cacheService } from '../../services/DataCacheService.js'
import { Pencil as PencilIcon, Check as CheckIcon, Video as VideoIcon, Edit3 as Edit3Icon, FileQuestion as FileQuestionIcon, ChevronLeft as ChevronLeftIcon } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const courseId = route.params.courseId
const assignmentId = route.params.assignmentId

const loading = ref(true)
const assignmentTitle = ref('加载中...')
const studentSubmissions = ref([])

const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const teacherId = currentUser.id || ''
const jwt = currentUser.token || ''

// 编辑状态
const editingStudentId = ref(null)
const editingScore = ref('')
const editingComment = ref('')

// 视频播放对话框控制
const videoDialogVisible = ref(false)
const currentVideoUrl = ref('')
const currentVideoTitle = ref('AI 分析视频')

// 根据学号查询学生姓名
const fetchStudentName = async (studentId) => {
  try {
    // 跨页面共享学生信息缓存
    const resp = await cacheService.fetchWithCache(`user_info:${studentId}`, () =>
      apiClient.post('/User/get_student_info', {
        First: teacherId,
        Second: jwt,
        Third: '1',
        Fourth: studentId
      })
    )

    if (resp.data.success && resp.data.data) {
      const parts = resp.data.data.trim().replace(/\t\r$/g, '').split('\t\r').filter(Boolean)
      return parts[0] || `学生${studentId}`
    }
  } catch (err) {
    console.error(`查询学生${studentId}姓名失败:`, err)
  }
  return `学生${studentId}`
}

const fetchData = async () => {
  loading.value = true
  try {
    const [infoResp, finalResp] = await Promise.all([
      cacheService.fetchWithCache(`homework_info:${assignmentId}`, () =>
        apiClient.post('/Homework/get_info_by_homework_id', {
          First: courseId,
          Second: assignmentId
        })
      ),
      apiClient.post('/Homework/get_final_submit', {
        First: teacherId,
        Second: jwt,
        Third: courseId,
        Fourth: assignmentId
      })
    ])

    // 处理作业标题
    if (infoResp.data.success && infoResp.data.data) {
      const d = infoResp.data.data.trim().replace(/\t\r$/g, '').split('\t\r').filter(Boolean)
      assignmentTitle.value = d[0] || '未知作业'
    }

    if (!finalResp.data.success || !finalResp.data.data) {
      studentSubmissions.value = []
      loading.value = false
      return
    }

    const pairs = finalResp.data.data.split('\t\r').filter(Boolean)
    const submissions = []

    // 提取所有 studentId 和需要查询详情的 submitId
    const studentNamePromises = []
    const detailPromises = []

    for (const pair of pairs) {
      const [studentId, submitId] = pair.split('\n')

      // 收集所有查姓名的 Promise
      studentNamePromises.push(
        fetchStudentName(studentId).then(name => ({ studentId, studentName: name }))
      )

      let subInfo = {
        studentId,
        studentName: '加载中...', // 临时占位
        submitId,
        createTime: null,
        score: null,
        aiFeedback: null,
        teacherFeedback: null,
        videoUrl: null
      }

      if (submitId === '-1' || submitId === '-2') {
        submissions.push(subInfo)
        continue
      }

      // 收集所有查提交详情的 Promise
      detailPromises.push(
        cacheService.fetchWithCache(`submit_detail:${submitId}`, () =>
          apiClient.post('/Homework/get_submit_info', {
            First: '1', Second: teacherId, Third: jwt, Fourth: submitId
          })
        ).then(detailResp => {
          if (detailResp.data.success && detailResp.data.data) {
            const raw = detailResp.data.data.trim().replace(/\t\r$/g, '')
            const parts = raw.split('\t\r')
            return {
              studentId, submitId,
              videoUrl: parts[0] || null,
              score: parts[1] || null,
              aiFeedback: parts[2] || null,
              teacherFeedback: parts[3] || null,
              createTime: parts[4] || null
            }
          }
          return { studentId, submitId }
        })
      )
      submissions.push(subInfo)
    }

    // 并行执行所有查姓名和查详情的请求
    const [nameResults, detailResults] = await Promise.all([
      Promise.all(studentNamePromises),
      Promise.all(detailPromises)
    ])

    const nameMap = Object.fromEntries(nameResults.map(i => [i.studentId, i.studentName]))
    const detailMap = Object.fromEntries(detailResults.map(i => [i.submitId, i]))

    // 合并数据
    studentSubmissions.value = submissions.map(sub => {
      const name = nameMap[sub.studentId] || sub.studentName
      if (sub.submitId === '-1' || sub.submitId === '-2') return { ...sub, studentName: name }
      const detail = detailMap[sub.submitId] || {}
      return { ...sub, studentName: name, ...detail }
    }).sort((a, b) => {
      if (!a.createTime) return 1
      if (!b.createTime) return -1
      return new Date(b.createTime) - new Date(a.createTime)
    })

  } catch (err) {
    console.error('加载成绩失败:', err)
    alert('加载失败，请刷新重试')
  } finally {
    loading.value = false
  }
}

const startEdit = (sub) => {
  editingStudentId.value = sub.studentId
  editingScore.value = sub.score || ''
  editingComment.value = sub.teacherFeedback || ''
}

const saveGrade = async (sub) => {
  if (!sub.submitId || sub.submitId === '-1' || sub.submitId === '-2') {
    alert('无法评分：学生未提交')
    return
  }

  try {
    const resp = await apiClient.post('/Homework/teacher_test', {
      First: teacherId, Second: jwt, Third: courseId, Fourth: assignmentId,
      Fifth: sub.submitId, Sixth: editingScore.value, Seventh: editingComment.value.trim()
    })

    if (resp.data[0] === 0 || resp.data.success) {
      // 缓存清理
      cacheService.invalidate(`submit_detail:${sub.submitId}`);

      alert('评分保存成功！')
      editingStudentId.value = null
      await fetchData()
    } else {
      alert('保存失败')
    }
  } catch (err) {
    console.error(err)
    alert('保存失败，请检查网络')
  }
}

const viewVideo = (studentId, studentName = '') => {
  if (!studentId) return

  // 构造 SSE 流地址
  const baseUrl = aiClient.defaults.baseURL
  currentVideoUrl.value = `${baseUrl}/get_processed_video?homework_id=${assignmentId}&student_id=${studentId}&download=false`

  currentVideoTitle.value = `正在查看：${studentName} 的 AI 分析`
  videoDialogVisible.value = true
}


const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const goBack = () => router.push('/teacher')


onMounted(fetchData)
</script>
