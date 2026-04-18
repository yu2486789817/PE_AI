<template>
  <div class="min-h-screen bg-slate-50 font-display">
    <div class="max-w-6xl mx-auto p-6 space-y-10">

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-32">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-blue-500"></div>
        <p class="mt-6 text-xl text-gray-600">加载中...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="errorMsg" class="text-center py-32">
        <p class="text-2xl text-red-600 mb-6">{{ errorMsg }}</p>
        <button @click="loadData" class="px-8 py-3 rounded-xl bg-blue-500 text-white hover:bg-blue-600 transition-all shadow-lg">
          重试
        </button>
      </div>

      <!-- 正常内容 -->
      <div v-else class="space-y-12">  <!-- ⭐ 关键：大间距分隔区 -->

        <!-- 标题 + 操作栏 -->
        <section class="glass-card rounded-2xl p-8 kinetic-shadow">
          <div class="flex flex-col md:flex-row md:justify-between md:items-center gap-6">
            <div class="flex items-center">
              <VideoIcon class="w-10 h-10 text-blue-600 mr-4" />
              <div>
                <h2 class="text-3xl font-bold text-slate-900 tracking-tight mb-1">教学视频管理</h2>
                <p class="text-slate-500 text-sm font-medium">发布和管理体育教学视频</p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <select v-model="selectedCourseFilter"
                      @change="loadVideos"
                      class="px-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50/50 text-slate-700 text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all shadow-sm cursor-pointer">
                <option value="all">所有课程</option>
                <option v-for="course in courses" :key="course.id" :value="course.id">
                  {{ course.name }}
                </option>
              </select>
              <button @click="openAddModal"
                      class="flex items-center px-6 py-2.5 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 shadow-sm kinetic-button">
                <PlusIcon class="w-5 h-5 mr-2" />
                发布新视频
              </button>
            </div>
          </div>
        </section>

        <!-- 视频内容区 -->
        <section class="glass-card rounded-2xl p-8 kinetic-shadow">
          <h3 class="text-xl font-bold text-slate-900 mb-8 flex items-center">
            视频列表
            <span class="ml-3 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-sm font-medium border border-slate-200">
              {{ filteredVideos.length }}
            </span>
          </h3>

          <!-- 有视频：网格列表 -->
          <div v-if="filteredVideos.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div v-for="video in filteredVideos"
                 :key="video.id"
                 @click="openPlayDialog(video)"
                 class="group bg-white rounded-2xl border border-slate-200 overflow-hidden kinetic-shadow cursor-pointer flex flex-col h-full">
              <!-- 卡片内容保持不变 -->
              <div class="relative overflow-hidden">
                <img :src="video.cover" class="w-full h-48 object-cover transition-transform duration-500 group-hover:scale-105" alt="视频封面" />
                <div class="absolute inset-0 bg-slate-900/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 backdrop-blur-[2px]">
                  <div class="w-14 h-14 rounded-full bg-white/90 flex items-center justify-center shadow-lg transform scale-95 group-hover:scale-100 transition-transform duration-300">
                    <PlayIcon class="w-6 h-6 text-blue-600 ml-1 fill-current" />
                  </div>
                </div>
                <div class="absolute bottom-3 right-3 bg-slate-900/80 backdrop-blur-md text-white text-xs font-medium px-2.5 py-1 rounded-md shadow-sm border border-white/10">
                  {{ video.duration }}
                </div>
                <div class="absolute top-3 left-3 bg-blue-600/90 backdrop-blur-md text-white text-xs font-medium px-2.5 py-1 rounded-md shadow-sm border border-white/10">
                  {{ getCourseName(video.courseId) }}
                </div>
              </div>
              <div class="p-5 flex flex-col flex-grow">
                <h4 class="text-lg font-semibold text-slate-900 mb-2 line-clamp-1">{{ video.title }}</h4>
                <p class="text-sm text-slate-500 mb-5 line-clamp-2 flex-grow">{{ video.description }}</p>
                <div class="flex justify-between items-center pt-4 border-t border-slate-100">
                  <span class="text-xs font-medium text-slate-400">{{ formatDate(video.createdAt) }}</span>
                  <div class="flex gap-2">
                    <button @click.stop="openEditModal(video)" class="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors kinetic-button">
                      <PencilIcon class="w-4 h-4" />
                    </button>
                    <button @click.stop="deleteVideo(video.id)" class="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors kinetic-button">
                      <Trash2Icon class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 无视频：空状态 -->
          <div v-else class="text-center py-20 flex flex-col items-center justify-center border-2 border-dashed border-slate-200 rounded-2xl bg-slate-50/50">
            <FilmIcon class="w-16 h-16 text-slate-300 mb-4" stroke-width="1.5" />
            <h4 class="text-lg font-semibold text-slate-900 mb-2">暂无教学视频</h4>
            <p class="text-sm text-slate-500 mb-6 max-w-sm">
              当前筛选条件下还没有发布任何视频，请点击下方按钮添加。
            </p>
            <button @click="openAddModal"
                    class="flex items-center px-6 py-2.5 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 shadow-sm kinetic-button">
              <PlusIcon class="w-4 h-4 mr-2" />
              发布第一个视频
            </button>
          </div>
        </section>
      </div>


      <!-- 弹窗播放器 -->
      <VideoDialogPlayer
        v-model:visible="playDialogVisible"
        :video-url="currentPlayUrl"
        :title="currentPlayTitle"
      />

      <!-- 发布/编辑模态框 -->
      <Transition name="fade">
        <div v-if="showUploadModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-6 z-50">
          <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden border border-slate-200">
            <div class="flex justify-between items-center px-8 py-6 border-b border-slate-100 bg-slate-50/50">
              <h3 class="text-xl font-bold text-slate-900">
                {{ isEditMode ? '编辑教学视频' : '发布教学视频' }}
              </h3>
              <button @click="closeModal" class="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors kinetic-button">
                <XIcon class="w-5 h-5" />
              </button>
            </div>

          <div class="p-8 overflow-y-auto">
            <form @submit.prevent="submitVideo" class="space-y-6">
              <!-- 所属课程 -->
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">所属课程 <span class="text-red-500">*</span></label>
                <select v-model="videoForm.courseId"
                        class="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm outline-none text-slate-700"
                        required>
                  <option value="" disabled>请选择课程</option>
                  <option v-for="course in courses" :key="course.id" :value="course.id">
                    {{ course.name }}
                  </option>
                </select>
              </div>

              <!-- 编辑时预览当前视频（默认暂停） -->
              <div v-if="isEditMode && videoForm.url">
                <p class="text-xs font-medium text-amber-600 bg-amber-50 px-3 py-2 rounded-lg border border-amber-200">重新上传将替换当前视频</p>
              </div>

              <!-- 视频上传 -->
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">
                  {{ isEditMode ? '替换视频（可选）' : '上传视频' }} <span v-if="!isEditMode" class="text-red-500">*</span>
                </label>
                <FileUploader max-width="100%" :max-file-size="2048" @uploaded="onVideoUploaded" />
              </div>

              <!-- 视频标题 -->
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">视频标题 <span class="text-red-500">*</span></label>
                <input v-model="videoForm.title"
                       type="text"
                       class="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm outline-none text-slate-900 placeholder-slate-400"
                       placeholder="例如：50米折返跑技巧教学"
                       required />
              </div>

              <!-- 视频描述 -->
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">视频描述 <span class="text-red-500">*</span></label>
                <textarea v-model="videoForm.description"
                          rows="4"
                          class="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm outline-none text-slate-900 placeholder-slate-400 resize-none"
                          placeholder="详细描述视频内容和教学要点"
                          required></textarea>
              </div>

              <!-- 提交按钮 -->
              <div class="flex gap-3 justify-end pt-4 border-t border-slate-100">
                <button type="button"
                        @click="closeModal"
                        class="px-6 py-2.5 rounded-xl border border-slate-200 text-slate-700 font-medium hover:bg-slate-50 transition-colors shadow-sm kinetic-button">
                  取消
                </button>
                <button type="submit"
                        :disabled="!videoForm.url"
                        class="px-6 py-2.5 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed kinetic-button flex items-center">
                  <span v-if="isEditMode">保存修改</span>
                  <span v-else>发布视频</span>
                </button>
              </div>
            </form>
          </div>
        </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '../../services/axios.js'
