<template>
  <section class="section-card">
    <div v-if="title || $slots.header" class="section-card__header">
      <slot name="header">
        <h3>{{ title }}</h3>
      </slot>
      <slot name="extra" />
    </div>
    <div class="section-card__body">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' }
})
</script>

<style scoped>
.section-card {
  background: var(--web-surface-card);
  border: 1px solid var(--web-line-200);
  border-radius: var(--web-radius-xl);
  box-shadow: var(--web-shadow-card);
}
.section-card__header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--web-line-100);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}
.section-card__header h3 {
  margin: 0;
  color: var(--web-ink-900);
  font-size: 1rem;
  font-weight: 700;
}
.section-card__body {
  padding: 1.25rem;
}
</style>
