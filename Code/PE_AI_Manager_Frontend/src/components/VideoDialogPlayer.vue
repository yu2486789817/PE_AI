<template>
  <Teleport to="body">
    <Transition name="video-fade">
      <div
        v-if="visible"
        class="video-overlay"
        @click.self="visible = false"
      >
        <div class="video-modal">
          <div class="video-modal__header">
            <span class="video-modal__title">{{ title }}</span>
            <button class="video-modal__close" type="button" aria-label="关闭" @click="visible = false">
              ✕
            </button>
          </div>

          <div class="video-modal__body">
            <video
              v-if="videoUrl"
              :src="videoUrl"
              controls
              autoplay
              muted
              playsinline
              preload="metadata"
              class="video-element"
            >
              您的浏览器不支持 video 标签。
            </video>
            <div v-else class="no-video">暂无视频</div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: Boolean,
  videoUrl: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: '视频播放'
  }
})

const emit = defineEmits(['update:visible'])

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})
</script>

<style scoped>
/* 遮罩层：teleport 到 body，z-index 远高于侧边栏 (z-50) */
.video-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.video-modal {
  width: 100%;
  max-width: 960px;
  max-height: 88vh;
  background: #0f172a;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
}

.video-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: #1e293b;
  color: #f8fafc;
}

.video-modal__title {
  font-size: 16px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-modal__close {
  flex-shrink: 0;
  margin-left: 16px;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #cbd5e1;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.video-modal__close:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.video-modal__body {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
}

.video-element {
  width: 100%;
  max-height: calc(88vh - 60px);
  object-fit: contain;
  background: #000;
  display: block;
}

.no-video {
  color: #888;
  font-size: 20px;
  padding: 80px 0;
}

/* 弹窗淡入淡出 */
.video-fade-enter-active,
.video-fade-leave-active {
  transition: opacity 0.2s ease;
}

.video-fade-enter-from,
.video-fade-leave-to {
  opacity: 0;
}

/* 移动端：占满更大区域但仍受控 */
@media (max-width: 768px) {
  .video-overlay {
    padding: 0;
  }

  .video-modal {
    max-width: 100%;
    width: 100%;
    height: 100%;
    max-height: 100%;
    border-radius: 0;
  }

  .video-element {
    max-height: calc(100vh - 60px);
  }
}
</style>