import FileUploader from '@/components/FileUploader.vue'
import VideoDialogPlayer from '@/components/VideoDialogPlayer.vue'
import { Video as VideoIcon, Play as PlayIcon, Pencil as PencilIcon, Trash2 as Trash2Icon, X as XIcon, Plus as PlusIcon, Film as FilmIcon } from 'lucide-vue-next'

const courses = ref([])
const videos = ref([])
const selectedCourseFilter = ref('all')
const showUploadModal = ref(false)
const isEditMode = ref(false)
const editingVideoId = ref('')

const playDialogVisible = ref(false)
const currentPlayUrl = ref('')
const currentPlayTitle = ref('')

const loading = ref(true)
const errorMsg = ref('')

const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const teacherId = currentUser.id || ''
const jwt = currentUser.token || ''

const defaultCover = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAoMBgDTDzwAAAABJRU5ErkJggg=='
const videoForm = ref({
  courseId: '',
  title: '',
  description: '',
  url: ''
})

const filteredVideos = computed(() => {
  if (selectedCourseFilter.value === 'all') return videos.value
  return videos.value.filter(v => v.courseId === selectedCourseFilter.value)
})

// 路径修正：将完整URL转换为相对路径
const getPlayUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http://47.121.177.100:5002')) {
    let filename = ''
    if (url) {
      const lastSlashIndex = url.lastIndexOf('/')
      if (lastSlashIndex !== -1) {
        filename = url.substring(lastSlashIndex + 1)
      } else {
        filename = url
      }
    }
    return `/Teaching-video/files/${filename}`
  }
  return url
}

