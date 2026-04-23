<template>
  <div class="page-shell">
    <div class="page-container">
      <PageHeader title="学生管理" :subtitle="`课程 ID：${courseId}`">
        <template #actions>
          <button class="btn-outline" @click="goBack">返回课程</button>
        </template>
      </PageHeader>

      <SectionCard title="名单操作">
        <div class="flex flex-wrap items-center gap-2">
          <button class="btn-primary" :disabled="isArchived" @click="openImportDialog">导入学生</button>
          <button class="btn-outline" :disabled="students.length === 0" @click="exportStudentsCsv">导出 CSV</button>
          <button class="btn-outline" :disabled="students.length === 0" @click="copyAllStudentIds">复制全部学号</button>
        </div>
        <p v-if="isArchived" class="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-700">
          当前课程已归档，可查看和导出名单，但不能导入或移除学生。
        </p>
      </SectionCard>

      <SectionCard :title="`学生列表（${students.length}）`">
        <div v-if="loading" class="py-10 text-center text-web-ink-500">正在加载学生名单...</div>

        <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-red-700">
          {{ errorMessage }}
          <button class="btn-primary mt-3" @click="fetchStudents">重试</button>
        </div>

        <EmptyState
          v-else-if="students.length === 0"
          title="暂无学生"
          description="学生可通过课程邀请码加入课程。"
        />

        <div v-else class="space-y-3">
          <article
            v-for="student in students"
            :key="student.id"
            class="rounded-lg border border-web-line-200 bg-white p-4"
          >
            <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p class="font-semibold text-web-ink-900">{{ student.name || '未命名学生' }}（{{ student.id }}）</p>
                <p class="mt-1 text-sm text-web-ink-500">
                  性别：{{ student.gender || '-' }}
                  <span v-if="student.college"> | 学院：{{ student.college }}</span>
                  <span v-if="student.department"> | 系别：{{ student.department }}</span>
                  <span v-if="student.major"> | 专业：{{ student.major }}</span>
                </p>
              </div>
              <button class="btn-danger" :disabled="isArchived" @click="removeStudent(student.id)">移除</button>
            </div>
          </article>
        </div>
      </SectionCard>
    </div>

    <el-dialog v-model="showImportDialog" title="导入学生" width="640px">
      <p class="text-sm text-web-ink-500">支持换行、空格、逗号分隔学号，也可上传 CSV/TXT。</p>

      <div class="mt-3 flex gap-2">
        <button class="btn-outline" @click="triggerImportFile">选择文件</button>
        <input ref="importFileInput" type="file" accept=".csv,.txt" class="hidden" @change="handleImportFile" />
      </div>

      <textarea
        v-model="importText"
        rows="8"
        class="input-base mt-3"
        placeholder="示例：\n20240001\n20240002"
      />

      <template #footer>
        <button class="btn-outline" @click="closeImportDialog">取消</button>
        <button class="btn-primary" :disabled="importing" @click="confirmImportStudents">{{ importing ? '导入中...' : '确认导入' }}</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import apiClient from '../../services/axios.js'
import { cacheService } from '../../services/DataCacheService.js'
import PageHeader from '../../components/ui/PageHeader.vue'
import SectionCard from '../../components/ui/SectionCard.vue'
import EmptyState from '../../components/ui/EmptyState.vue'

const router = useRouter()
const route = useRoute()

const courseId = route.params.courseId

const students = ref([])
const courseStatus = ref('1')
const loading = ref(true)
const error = ref(false)
const errorMessage = ref('')

const showImportDialog = ref(false)
const importText = ref('')
const importing = ref(false)
const importFileInput = ref(null)

const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const teacherId = currentUser.id || ''
const jwt = currentUser.token || ''

const isArchived = computed(() => courseStatus.value === '2')

const fetchCourseStatus = async () => {
  const resp = await apiClient.post('/Course/get_info_by_course_id', {
    First: courseId,
    Second: jwt
  })

  if (!resp?.data?.success || !resp?.data?.data) return
  const parts = String(resp.data.data).trim().replace(/\t\r$/g, '').split(/\t\r/).filter(Boolean)
  courseStatus.value = String(parts[5] || '1')
}

