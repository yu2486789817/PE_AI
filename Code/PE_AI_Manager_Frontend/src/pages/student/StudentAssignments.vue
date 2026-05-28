<template>
  <div class="min-h-screen bg-gray-100">
    <!-- 同济大学校徽 -->
    <div class="fixed inset-0 z-10 flex items-center justify-center opacity-5 pointer-events-none">
      <img src="@/assets/Login/2.jpg" alt="同济大学校徽" class="w-21 h-21 object-contain" />
    </div>
    <div class="max-w-4xl mx-auto p-6 space-y-10">

      <!-- 页面标题 -->
      <section class="flex justify-between items-center">
        <div class="flex items-center gap-4">
          <button @click="goBack" class="px-6 py-3 rounded-xl bg-gray-200 text-gray-800 hover:bg-gray-300 transition-all shadow flex items-center gap-2">
           返回
          </button>
          <div>
            <h2 class="text-4xl font-bold text-gray-800 mb-4">作业详情</h2>
            <p class="text-gray-600">查看作业要求和提交状态</p>
          </div>
        </div>
        <button @click="goToHistory" class="px-6 py-3 rounded-xl bg-purple-500 text-white hover:bg-purple-600 transition-all shadow-lg flex items-center gap-2">
          查看提交历史
        </button>
      </section>

      <!-- 加载状态 -->
      <div v-if="loading" class="flex justify-center items-center h-64">
        <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-500"></div>
      </div>

      <!-- 错误信息 -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-3xl p-6">
        <div class="flex items-center gap-3 mb-3">
          <h3 class="text-xl font-bold text-red-800">加载失败</h3>
        </div>
        <p class="text-red-700">{{ errorMessage }}</p>
        <button @click="fetchAssignmentDetails" class="mt-4 px-6 py-2 rounded-xl bg-red-500 text-white hover:bg-red-600 transition-all shadow">
          重试
        </button>
      </div>

      <!-- 作业信息卡片 -->
      <section v-else-if="assignment" class="bg-white rounded-3xl shadow-xl p-6">
        <h3 class="text-3xl font-bold text-gray-800 mb-4">{{ assignment.title }}</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div class="flex items-center gap-2 text-gray-600">
            <div>
              <div class="text-sm text-gray-400">创建时间</div>
              <div class="text-lg">{{ formatDate(assignment.create_time) }}</div>
            </div>
          </div>
          <div class="flex items-center gap-2 text-gray-600">
            <div>
              <div class="text-sm text-gray-400">截止时间</div>
              <div class="text-lg">{{ formatDate(assignment.deadline) }}</div>
            </div>
          </div>
          <div class="flex items-center gap-2 text-gray-600">
            <div>
              <div class="text-sm text-gray-400">科目</div>
              <div class="text-lg">{{ assignment.subject }}</div>
            </div>
          </div>
          <div class="flex items-center gap-2 text-gray-600">
            <div>
              <div class="text-sm text-gray-400">状态</div>
              <div>
                <span :class="[
                  'px-3 py-1 rounded-full text-sm font-medium',
                  assignment.status === '进行中' ? 'bg-blue-100 text-blue-800' :
                  assignment.status === '已完成' ? 'bg-green-100 text-green-800' :
                  'bg-gray-100 text-gray-800'
                ]">
                  {{ assignment.status }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div class="flex items-center gap-2 text-gray-600">
            <div>
              <div class="text-sm text-gray-400">课程ID</div>
              <div class="text-lg">{{ assignment.course_id }}</div>
            </div>
          </div>
          <div class="flex items-center gap-2 text-gray-600">
            <div>
              <div class="text-sm text-gray-400">分值</div>
              <div class="text-lg">{{ assignment.points }}分</div>
            </div>
          </div>
          <div class="flex items-center gap-2 text-gray-600">
            <div>
              <div class="text-sm text-gray-400">动作类型</div>
              <div>
                <span class="text-lg font-medium text-gray-700">
                  {{ aiType || '加载中...' }}
                </span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2 text-gray-600">
            <div>
              <div class="text-sm text-gray-400">要求动作个数</div>
              <div>
                <span class="text-lg font-medium text-gray-700">
                  {{ requiredCount !== null ? requiredCount : '加载中...' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 作业描述与视频上传上下布局 -->
        <div class="space-y-6">
          <!-- 作业描述和AI评分说明 -->
          <div class="w-full">
            <!-- 作业描述 -->
            <div class="mt-4 p-4 bg-blue-50 rounded-xl">
              <div class="assignment-description-wrapper">
                <h4 class="font-medium text-blue-800 mb-2">作业描述：</h4>
                <p class="text-blue-700 whitespace-pre-line max-h-32 overflow-y-auto">{{ assignment.description }}</p>
              </div>
            </div>

            <!-- AI评分说明 -->
            <div class="mt-4 p-4 bg-purple-50 rounded-xl">
              <div>
                <h4 class="font-medium text-purple-800 mb-1">AI评分说明：</h4>
                <p class="text-sm text-purple-700">
                  提交视频后，AI将自动分析你的动作规范度、完成度和技术要点，给出初步评分和详细反馈。
                  教师将根据AI评分和实际情况进行最终评分。
                </p>
              </div>
            </div>
          </div>

          <!-- 视频上传区域 -->
          <div class="w-full bg-white rounded-3xl shadow-xl p-8">
            <div class="flex flex-col items-center space-y-6">
              <!-- 上传区域 -->
              <div
                class="w-full max-w-2xl border-2 border-dashed rounded-2xl p-6 text-center transition-all hover:bg-gray-50"
                :disabled="assignment.status === '已完成'"
                :class="assignment.status === '已完成' ? 'opacity-50 cursor-not-allowed' : ''"
              >
                <div class="text-6xl text-gray-300 mb-4">🎥</div>
                <h3 class="text-xl font-bold text-gray-800 mb-2">上传作业视频</h3>
                <p class="text-gray-500 mb-4">仅支持 MP4 格式，单个文件最大 100MB</p>
                <button
                  @click="triggerFileInput"
                  class="px-6 py-2 rounded-xl bg-blue-500 text-white hover:bg-blue-600 transition-all shadow"
                >
                  选择视频文件
                </button>
                <input
                  ref="fileInput"
                  type="file"
                  accept="video/*"
                  class="hidden"
                  @change="handleFileChange"
                  :disabled="assignment.status === '已完成'"
                />
              </div>

              <!-- 已选择视频预览 -->
              <div v-if="selectedFile" class="w-full max-w-2xl">
                <div class="bg-gray-100 rounded-xl p-6 mb-4">
                  <div class="flex items-center justify-between mb-4">
                    <div>
                      <h4 class="font-medium text-gray-800">{{ selectedFile.name }}</h4>
                      <p class="text-sm text-gray-500">{{ formatFileSize(selectedFile.size) }}</p>
                    </div>
                  </div>
                  <button
                    @click="removeFile"
                    class="px-4 py-2 rounded-xl bg-red-500 text-white hover:bg-red-600 transition-all shadow"
                  >
                    移除
                  </button>
                </div>
                <!-- 视频预览 -->
                <div class="rounded-lg overflow-hidden border border-gray-300">
                  <video
                    ref="videoPreview"
                    controls
                    class="w-full h-auto max-h-60"
                  ></video>
                </div>
              </div>

              <!-- 上传进度显示 -->
              <div v-if="isUploading" class="w-full max-w-2xl">
                <div class="bg-gray-100 rounded-xl p-6">
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-gray-700 font-medium">上传进度</span>
                    <span class="text-blue-600 font-bold">{{ uploadProgress }}%</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2.5">
                    <div
                      class="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                      :style="{ width: uploadProgress + '%' }"
                    ></div>
                  </div>
                  <p class="text-sm text-gray-500 mt-2 text-center">视频正在上传，请不要关闭页面...</p>
                </div>
              </div>

              <!-- 处理后的视频预览 -->
              <div v-if="showProcessedVideo" class="w-full mt-8">
                <div class="bg-gray-100 rounded-xl p-6 mb-4">
                  <div class="flex items-center justify-between mb-4">
                    <div>
                      <h4 class="font-medium text-gray-800">AI处理后的视频</h4>
                      <p class="text-sm text-gray-500">AI已完成评分并生成处理后的视频</p>
                    </div>
                  </div>
                </div>
                <!-- AI处理后的视频预览 - 使用SSE流播放 -->
                <div class="rounded-lg overflow-hidden border border-gray-300 w-full">
                  <div class="relative aspect-video bg-black rounded-xl overflow-hidden shadow-lg">
                    <canvas
                      id="processed-video-canvas"
                      class="w-full h-full object-contain"
                      style="display: none;"
                    ></canvas>
                    <div
                      v-if="!isPlayingProcessedVideo"
                      class="absolute inset-0 flex items-center justify-center bg-gray-900"
                    >
                      <button
                        @click="startProcessedVideoPlayback"
                        class="px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-all shadow-lg"
                      >
                        ▶
                      </button>
                    </div>
                  </div>
                  <div
                    id="processed-video-info"
                    class="text-sm text-gray-600 bg-gray-100 rounded-lg p-3 mt-3"
                  >
                    点击播放按钮开始观看视频
                  </div>
                  <div v-if="isPlayingProcessedVideo" class="flex gap-2 mt-3">
                    <button
                      @click="stopProcessedVideoPlayback"
                      class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all"
                    >
                      ⏹ 停止
                    </button>
                  </div>
                </div>
                <div class="mt-4 flex justify-center">
                  <button
                    v-if="processedVideoUrl || processedVideoBlob"
                    @click="downloadProcessedVideo"
                    class="px-6 py-2 rounded-xl bg-green-500 text-white hover:bg-green-600 transition-all shadow"
                  >
                    下载处理后的视频
                  </button>
                </div>
              </div>

              <!-- 视频处理状态区域 -->
              <div v-if="isProcessing" class="w-full max-w-2xl space-y-4">
                <!-- 处理状态信息 -->
                <div
                  id="processingStats"
                  class="p-4 rounded-xl bg-gray-50 border border-gray-200"
                  v-html="processingStats"
                ></div>

                <!-- 处理中的视频帧预览 -->
                <div v-if="processingVideoFrame" class="flex justify-center">
                  <img
                    :src="processingVideoFrame"
                    alt="处理过程预览"
                    class="max-w-full max-h-100 rounded-lg shadow"
                  />
                </div>
              </div>

              <!-- 提交按钮 -->
              <button
                @click="submitAssignment"
                :disabled="!selectedFile || isUploading || assignment.status === '已完成'"
                class="px-10 py-4 rounded-2xl bg-blue-500 text-white font-bold text-lg hover:bg-blue-600 transition-all shadow-lg"
                :class="{ 'opacity-50 cursor-not-allowed': !selectedFile || isUploading || assignment.status === '已完成' }"
              >
                {{ isUploading ? '上传中...' : '提交作业' }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- 未找到作业 -->
      <section v-else class="bg-white rounded-3xl shadow-xl p-10 text-center">
        <h3 v-if="!assignment && !loading && !error" class="text-2xl font-bold text-gray-800 mb-2">未找到作业</h3>
        <p class="text-gray-500 mb-6">无法找到指定ID的作业信息</p>
        <button @click="goBack" class="px-6 py-2 rounded-xl bg-blue-500 text-white hover:bg-blue-600 transition-all shadow">
          返回上一页
        </button>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { StudentAssignmentService } from '../../services/studentAssignments'
import { apiClient } from '../../services/axios'

const router = useRouter()
const route = useRoute()
const assignmentService = new StudentAssignmentService()

// 作业详情相关
const assignment = ref(null)
const loading = ref(true)
const error = ref(false)
const errorMessage = ref('')
const finalScore = ref(null)
const aiType = ref(null)
const requiredCount = ref(null)

// SSE流播放相关
const isPlayingProcessedVideo = ref(false)
const processedVideoEventSource = ref(null)

// 文件上传相关（集成提交作业功能）
const fileInput = ref(null)
const videoPreview = ref(null)
const selectedFile = ref(null)
const uploadProgress = ref(0)
const isUploading = ref(false)
const processedVideoUrl = ref(null)
const downloadVideoUrl = ref(null)
const showProcessedVideo = ref(false)
const aiEvaluationSaved = ref(false)
const processingStats = ref('')
const isProcessing = ref(false)
const processingVideoFrame = ref('')
const processedVideoBlob = ref(null)

// 获取课程ID和作业ID
// 支持路由格式：/course/:courseId/assignments/:assignmentId
const courseId = route.params.courseId || 'PE101' // 默认为PE101课程
const assignmentId = route.params.assignmentId || route.params.id

// 获取作业详情（调用后端API）
const fetchAssignmentDetails = async () => {
  loading.value = true
  error.value = false
  errorMessage.value = ''

  try {
    const assignmentData = await assignmentService.fetchAssignmentDetails(courseId, assignmentId);
    assignment.value = assignmentData;
    console.log('作业详情加载成功:', assignment.value);

    // 获取AI类型
    const poseTypeInfo = await assignmentService.getPoseType(assignmentId);
    aiType.value = poseTypeInfo.poseType;
    requiredCount.value = poseTypeInfo.requiredCount;
    console.log('AI类型:', aiType.value);
    console.log('要求数量:', requiredCount.value);

    // 检查是否已有提交记录，更新作业状态
    await checkSubmissionStatus();
  } catch (err) {
    console.error('获取作业详情失败:', err);
    error.value = true;
    errorMessage.value = err.message || '获取作业详情失败，请稍后重试';
  } finally {
    loading.value = false;
  }
};

// 检查提交状态
const checkSubmissionStatus = async () => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const studentId = user.id;
    const token = localStorage.getItem('token') || user.token || '';

    if (!studentId || !token) {
      console.log('未找到用户信息，无法检查提交状态');
      return;
    }

    console.log('开始检查提交状态, studentId:', studentId, 'assignmentId:', assignmentId);

    // 调用 get_submit_id_by_student 获取提交ID列表
    const submitIdResponse = await apiClient.post('/Homework/get_submit_id_by_student', {
      first: '0',
      second: studentId,
      third: token,
      fourth: assignmentId,
      fifth: studentId
    });

    console.log('get_submit_id_by_student 响应:', submitIdResponse.data);

    if (submitIdResponse.data.success && submitIdResponse.data.data) {
      const submitData = submitIdResponse.data.data;
      console.log('提交数据:', submitData);

      // 检查是否有有效的提交ID（不是 NULL、-1、-2、空字符串）
      const invalidValues = ['NULL', '-1', '-2', ''];
      const hasValidSubmit = !invalidValues.includes(submitData.trim());

      if (hasValidSubmit) {
        // 有提交记录，更新状态为已完成
        if (assignment.value) {
          assignment.value.status = '已完成';
          console.log('该作业已有有效提交记录(submitId=' + submitData + ')，状态更新为已完成');
        }
      } else {
        console.log('提交数据无效(' + submitData + ')，保持当前状态:', assignment.value?.status);
      }
    } else {
      console.log('提交状态检查失败或无数据:', submitIdResponse.data);
    }
  } catch (err) {
    console.error('检查提交状态失败:', err);
    // 不影响主流程，静默处理
  }
};

// 获取最终得分
const fetchFinalScore = async () => {
  try {
    const score = await assignmentService.fetchFinalScore(courseId, assignmentId);
    finalScore.value = score;
  } catch (err) {
    console.error('获取最终得分失败:', err);
    finalScore.value = null;
  }
};

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 导航函数
const goBack = () => {
  router.push(`/student/course/${courseId}`)
}

const goToHistory = () => {
  router.push(`/student/course/${courseId}/assignments/${assignmentId}/submission-history`)
}

// 文件上传相关函数（集成提交作业功能）

// 触发文件选择
const triggerFileInput = () => {
  if (assignment.value && assignment.value.status !== '已完成') {
    fileInput.value.click()
  }
}

// 处理文件选择
const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file

    // 预览视频
    const reader = new FileReader()
    reader.onload = (e) => {
      if (videoPreview.value) {
        videoPreview.value.src = e.target.result
      }
    }
    reader.readAsDataURL(file)
  }
}

