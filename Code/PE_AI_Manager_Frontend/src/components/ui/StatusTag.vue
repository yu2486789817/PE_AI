<template>
  <span class="status-tag" :class="toneClass">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: [String, Number], default: '' }
})

const toneMap = {
  draft: { label: '未发布', class: 'tone-muted' },
  active: { label: '进行中', class: 'tone-primary' },
  archived: { label: '已归档', class: 'tone-warning' },
  expired: { label: '已截止', class: 'tone-muted' },
  error: { label: '异常', class: 'tone-danger' }
}

const normalized = computed(() => {
  const v = String(props.value ?? '').toLowerCase()
  if (['0', 'draft', 'inactive'].includes(v)) return 'draft'
  if (['1', 'active', 'ongoing'].includes(v)) return 'active'
  if (['2', 'archived'].includes(v)) return 'archived'
  if (['ended', 'expired', 'closed'].includes(v)) return 'expired'
  if (['error', 'failed'].includes(v)) return 'error'
  return 'draft'
})

const label = computed(() => toneMap[normalized.value].label)
const toneClass = computed(() => toneMap[normalized.value].class)
</script>

<style scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 700;
  border: 1px solid transparent;
}
.tone-primary { background: rgba(35,109,242,0.12); color: var(--web-primary-700); border-color: rgba(35,109,242,0.25); }
.tone-warning { background: rgba(234,136,20,0.14); color: var(--web-warning-700); border-color: rgba(234,136,20,0.25); }
.tone-danger { background: rgba(214,62,53,0.12); color: var(--web-danger-700); border-color: rgba(214,62,53,0.25); }
.tone-muted { background: var(--web-surface-200); color: var(--web-ink-600); border-color: var(--web-line-200); }
</style>
