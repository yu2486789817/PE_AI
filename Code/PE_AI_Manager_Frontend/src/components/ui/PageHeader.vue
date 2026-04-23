<template>
  <header class="page-header">
    <div>
      <h1 class="page-header__title">{{ title }}</h1>
      <p v-if="subtitle" class="page-header__subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' }
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}
.page-header__title {
  font-size: 1.75rem;
  line-height: 2rem;
  font-weight: 700;
  color: var(--web-ink-900);
}
.page-header__subtitle {
  margin-top: 0.5rem;
  color: var(--web-ink-500);
  font-size: 0.95rem;
}
.page-header__actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}
</style>
