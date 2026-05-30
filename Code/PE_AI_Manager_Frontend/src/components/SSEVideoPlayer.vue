<template>
  <div class="rounded-lg overflow-hidden border border-gray-300 w-full">
    <!-- 直链视频（如 Supabase 公共 URL）：原生播放器，支持拖动进度 -->
    <div
      v-if="isDirectVideo"
      class="relative aspect-video bg-black rounded-xl overflow-hidden shadow-lg"
    >
      <video
        :src="streamUrl"
        controls
        playsinline
        class="w-full h-full object-contain"
      ></video>
    </div>
    <!-- SSE 帧流（兼容老的 get_processed_video 流式端点） -->
    <template v-else>
      <div class="relative aspect-video bg-black rounded-xl overflow-hidden shadow-lg">
        <canvas
          ref="canvasRef"
          class="w-full h-full object-contain"
          style="display: none;"
        ></canvas>
        <div
          v-if="!isPlaying"
          class="absolute inset-0 flex items-center justify-center bg-gray-900"
        >
          <button
            @click="startPlayback"
            class="px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-all shadow-lg"
          >
            ▶
          </button>
        </div>
      </div>
      <div
        ref="infoDivRef"
        class="text-sm text-gray-600 bg-gray-100 rounded-lg p-3 mt-3"
      >
        点击播放按钮开始观看视频
      </div>
      <div v-if="isPlaying" class="flex gap-2 mt-3">
        <button
          @click="stopPlayback"
          class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all"
        >
          ⏹ 停止
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'

const props = defineProps({
  streamUrl: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['playback-started', 'playback-stopped', 'playback-completed', 'playback-error'])

// 直链视频：http(s) 开头且不是老的 SSE 帧流端点。命中则用原生 <video> 播放。
const isDirectVideo = computed(() => {
  const url = props.streamUrl || ''
  return /^https?:\/\//i.test(url) && !url.includes('get_processed_video')
})

const canvasRef = ref(null)
const infoDivRef = ref(null)
const isPlaying = ref(false)
const eventSource = ref(null)

const startPlayback = () => {
  const canvas = canvasRef.value
  const infoDiv = infoDivRef.value

  if (!canvas || !infoDiv) {
    alert('视频播放器初始化失败')
    return
  }

  const ctx = canvas.getContext('2d')

  isPlaying.value = true
  eventSource.value = null

  const streamUrl = props.streamUrl

  if (!streamUrl) {
    alert('视频URL不存在')
    stopPlayback()
    return
  }

  eventSource.value = new EventSource(streamUrl)

  eventSource.value.onopen = function() {
    infoDiv.innerHTML = '视频流连接成功，正在接收数据...'
    canvas.style.display = 'block'
    emit('playback-started')
  }

  eventSource.value.onmessage = function(event) {
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
          stopPlayback()
          emit('playback-completed')
          break

        case 'error': {
          const errorMessage = data.data && data.data.message ? data.data.message : '未知错误'
          infoDiv.innerHTML = `错误: ${errorMessage}`
          stopPlayback()
          alert(`视频流错误: ${errorMessage}`)
          emit('playback-error', errorMessage)
          break
        }
      }
    } catch (e) {
      console.error('解析SSE数据出错:', e)
      infoDiv.innerHTML = `解析数据出错: ${e.message}`
    }
  }

  eventSource.value.onerror = function(err) {
    console.error('SSE连接错误:', err)
    infoDiv.innerHTML = '连接错误，请重试'
    stopPlayback()
    emit('playback-error', '连接错误')
  }
}

const stopPlayback = () => {
  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }
  isPlaying.value = false

  const canvas = canvasRef.value
  const infoDiv = infoDivRef.value

  if (canvas) {
    canvas.style.display = 'none'
  }
  if (infoDiv) {
    infoDiv.innerHTML = '点击播放按钮开始观看视频'
  }
  emit('playback-stopped')
}

onBeforeUnmount(() => {
  stopPlayback()
})
</script>
