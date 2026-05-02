<template>
  <div class="data-table">
    <slot />
  </div>
</template>

<style scoped>
.data-table {
  overflow-x: auto;
  border: 1px solid var(--web-line-200);
  border-radius: var(--web-radius-lg);
  background: var(--web-surface-card);
}
</style>