// 点击卡片弹窗播放
const openPlayDialog = (video) => {
  currentPlayUrl.value = getPlayUrl(video.url)
  currentPlayTitle.value = video.title
  playDialogVisible.value = true
}

// 动态生成封面和时长
const generateVideoMeta = (url, callback) => {
  if (!url) return callback(defaultCover, '未知')

  const video = document.createElement('video')
  video.src = getPlayUrl(url)
  video.crossOrigin = 'anonymous'

  let cover = defaultCover
  let duration = '未知'

  video.onloadedmetadata = () => {
    const mins = Math.floor(video.duration / 60).toString().padStart(2, '0')
    const secs = Math.floor(video.duration % 60).toString().padStart(2, '0')
    duration = `${mins}:${secs}`

    // 截取第1秒作为封面
    video.currentTime = Math.min(1, video.duration)
  }

  video.onseeked = () => {
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    cover = canvas.toDataURL('image/jpeg')
    callback(cover, duration)
  }

  video.onerror = () => callback(defaultCover, '未知')
}

// 上传成功回调
const onVideoUploaded = (result) => {
  if (result && result.url) {
    // 将完整URL转换为相对路径存储
    videoForm.value.url = getPlayUrl(result.url)
    ElMessage.success('视频上传成功！封面和时长加载中...')

    // 立即生成封面和时长（仅用于当前表单预览）
    generateVideoMeta(result.url, (newCover, newDuration) => {
      ElMessage.success('封面和时长已生成')
    })
  }
}

const openAddModal = () => {
  isEditMode.value = false
  editingVideoId.value = ''
  videoForm.value = {
    courseId: courses.value[0]?.id || '',
    title: '',
    description: '',
    url: ''
  }
  showUploadModal.value = true
}

const openEditModal = (video) => {
  isEditMode.value = true
  editingVideoId.value = video.id
  videoForm.value = {
    courseId: video.courseId,
    title: video.title,
    description: video.description,
    url: video.url
  }
  showUploadModal.value = true
}

const closeModal = () => {
  showUploadModal.value = false
  videoForm.value = { courseId: '', title: '', description: '', url: '' }
}