const fetchStudents = async () => {
  loading.value = true
  error.value = false
  students.value = []

  try {
    await fetchCourseStatus()

    const idResp = await cacheService.fetchWithCache(`course_student_ids:${courseId}`, () =>
      apiClient.post('/Course_student/get_student_id_by_course', {
        First: teacherId,
        Second: jwt,
        Third: courseId
      })
    )

    if (!idResp.data.success) return

    const studentIdStr = idResp.data.data
    if (!studentIdStr || studentIdStr === 'NULL') return

    const studentIds = studentIdStr.split('\t\r').filter(Boolean)

    const studentPromises = studentIds.map(async (id) => {
      try {
        const infoResp = await cacheService.fetchWithCache(`user_info:${id}`, () =>
          apiClient.post('/User/get_student_info', {
            First: teacherId,
            Second: jwt,
            Third: '1',
            Fourth: id
          })
        )

        if (!infoResp.data.success) {
          return { id, name: null, gender: null, major: null, college: null, department: null }
        }

        const parts = String(infoResp.data.data || '').trim().replace(/\t\r$/g, '').split(/\t\r/).filter(Boolean)
        return {
          id,
          name: parts[0] || null,
          gender: parts[1] || null,
          major: parts[2] || null,
          college: parts[3] || null,
          department: parts[4] || null
        }
      } catch (err) {
        console.error(`failed to load student ${id}`, err)
        return { id, name: null, gender: null, major: null, college: null, department: null }
      }
    })

    students.value = await Promise.all(studentPromises)
  } catch (err) {
    console.error(err)
    error.value = true
    errorMessage.value = '无法加载学生名单，请检查权限或网络。'
  } finally {
    loading.value = false
  }
}

const removeStudent = async (studentId) => {
  if (isArchived.value) {
    alert('课程已归档，不能修改名单')
    return
  }
  if (!confirm(`确定移除学号 ${studentId} 吗？`)) return

  try {
    const resp = await apiClient.post('/Course_student/exit_course_by_teacher', {
      First: teacherId,
      Second: jwt,
      Third: courseId,
      Fourth: studentId
    })

    if (resp.data.success) {
      cacheService.invalidate(`course_student_ids:${courseId}`)
      cacheService.invalidate(`course_student_count:${courseId}`)
      students.value = students.value.filter((s) => s.id !== studentId)
      alert('学生已移除')
    } else {
      alert(`移除失败：${resp.data.message || '未知错误'}`)
    }
  } catch (err) {
    console.error(err)
    alert('操作失败，请稍后重试')
  }
}

const copyAllStudentIds = async () => {
  const text = students.value.map((s) => s.id).join('\n')
  try {
    await navigator.clipboard.writeText(text)
    alert('学号已复制到剪贴板')
  } catch {
    alert('复制失败，请手动复制')
  }
}

const exportStudentsCsv = () => {
  if (!students.value.length) return

  const header = ['学号', '姓名', '性别', '学院', '系别', '专业']
  const rows = students.value.map((s) => [s.id || '', s.name || '', s.gender || '', s.college || '', s.department || '', s.major || ''])
  const csvLines = [header, ...rows].map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))

  const blob = new Blob(['\uFEFF' + csvLines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `course_${courseId}_students.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const parseStudentIds = (raw) => {
  if (!raw) return []
  const tokens = raw
    .split(/[\s,;，；]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item) => /^[A-Za-z0-9_-]+$/.test(item))
  return [...new Set(tokens)]
}

const triggerImportFile = () => importFileInput.value?.click()

const handleImportFile = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = () => {
    importText.value = String(reader.result || '')
  }
  reader.readAsText(file, 'utf-8')
  event.target.value = ''
}

const closeImportDialog = () => {
  if (importing.value) return
  showImportDialog.value = false
}

const openImportDialog = () => {
  if (isArchived.value) {
    alert('课程已归档，不能导入学生')
    return
  }
  importText.value = ''
  showImportDialog.value = true
}

const confirmImportStudents = async () => {
  if (isArchived.value) {
    alert('课程已归档，不能导入学生')
    return
  }

  const ids = parseStudentIds(importText.value)
  if (!ids.length) {
    alert('未识别到有效学号')
    return
  }

  importing.value = true
  try {
    const resp = await apiClient.post('/Course_student/import_students_by_teacher', {
      First: teacherId,
      Second: jwt,
      Third: courseId,
      Fourth: ids.join(',')
    })

    if (!resp.data.success) {
      alert(`导入失败：${resp.data.message || '未知错误'}`)
      return
    }

    const summary = resp.data.data || {}
    alert(`导入完成：新增 ${summary.addedCount || 0}，已存在 ${summary.existingCount || 0}，未找到 ${summary.notFoundCount || 0}`)

    cacheService.invalidate(`course_student_ids:${courseId}`)
    cacheService.invalidate(`course_student_count:${courseId}`)
    showImportDialog.value = false
    await fetchStudents()
  } catch (err) {
    console.error(err)
    alert('导入失败，请稍后重试')
  } finally {
    importing.value = false
  }
}

const goBack = () => router.push(`/teacher/course/${courseId}`)

onMounted(() => {
  if (!courseId) {
    alert('无效课程 ID')
    router.push('/teacher')
    return
  }
  fetchStudents()
})
</script>