// 移除文件
const removeFile = () => {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  if (videoPreview.value) {
    videoPreview.value.src = ''
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 提交作业
const uploadHomeworkVideo = (formData, token) => {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', '/Homework/upload_submit')
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        uploadProgress.value = Math.round((event.loaded / event.total) * 100)
      }
    }
    xhr.onload = () => {
      try {
        const data = JSON.parse(xhr.responseText || '{}')
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(data)
        } else {
          reject(new Error(data.message || `上传失败(${xhr.status})`))
        }
      } catch {
        reject(new Error('提交响应解析失败'))
      }
    }
    xhr.onerror = () => reject(new Error('上传失败，请检查网络'))
    xhr.send(formData)
  })
}

const submitAssignment = async () => {
  if (!selectedFile.value) return

  try {
    aiEvaluationSaved.value = false
    uploadProgress.value = 0
    isUploading.value = true
    isProcessing.value = false
    processingStats.value = '正在上传视频，AI分析将在后台进行...'
    processingVideoFrame.value = ''
    showProcessedVideo.value = false

    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const studentId = user.id || 'student1'
    const token = localStorage.getItem('token') || user.token || ''

    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('student_id', studentId)
    formData.append('course_id', courseId)
    formData.append('homework_id', assignmentId)
    formData.append('pose_type', aiType.value || 'pushup')

    const response = await uploadHomeworkVideo(formData, token)
    if (!response?.success) {
      throw new Error(response?.message || '作业提交失败')
    }

    if (assignment.value) {
      assignment.value.status = '已提交'
    }

    removeFile()
    await fetchFinalScore()

    ElMessageBox.alert('作业提交成功，AI分析将在后台进行。', '提示', {
      confirmButtonText: '确定',
      type: 'success'
    })
  } catch (error) {
    console.error('作业提交失败:', error)
    alert(`作业提交失败: ${error.message}`)
  } finally {
    isUploading.value = false
    isProcessing.value = false
  }
}