const submitVideo = async () => {
  if (!videoForm.value.courseId || !videoForm.value.title ||
      !videoForm.value.description || !videoForm.value.url) {
    alert('请填写所有必填项并上传视频')
    return
  }

  try {
    let resp
    if (isEditMode.value) {
      resp = await apiClient.post('/Class/edit_class', {
        first: teacherId,
        second: jwt,
        third: videoForm.value.courseId,
        fourth: editingVideoId.value,
        fifth: videoForm.value.title,
        sixth: videoForm.value.description,
        seventh: videoForm.value.url
      })
    } else {
      resp = await apiClient.post('/Class/new_class', {
        first: teacherId,
        second: jwt,
        third: videoForm.value.courseId,
        fourth: videoForm.value.title,
        fifth: videoForm.value.description,
        sixth: videoForm.value.url
      })
    }

    if (resp.data.success) {
      ElMessage.success(isEditMode.value ? '修改成功！' : '发布成功！')
      closeModal()
      await loadVideos()
    } else {
      alert(isEditMode.value ? '修改失败' : '发布失败')
    }
  } catch (err) {
    console.error(err)
    alert('网络错误，请重试')
  }
}

const deleteVideo = async (classId) => {
  if (!confirm('确定删除此教学视频吗？删除后不可恢复')) return

  const video = videos.value.find(v => v.id === classId)
  if (!video) return

  try {
    const resp = await apiClient.post('/Class/delete_class', {
      first: teacherId,
      second: jwt,
      third: video.courseId,
      fourth: classId
    })

    if (resp.data.success) {
      ElMessage.success('删除成功')
      await loadVideos()
    } else {
      alert('删除失败')
    }
  } catch (err) {
    console.error(err)
    alert('网络错误')
  }
}

const getCourseName = (courseId) => {
  const c = courses.value.find(item => item.id === courseId)
  return c ? c.name : '未知课程'
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

const loadData = async () => {
  loading.value = true
  errorMsg.value = ''

  try {
    const resp = await apiClient.post('/Course/get_course_id_by_teacher', {
      first: teacherId,
      second: jwt
    })

    if (!resp.data.success) {
      errorMsg.value = '获取课程失败'
      return
    }

    const courseIds = resp.data.data.trim().replace(/\t\r$/g, '').split('\t\r').filter(Boolean)

    const promises = courseIds.map(id =>
      apiClient.post('/Course/get_info_by_course_id', { first: id })
    )
    const resps = await Promise.all(promises)

    courses.value = resps
      .filter(r => r.data.success)
      .map((r, i) => ({
        id: courseIds[i],
        name: r.data.data.trim().replace(/\t\r$/g, '').split('\t\r').filter(Boolean)[1] || '未知课程'
      }))

    await loadVideos()
  } catch (err) {
    console.error(err)
    errorMsg.value = '加载失败，请检查网络或登录状态'
  } finally {
    loading.value = false
  }
}

const loadVideos = async () => {
  const tempVideos = []

  const targetIds = selectedCourseFilter.value === 'all'
    ? courses.value.map(c => c.id)
    : [selectedCourseFilter.value]

  for (const courseId of targetIds) {
    const resp = await apiClient.post('/Class/get_class_id_by_course', {
      first: '1',
      second: teacherId,
      third: jwt,
      fourth: courseId
    })

    if (!resp.data.success) continue

    const classIds = resp.data.data.trim().replace(/\t\r$/g, '').split('\t\r').filter(Boolean)

    const infoPromises = classIds.map(classId =>
      apiClient.post('/Class/get_info_by_class_id', {
        first: courseId,
        second: classId
      })
    )
    const infoResps = await Promise.all(infoPromises)

    infoResps.forEach((infoResp, idx) => {
      if (infoResp.data.success) {
        const d = infoResp.data.data.trim().replace(/\t\r$/g, '').split('\t\r').filter(Boolean)
        tempVideos.push({
          id: classIds[idx],
          courseId: courseId,
          title: d[0] || '无标题',
          description: d[1] || '暂无描述',
          url: getPlayUrl(d[2] || ''),
          cover: defaultCover,  // 占位
          duration: '加载中...',
          createdAt: d[3] || ''
        })
      }
    })
  }

  videos.value = tempVideos

  // 动态计算每个视频的封面和时长
  videos.value.forEach(video => {
    if (video.url) {
      video.cover = defaultCover
      generateVideoMeta(video.url, (cover, duration) => {
        video.cover = cover
        video.duration = duration
      })
    }
  })
}

onMounted(() => {
  if (!teacherId || !jwt) {
    errorMsg.value = '请先登录'
    loading.value = false
    return
  }
  loadData()
})
</script>
