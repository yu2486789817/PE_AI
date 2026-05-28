<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
    <div class="max-w-6xl mx-auto p-6 space-y-10">

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-32">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-blue-500"></div>
        <p class="mt-6 text-xl text-gray-600">加载教学视频中...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="errorMsg" class="text-center py-32">
        <p class="text-2xl text-red-600 mb-6">{{ errorMsg }}</p>
        <button @click="loadData" class="px-8 py-3 rounded-xl bg-blue-500 text-white hover:bg-blue-600 shadow-lg">
          重试
        </button>
      </div>

      <!-- 正常内容 -->
      <div v-else>
        <!-- 标题 + 课程筛选 -->
        <section class="flex flex-col md:flex-row md:justify-between md:items-center gap-6">
          <div>
            <h2 class="text-4xl font-bold text-gray-800 mb-2">🎥 教学视频</h2>

          </div>
          <select v-model="selectedCourse"
                  @change="loadVideos"
                  class="px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-blue-500 transition-all shadow-sm">
            <option value="all">所有课程</option>
            <option v-for="course in courses" :key="course.id" :value="course.id">
              {{ course.name }}
            </option>
          </select>
        </section>

        <!-- 视频列表 - 纵向排布 -->
        <section class="flex flex-col items-center gap-6">
          <div v-for="video in videos"
               :key="video.id"
               class="w-full max-w-2xl bg-white rounded-3xl shadow-xl overflow-hidden transition-all hover:shadow-2xl cursor-pointer"
               @click="playVideo(video)">
            <div class="relative">
              <div class="w-full h-64 bg-gray-200 flex items-center justify-center">
                <span class="text-6xl">🎬</span>  <!-- 占位封面 -->
              </div>
              <div class="absolute inset-0 bg-black/30 flex items-center justify-center">
                <div class="w-16 h-16 rounded-full bg-white/90 flex items-center justify-center text-3xl text-blue-600">
                  ▶️
                </div>
              </div>
              <div class="absolute top-3 left-3 bg-blue-600 text-white text-xs px-2 py-1 rounded-lg">
                {{ getCourseName(video.courseId) }}
              </div>
            </div>

            <div class="p-6">
              <h3 class="text-xl font-bold text-gray-800 mb-2">{{ video.title }}</h3>
              <p class="text-sm text-gray-600 mb-4 line-clamp-3">{{ video.description }}</p>
              <div class="text-sm text-gray-500">
                发布时间：{{ formatDate(video.create_time) }}
              </div>
            </div>
          </div>
        </section>

        <!-- 空状态 -->
        <section v-if="videos.length === 0" class="bg-white rounded-3xl shadow-xl p-16 text-center">
          <div class="text-6xl text-gray-300 mb-4">📹</div>
          <h3 class="text-xl font-bold text-gray-800 mb-2">暂无教学视频</h3>
          <p class="text-gray-500">教师尚未发布视频，请耐心等待～</p>
        </section>
      </div>

      <!-- 内联视频播放器 -->
      <div v-if="showVideoPlayer" class="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4">
        <div class="relative w-full max-w-5xl">
          <button @click="closeVideoPlayer" class="absolute -top-12 right-0 text-white text-3xl hover:text-gray-300 transition-colors z-10">
            ✕
          </button>
          <div class="bg-black rounded-2xl overflow-hidden shadow-2xl" style="height: 70vh;">
            <InlineVideoPlayer :src="playingVideoUrl" />
          </div>
          <div class="mt-4 text-white text-center">
            <h3 class="text-2xl font-bold mb-2">{{ playingVideoTitle }}</h3>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '../../services/axios.js'
import InlineVideoPlayer from '../../components/InlineVideoPlayer.vue'

const route = useRoute()

const courseIdFromRoute = route.params.courseId || ''

const courses = ref([])
const videos = ref([])
const selectedCourse = ref(courseIdFromRoute || 'all')
const showVideoPlayer = ref(false)
const playingVideoUrl = ref('')
const playingVideoTitle = ref('')
const loading = ref(true)
const errorMsg = ref('')

// 当前登录学生
const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const studentId = currentUser.id || ''
const jwt = currentUser.token || ''

