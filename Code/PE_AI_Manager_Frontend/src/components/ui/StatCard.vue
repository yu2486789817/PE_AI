<template>
  <div class="stat-card">
    <div class="stat-card__icon" :class="`tone-${tone}`">
      <slot name="icon" />
    </div>
    <div>
      <p class="stat-card__label">{{ label }}</p>
      <p class="stat-card__value">{{ value }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  tone: { type: String, default: 'primary' }
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: var(--web-surface-card);
  border: 1px solid var(--web-line-200);
  border-radius: var(--web-radius-lg);
  box-shadow: var(--web-shadow-card);
  padding: 1rem;
}
.stat-card__icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.75rem;
  display: grid;
  place-items: center;
}
.tone-primary { background: rgba(35, 109, 242, 0.12); color: var(--web-primary-600); }
.tone-success { background: rgba(19, 151, 105, 0.12); color: var(--web-success-600); }
.tone-warning { background: rgba(234, 136, 20, 0.12); color: var(--web-warning-600); }
.stat-card__label {
  margin: 0;
  color: var(--web-ink-500);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.stat-card__value {
  margin: 0.1rem 0 0;
  color: var(--web-ink-900);
  font-size: 1.5rem;
  font-weight: 700;
}
</style>
