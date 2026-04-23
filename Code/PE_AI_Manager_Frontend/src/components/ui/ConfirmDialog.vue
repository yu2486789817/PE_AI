<template>
  <Teleport to="body">
    <div v-if="modelValue" class="confirm-overlay" @click="closeOnOverlay && $emit('update:modelValue', false)">
      <div class="confirm-dialog" @click.stop>
        <h3>{{ title }}</h3>
        <p>{{ message }}</p>
        <div class="confirm-dialog__actions">
          <button class="btn-outline" @click="$emit('update:modelValue', false)">{{ cancelText }}</button>
          <button class="btn-danger" @click="$emit('confirm')">{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '确认操作' },
  message: { type: String, default: '' },
  confirmText: { type: String, default: '确认' },
  cancelText: { type: String, default: '取消' },
  closeOnOverlay: { type: Boolean, default: true }
})

defineEmits(['update:modelValue', 'confirm'])
</script>

<style scoped>
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 20, 40, 0.45);
  display: grid;
  place-items: center;
  z-index: 2000;
}
.confirm-dialog {
  width: min(420px, calc(100vw - 2rem));
  border-radius: var(--web-radius-xl);
  background: var(--web-surface-card);
  border: 1px solid var(--web-line-200);
  box-shadow: var(--web-shadow-soft);
  padding: 1.2rem;
}
.confirm-dialog h3 {
  margin: 0;
  color: var(--web-ink-900);
}
.confirm-dialog p {
  margin: 0.75rem 0 1rem;
  color: var(--web-ink-600);
}
.confirm-dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
.btn-outline,
.btn-danger {
  border: none;
  border-radius: 0.625rem;
  padding: 0.45rem 0.85rem;
  cursor: pointer;
  font-weight: 600;
}
.btn-outline {
  background: var(--web-surface-200);
  color: var(--web-ink-700);
}
.btn-danger {
  background: var(--web-danger-600);
  color: white;
}
</style>
