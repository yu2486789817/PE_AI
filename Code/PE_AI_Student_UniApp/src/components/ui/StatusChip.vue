<template>
  <text class="status-chip" :class="toneClass">{{ text }}</text>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ value: { type: String, default: '' } })

const normalized = computed(() => {
  const v = String(props.value || '').toLowerCase()
  if (['1', 'active', '进行中'].includes(v)) return 'active'
  if (['2', 'archived', '已归档'].includes(v)) return 'archived'
  if (['ended', 'expired', '已截止'].includes(v)) return 'expired'
  return 'draft'
})

const text = computed(() => {
  if (normalized.value === 'active') return '进行中'
  if (normalized.value === 'archived') return '已归档'
  if (normalized.value === 'expired') return '已截止'
  return '未发布'
})

const toneClass = computed(() => `tone-${normalized.value}`)
</script>

<style scoped>
.status-chip {
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  font-size: 21rpx;
  font-weight: 600;
}
.tone-active { background: rgba(35, 109, 242, 0.12); color: var(--color-primary-600); }
.tone-archived { background: rgba(234, 136, 20, 0.16); color: var(--color-warning-600); }
.tone-expired { background: rgba(103, 116, 143, 0.16); color: var(--color-ink-600); }
.tone-draft { background: var(--color-surface-200); color: var(--color-ink-600); }
</style>