// 主加载函数
const loadData = async () => {
  loading.value = true
  errorMsg.value = ''

  if (!studentId || !jwt) {
    errorMsg.value = '未登录或登录信息丢失'
    loading.value = false
    return
  }

  try {
    // 如果路由中有courseId参数，只加载该课程的视频
    if (courseIdFromRoute) {
      // 获取课程信息
      const courseResp = await apiClient.post('/Course/get_info_by_course_id', {
        first: courseIdFromRoute
      })

      if (courseResp.data.success && courseResp.data.data) {
        const courseDataArray = courseResp.data.data.split('\t\r')
        if (courseDataArray.length >= 2) {
          courses.value = [{
            id: courseIdFromRoute,
            name: courseDataArray[1] || '未知课程'
          }]
          selectedCourse.value = courseIdFromRoute
          await loadVideos()
        } else {
          errorMsg.value = '课程数据格式不正确'
        }
      } else {
        errorMsg.value = '获取课程信息失败'
      }
    } else {
      // 1. 获取学生加入的所有课程ID
      const courseIdResp = await apiClient.post('/Course_student/get_course_id_by_student', {
        first: studentId,
        second: jwt
      })

      if (courseIdResp.data[0] < 0) {
        errorMsg.value = '获取课程列表失败'
        console.error('get_course_id_by_student error:', courseIdResp.data[0])
        loading.value = false
        return
      }

      const courseIdStr = courseIdResp.data[0]
      const courseIds = courseIdStr ? courseIdStr.split('\t\r').filter(id => id) : []

      if (courseIds.length === 0) {
        errorMsg.value = '您尚未加入任何课程'
        loading.value = false
        return
      }

      // 2. 并行获取每个课程的详细信息（主要是 name）
      const coursePromises = courseIds.map(id =>
        apiClient.post('/Course/get_info_by_course_id', { first: id })
      )
      const courseResps = await Promise.all(coursePromises)

      courses.value = courseResps
        .filter(resp => resp.data[0] >= 0)  // 过滤错误
        .map((resp, index) => ({
          id: courseIds[index],
          name: resp.data[1]  // name 是第2个字段
        }))

      // 3. 默认选中第一个课程或'all'，加载视频
      selectedCourse.value = 'all'
      await loadVideos()
    }
  } catch (err) {
    errorMsg.value = '网络错误，请检查连接'
    console.error(err)
  } finally {
    loading.value = false
  }
}

// 加载视频（根据选中课程）
const loadVideos = async () => {
  videos.value = []

  const targetIds = selectedCourse.value === 'all'
    ? courses.value.map(c => c.id)
    : [selectedCourse.value]

  for (const courseId of targetIds) {
    try {
      // 获取该课程下所有教学任务ID
      const classIdResp = await apiClient.post('/Class/get_class_id_by_course', {
        capacity: '0',
        user_id: studentId,
        jwt,
        fourth: courseId
      })

      if (!classIdResp.data.data) {
        console.log(`课程 ${courseId} 暂无教学视频`)
        continue
      }

      const classIdStr = classIdResp.data.data
      const classIds = classIdStr.split('\t\r')

      // 获取每个视频详情
      for (const classId of classIds) {
        const infoResp = await apiClient.post('/Class/get_info_by_class_id', {
          first: courseId,
          second: classId,
          jwt
        })

        if (!infoResp.data.data) {
          continue
        }

        const d = infoResp.data.data.split('\t\r')
        videos.value.push({
          id: classId,
          courseId: courseId,
          title: d[0],         // title: 教学任务的标题
          description: d[1],   // description: 教学任务的描述
          content_url: d[2],   // content_url: 教学任务对应的视频地址
          create_time: d[3]   // create_time: 教学任务的创建时间
        })
      }
    } catch (err) {
      console.error('加载视频失败:', courseId, err)
    }
  }
}

onMounted(loadData)

// 切换课程时重新加载视频
watch(selectedCourse, loadVideos)

const getCourseName = (courseId) => {
  const c = courses.value.find(item => item.id === courseId)
  return c ? c.name : '未知课程'
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

const playVideo = (video) => {
  console.log('播放视频:', video)
  console.log('原始视频URL:', video.content_url)

  let videoUrl = video.content_url

  if (videoUrl && videoUrl.includes('http://47.121.177.100:5002')) {
    let filename = ''
    if (videoUrl) {
      const lastSlashIndex = videoUrl.lastIndexOf('/')
      if (lastSlashIndex !== -1) {
        filename = videoUrl.substring(lastSlashIndex + 1)
      } else {
        filename = videoUrl
      }
    }
    videoUrl = `/Teaching-video/files/${filename}`
    console.log('转换后的视频URL:', videoUrl)
  }

  playingVideoUrl.value = videoUrl
  playingVideoTitle.value = video.title
  showVideoPlayer.value = true

  console.log('播放器URL:', playingVideoUrl.value)
}

const closeVideoPlayer = () => {
  showVideoPlayer.value = false
  playingVideoUrl.value = ''
  playingVideoTitle.value = ''
}

</script>
