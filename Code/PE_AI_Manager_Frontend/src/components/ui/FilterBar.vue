<template>
  <div class="filter-bar">
    <div class="filter-bar__grid">
      <slot />
    </div>
    <p v-if="summary" class="filter-bar__summary">{{ summary }}</p>
  </div>
</template>

<script setup>
defineProps({
  summary: { type: String, default: '' }
})
</script>

<style scoped>
.filter-bar {
  background: var(--web-surface-card);
  border: 1px solid var(--web-line-200);
  border-radius: var(--web-radius-xl);
  box-shadow: var(--web-shadow-card);
  padding: 1rem;
}
.filter-bar__grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}
.filter-bar__summary {
  margin-top: 0.75rem;
  color: var(--web-ink-500);
  font-size: 0.85rem;
}
</style>
