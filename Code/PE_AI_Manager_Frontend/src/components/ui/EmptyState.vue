<template>
  <div class="empty-state">
    <slot name="icon" />
    <h4>{{ title }}</h4>
    <p>{{ description }}</p>
    <div v-if="$slots.actions" class="empty-state__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' }
})
</script>

<style scoped>
.empty-state {
  text-align: center;
  padding: 2.5rem 1.5rem;
  border: 1px dashed var(--web-line-200);
  border-radius: var(--web-radius-lg);
  background: var(--web-surface-100);
}
.empty-state h4 {
  margin-top: 0.75rem;
  font-size: 1.1rem;
  color: var(--web-ink-800);
}
.empty-state p {
  margin-top: 0.4rem;
  color: var(--web-ink-500);
}
.empty-state__actions {
  margin-top: 1rem;
}
</style>