// SSE流播放处理后的视频
const startProcessedVideoPlayback = () => {
  const canvasId = 'processed-video-canvas'
  const infoId = 'processed-video-info'

  const canvas = document.getElementById(canvasId)
  const infoDiv = document.getElementById(infoId)

  if (!canvas || !infoDiv) {
    alert('视频播放器初始化失败')
    return
  }

  const ctx = canvas.getContext('2d')

  isPlayingProcessedVideo.value = true
  processedVideoEventSource.value = null

  const streamUrl = processedVideoUrl.value

  if (!streamUrl) {
    alert('视频URL不存在')
    stopProcessedVideoPlayback()
    return
  }

  processedVideoEventSource.value = new EventSource(streamUrl)

  processedVideoEventSource.value.onopen = function() {
    infoDiv.innerHTML = '视频流连接成功，正在接收数据...'
    canvas.style.display = 'block'
  }

  processedVideoEventSource.value.onmessage = function(event) {
    try {
      const data = JSON.parse(event.data)

      switch (data.event) {
        case 'video_info': {
          const width = data.data.width !== undefined ? data.data.width : 'N/A'
          const height = data.data.height !== undefined ? data.data.height : 'N/A'
          const fps = data.data.fps !== undefined ? data.data.fps : 30
          infoDiv.innerHTML = `视频信息: ${width}x${height} @ ${fps}fps`
          break
        }

        case 'frame': {
          const img = new Image()
          img.onload = function() {
            canvas.width = img.width
            canvas.height = img.height
            ctx.drawImage(img, 0, 0)
            const frameIndex = data.data.frame_index !== undefined ? data.data.frame_index : 'N/A'
            const timestamp = data.data.timestamp !== undefined ? data.data.timestamp.toFixed(2) : 'N/A'
            infoDiv.innerHTML = `正在播放: 第 ${frameIndex} 帧 (${timestamp}秒)`
          }
          if (data.data && data.data.image) {
            img.src = `data:image/jpeg;base64,${data.data.image}`
          } else {
            console.warn('接收到的帧数据缺少image字段:', data)
          }
          break
        }

        case 'complete':
          infoDiv.innerHTML = '视频播放完成'
          stopProcessedVideoPlayback()
          break

        case 'error': {
          const errorMessage = data.data && data.data.message ? data.data.message : '未知错误'
          infoDiv.innerHTML = `错误: ${errorMessage}`
          stopProcessedVideoPlayback()
          alert(`视频流错误: ${errorMessage}`)
          break
        }
      }
    } catch (e) {
      console.error('解析SSE数据出错:', e)
      infoDiv.innerHTML = `解析数据出错: ${e.message}`
    }
  }

  processedVideoEventSource.value.onerror = function(err) {
    console.error('SSE连接错误:', err)
    infoDiv.innerHTML = '连接错误，请重试'
    stopProcessedVideoPlayback()
  }
}

const stopProcessedVideoPlayback = () => {
  if (processedVideoEventSource.value) {
    processedVideoEventSource.value.close()
    processedVideoEventSource.value = null
  }
  isPlayingProcessedVideo.value = false

  const canvasId = 'processed-video-canvas'
  const infoId = 'processed-video-info'
  const canvas = document.getElementById(canvasId)
  const infoDiv = document.getElementById(infoId)

  if (canvas) {
    canvas.style.display = 'none'
  }
  if (infoDiv) {
    infoDiv.innerHTML = '点击播放按钮开始观看视频'
  }
}

// 下载处理后的视频
const downloadProcessedVideo = async () => {
  try {
    await assignmentService.downloadProcessedVideo(
      processedVideoUrl.value,
      downloadVideoUrl.value,
      processedVideoBlob.value,
      assignmentId
    );
  } catch (error) {
    console.error('视频下载失败:', error);
    alert(error.message || '无法下载视频文件');
  }
}

// 组件挂载时获取作业详情
onMounted(() => {
  fetchAssignmentDetails()
  fetchFinalScore()
})

// 组件卸载时清理SSE连接
onBeforeUnmount(() => {
  stopProcessedVideoPlayback()
})
</script>
