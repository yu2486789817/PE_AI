<template>
  <!-- 模板部分完全不变 -->
  <div class="file-uploader-wrapper">
    <div class="file-uploader" :style="{ maxWidth: maxWidth }">
      <!-- 拖拽上传区域 -->
      <div
        class="upload-area"
        :class="{ 'drag-over': dragOver }"
        @drop.prevent="handleDrop"
        @dragover.prevent="dragOver = true"
        @dragenter.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @click="triggerFileInput"
      >
        <input
          type="file"
          ref="fileInput"
          accept="video/mp4,.mp4"
          style="display: none"
          @change="handleFileChange"
        />
        <div class="upload-hint">
          <div class="text-5xl text-gray-300 mb-4">🎥</div>
          <p>点击或将 MP4 视频文件拖拽到这里上传</p>
          <p class="tip">仅支持 MP4 格式，单个文件最大 {{ formatBytes(maxSize) }}</p>
        </div>
      </div>

      <!-- 上传进度 -->
      <div v-if="uploading" class="progress-container">
        <div class="info">
          <p>正在上传：{{ fileName }} ({{ formatBytes(totalSize) }})</p>
          <p>已上传：{{ formatBytes(uploadedSize) }} ({{ progress.toFixed(1) }}%)</p>
          <p>速度：{{ uploadSpeed }}/s</p>
          <p>预计剩余时间：{{ remainingTime }}</p>
        </div>
        <el-progress
          :percentage="progress"
          :stroke-width="12"
          :format="formatProgress"
        />
        <button @click="cancelUpload" class="cancel-btn">取消上传</button>
      </div>

      <!-- 上传成功提示 -->
      <div v-if="uploadResult && !uploading" class="result">
        <p>上传成功！</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { fileClient } from '@/services/fileClient';
import axios from 'axios';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['uploaded']);

const uploading = ref(false);
const dragOver = ref(false);
const progress = ref(0);
const fileName = ref('');
const totalSize = ref(0);
const uploadedSize = ref(0);
const uploadSpeed = ref('计算中...');
const remainingTime = ref('计算中...');
const uploadResult = ref(null);

const fileInput = ref(null);

// 支持传入的最大文件大小（单位：字节），默认 100MB
const props = defineProps({
  maxWidth: {
    type: String,
    default: '600px'
  },
  maxFileSize: {
    type: Number,           // 单位：MB，例如 500 表示 500MB
    default: 100
  }
});

// 计算实际的最大字节数
const maxSize = computed(() => props.maxFileSize * 1024 * 1024);

let cancelTokenSource = null;

// 用于平滑速度计算
let lastLoaded = 0;
let lastTime = null;
let smoothedSpeed = 0; // 字节/秒

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const triggerFileInput = () => {
  fileInput.value.click();
};

const validateFile = (file) => {
  if (!file) return false;

  if (file.type !== 'video/mp4' && !file.name.toLowerCase().endsWith('.mp4')) {
    ElMessage.warning('只允许上传 MP4 格式的视频文件！');
    return false;
  }

  if (file.size > maxSize.value) {
    ElMessage.warning(`文件大小不能超过 ${props.maxFileSize}MB！`);
    return false;
  }

  return true;
};

const handleFileChange = (e) => {
  const file = e.target.files[0];
  if (file && validateFile(file)) {
    uploadFile(file);
  }
  e.target.value = '';
};

const handleDrop = (e) => {
  dragOver.value = false;
  const file = e.dataTransfer.files[0];
  if (file && validateFile(file)) {
    uploadFile(file);
  }
};

// 更新速度和剩余时间（平滑处理）
const updateSpeedAndTime = (loaded, total) => {
  const now = Date.now();
  if (!lastTime) {
    lastTime = now;
    lastLoaded = loaded;
    return;
  }

  const timeDiff = (now - lastTime) / 1000; // 秒
  const loadedDiff = loaded - lastLoaded;
  const instantSpeed = loadedDiff / timeDiff;

  // 简单指数移动平均（平滑系数 0.3）
  const alpha = 0.3;
  smoothedSpeed = smoothedSpeed === 0 ? instantSpeed : alpha * instantSpeed + (1 - alpha) * smoothedSpeed;

  uploadSpeed.value = formatBytes(smoothedSpeed) + '/s';

  if (smoothedSpeed > 100) {
    const remainingBytes = total - loaded;
    const remainingSeconds = Math.round(remainingBytes / smoothedSpeed);
    if (remainingSeconds < 60) {
      remainingTime.value = `${remainingSeconds} 秒`;
    } else {
      const min = Math.floor(remainingSeconds / 60);
      const sec = remainingSeconds % 60;
      remainingTime.value = `${min} 分 ${sec} 秒`;
    }
  }

  lastLoaded = loaded;
  lastTime = now;
};

const uploadFile = async (file) => {
  fileName.value = file.name;
  totalSize.value = file.size;
  uploadedSize.value = 0;
  progress.value = 0;
  uploadSpeed.value = '计算中...';
  remainingTime.value = '计算中...';
  uploadResult.value = null;
  uploading.value = true;

  cancelTokenSource = axios.CancelToken.source();
  lastLoaded = 0;
  lastTime = null;
  smoothedSpeed = 0;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fileClient.post('/upload', formData, {
      cancelToken: cancelTokenSource.token,
      headers: { 'Content-Type': undefined },
      onUploadProgress: (progressEvent) => {
        const { loaded, total } = progressEvent;

        uploadedSize.value = loaded;
        progress.value = total ? (loaded / total) * 100 : 0;

        const now = Date.now();
        // 每约 800ms 更新一次显示，避免太频繁导致跳动
        if (!lastTime || now - lastTime >= 800 || loaded === total) {
          updateSpeedAndTime(loaded, total);
        }
      },
    });

    uploadResult.value = response.data;
    emit('uploaded', response.data);

    ElMessage.success('上传成功！');
  } catch (error) {
    if (axios.isCancel(error)) {
      ElMessage.info('上传已取消');
    } else {
      ElMessage.error('上传失败: ' + (error.response?.data?.error || error.message));
    }
  } finally {
    uploading.value = false;
    cancelTokenSource = null;
  }
};

const cancelUpload = () => {
  if (cancelTokenSource) cancelTokenSource.cancel();
};

const formatProgress = (percentage) => {
  return Number(percentage.toFixed(1)) + '%';
};
</script>

<style scoped>
.file-uploader-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px;
  width: 100%;
}
.file-uploader {
  width: 100%;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}
.upload-area {
  border: 3px dashed #dcdfe6;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #fafafa;
}
.upload-area.drag-over {
  border-color: #409eff;
  background: #f0f8ff;
}
.tip {
  font-size: 14px;
  color: #909399;
}
.progress-container {
  margin-top: 30px;
}
.info p {
  margin: 8px 0;
}
.cancel-btn {
  margin-top: 15px;
  padding: 8px 16px;
  background: #f56c6c;
  color: white;
  border: none;
  border-radius: 6px;
}
.result {
  margin-top: 20px;
  padding: 15px;
  background: #f0f9eb;
  border-radius: 8px;
}
</style>
